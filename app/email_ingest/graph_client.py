from msal import ConfidentialClientApplication
import requests
from app.settings import settings

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]

def _token():
    cca = ConfidentialClientApplication(
        settings.GRAPH_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}",
        client_credential=settings.GRAPH_CLIENT_SECRET,
    )
    return cca.acquire_token_for_client(scopes=GRAPH_SCOPE)["access_token"]

def graph_get(url: str):
    headers = {"Authorization": f"Bearer {_token()}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()
