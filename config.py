from pathlib import Path

# Directories
UPLOAD_DIR = Path("files/uploads")
EXTRACT_DIR = Path("files/extracted")
NEW_SESSION_DIR = Path("files/new_sessions")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
NEW_SESSION_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# no spam phrases
NO_SPAM_PHRASES = (
    "good news, no limits are currently applied to your account. you’re free as a bird!",
)
