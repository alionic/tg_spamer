import asyncio
import logging
import os
import shutil
from pathlib import Path

import rarfile
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

import config
from telethon_bot import check_account

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


def get_extract_path(user_id: int) -> Path:
    extract_path = config.EXTRACT_DIR / str(user_id)
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    return extract_path

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Send me .rar archive with accounts.")

@dp.message()
async def handle_document(message: Message):
    if not message.document:
        await message.answer("Please send .rar archive with accounts.")
        return

    if not message.document.file_name.lower().endswith(".rar"):
        await message.answer("Please send .rar archive.")
        return

    if message.document.file_size > config.MAX_FILE_SIZE:
        await message.answer("❌ File is too large. Maximum size: 100MB.")
        return

    try:
        unique_filename = f"{message.from_user.id}_{message.document.file_name}"
        downloaded_file = config.UPLOAD_DIR / unique_filename

        extract_path = get_extract_path(message.from_user.id)

        await message.answer("Downloading archive...")
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, downloaded_file)

        if not downloaded_file.exists() or downloaded_file.stat().st_size == 0:
            raise Exception("File was not downloaded correctly.")

        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(exist_ok=True)

        await message.answer("Unpacking archive...")
        with rarfile.RarFile(downloaded_file) as rf:
            rf.extractall(path=extract_path)

        accounts = []
        for root, _, files in os.walk(extract_path):
            sessions = {
                os.path.splitext(f)[0]: os.path.join(root, f)
                for f in files
                if f.endswith(".session")
            }
            jsons = {
                os.path.splitext(f)[0]: os.path.join(root, f)
                for f in files
                if f.endswith(".json")
            }

            for name in sessions.keys() & jsons.keys():
                accounts.append((str(Path(sessions[name])), str(Path(jsons[name]))))

        if not accounts:
            await message.answer("❌ No accounts found in the archive.")
            return

        await message.answer(f"Found {len(accounts)} accounts. Starting check...")
        bad_accs = []
        good_accs = []
        for session_path, json_path in accounts:
            if await check_account(session_path, json_path):
                good_accs.append(session_path)
            else:
                bad_accs.append(session_path)
        bad_accs = [session_path.split("/")[-1].split(".")[0] for session_path in bad_accs]
        good_accs = [session_path.split("/")[-1].split(".")[0] for session_path in good_accs]
        await message.answer(f"✅ Good: {len(good_accs)}\n❌ Bad: {len(bad_accs)}")
        await message.answer(f"✅ Good: {good_accs}\n\n❌ Bad: {bad_accs}")

    except Exception as e:
        error_message = str(e)
        logging.error(f"Error: {error_message}")
        await message.answer(f"❌ Error while processing archive:\n{error_message}")

    finally:
        if downloaded_file.exists():
            try:
                downloaded_file.unlink()
            except Exception as e:
                logging.error(f"Error while deleting file {downloaded_file}: {e}")


async def main():
    logging.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
