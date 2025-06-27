"""Iterates new messages in Outlook folder, uploads raw blobs to S3, inserts stub row in SQLite."""
from datetime import datetime
from app.storage import s3, db
from .graph_client import graph_get
from app.settings import settings

def run():
    print("pulling messages…")
    # example only – implement delta query for production
    url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_USER_ID}/mailFolders/{settings.OUTLOOK_FOLDER_NAME}/messages?$top=10"
    data = graph_get(url)
    for msg in data.get("value", []):
        db.add_stub(msg)       # implement in storage.db
        s3.upload_raw(msg)     # implement in storage.s3
