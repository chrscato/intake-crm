import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

class Settings:
    # Support both naming conventions
    GRAPH_TENANT_ID        = os.getenv("GRAPH_TENANT_ID") or os.getenv("AZURE_TENANT_ID")
    GRAPH_CLIENT_ID        = os.getenv("GRAPH_CLIENT_ID") or os.getenv("AZURE_CLIENT_ID")
    GRAPH_CLIENT_SECRET    = os.getenv("GRAPH_CLIENT_SECRET") or os.getenv("AZURE_CLIENT_SECRET")
    SHARED_MAILBOX         = os.getenv("SHARED_MAILBOX") or os.getenv("OUTLOOK_USER_ID")
    MAILBOX_FOLDER         = os.getenv("MAILBOX_FOLDER") or os.getenv("OUTLOOK_FOLDER_NAME", "Inbox")

    AWS_ACCESS_KEY_ID      = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY  = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION             = os.getenv("AWS_REGION", "us-east-2")
    S3_BUCKET              = os.getenv("S3_BUCKET")

    OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY")

    SQLITE_DB_PATH         = os.getenv("SQLITE_DB_PATH", "./data/intake.db")

settings = Settings()
