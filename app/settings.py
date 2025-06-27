import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

class Settings:
    AZURE_TENANT_ID        = os.getenv("AZURE_TENANT_ID")
    AZURE_CLIENT_ID        = os.getenv("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET    = os.getenv("AZURE_CLIENT_SECRET")
    OUTLOOK_USER_ID        = os.getenv("OUTLOOK_USER_ID", "me")
    OUTLOOK_FOLDER_NAME    = os.getenv("OUTLOOK_FOLDER_NAME", "Inbox")

    AWS_ACCESS_KEY_ID      = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY  = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION             = os.getenv("AWS_REGION", "us-east-2")
    S3_BUCKET              = os.getenv("S3_BUCKET")

    OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY")

    SQLITE_DB_PATH         = os.getenv("SQLITE_DB_PATH", "./data/intake.db")

settings = Settings()
