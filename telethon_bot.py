import asyncio
import json
import re
import logging
from pathlib import Path
from socks import GeneralProxyError
from random import shuffle

from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, RPCError, FloodWaitError

import config

logging.basicConfig(level=logging.INFO)


async def parse_json(path: str):
    """
    Parses a JSON file and returns a dictionary of configuration.
    """
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    return {
        "api_id": cfg["app_id"],
        "api_hash": cfg["app_hash"],
        "phone": str(cfg["phone"]),
        "twoFA": cfg.get("twoFA", None),
        "sdk": cfg.get("sdk", None),
        "device": cfg.get("device", None),
        "app_version": cfg.get("app_version", None),
        "lang_pack": cfg.get("lang_pack", None),
        "system_lang_pack": cfg.get("system_lang_pack", None),
    }


def get_proxies():
    """
    Reads proxies from a file and returns a list of tuples.
    """
    proxies = []
    with open("proxies.txt", encoding="utf-8") as f:
        for line in f:
            host, port, username, password = line.strip().split(":")
            proxies.append(
                (
                    2,
                    host,
                    int(port),
                    True,
                    username,
                    password,
                )
            )
    return proxies


async def wait_code(
    old_client: TelegramClient,
    new_client: TelegramClient,
    phone: str,
    timeout: int = 120,
) -> tuple[str, str]:
    """
    Waits for the code to be sent to the phone.
    """
    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    async def handler(ev):
        m = re.search(r"\b\d{5,6}\b", ev.raw_text)
        if m and not fut.done():
            fut.set_result(m.group())

    old_client.add_event_handler(handler, events.NewMessage(from_users=777000))

    try:
        result = await new_client.send_code_request(f"+{phone}")
        code_hash = result.phone_code_hash

        code = await asyncio.wait_for(fut, timeout)
        return code, code_hash
    finally:
        old_client.remove_event_handler(handler)


async def new_session(
    json_path: str,
    old_client: TelegramClient,
    proxy: tuple[int, str, int, str, str],
) -> TelegramClient:
    """
    Creates a new session using the old session.
    """
    cfg = await parse_json(json_path)
    session_name = Path(json_path).stem + "_new"

    new_client = TelegramClient(
        session_name,
        cfg["api_id"],
        cfg["api_hash"],
        proxy=proxy,
        device_model=cfg["device"],
        system_version=cfg["sdk"],
        app_version=cfg["app_version"],
        lang_code=cfg["lang_pack"],
        system_lang_code=cfg["system_lang_pack"],
    )
    await new_client.connect()

    if not await new_client.is_user_authorized():
        phone = cfg["phone"]
        code, code_hash = await wait_code(old_client, new_client, phone)

        try:
            await new_client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=code_hash,
            )

        except SessionPasswordNeededError:
            password = cfg.get("twoFA")
            if not password:
                raise ValueError("There is no twoFA password in the JSON")

            await new_client.sign_in(password=password)

    return new_client


async def check_spam(client: TelegramClient, timeout: int = 10) -> bool:
    """
    Returns True if the account has no restrictions (according to @SpamBot).
    """
    try:
        async with client.conversation("SpamBot", timeout=timeout) as conv:
            await conv.send_message("/start")
            resp = await conv.get_response()
            text = resp.raw_text.lower()

        return any(p in text for p in config.NO_SPAM_PHRASES)

    except errors.FloodWaitError as e:
        logging.error(f"Flood-wait on {e.seconds} seconds — check will be repeated later")
        return False
    except Exception as e:
        logging.error(f"Error while checking account: {e}")
        return False


async def check_account(session_path: str, json_path: str) -> bool:
    """
    Checks the account for spam.
    """
    cfg = await parse_json(json_path)
    proxies = get_proxies()
    shuffle(proxies)
    session_name = session_path.replace(".session", "")

    last_exception = None

    for proxy_data in proxies:
        proxy_type, host, port, rdns, user, pwd = proxy_data
        proxy = (proxy_type, host, port, rdns, user, pwd)

        try:
            logging.info(f"Trying proxy: {proxy}")

            old_client = TelegramClient(
                session_name, cfg["api_id"], cfg["api_hash"], proxy=proxy
            )

            await old_client.connect()

            if not await old_client.is_user_authorized():
                logging.error(
                    f"❌ Old session not authorized, needs login. Skipping {session_path}"
                )
                await old_client.disconnect()
                return False

            me = await old_client.get_me()
            logging.info(f"Old session connected: {me.id}, {me.first_name}")

            new_client = await new_session(json_path, old_client, proxy=proxy)
            new_me = await new_client.get_me()

            if new_me.is_self:
                result = await check_spam(new_client)
                await new_client.disconnect()
                await old_client.disconnect()
                return result
            else:
                logging.error(f"❌ New session not working: {session_path.split('/')[-1]}")
                await new_client.disconnect()
                await old_client.disconnect()
                return False

        except (GeneralProxyError, ConnectionError, RPCError, FloodWaitError) as e:
            logging.error(f"❌ Connection failed with proxy {proxy}: {e}")
            last_exception = e
            continue

        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")
            last_exception = e
            break

    logging.error(f"❌ All proxies failed for {session_path.split('/')[-1]}")
    if last_exception:
        logging.error(f"Last error: {last_exception}")
    return False
