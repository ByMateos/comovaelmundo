"""Se ejecuta UNA vez en tu ordenador para autorizar el canal (abre el navegador, entras tú).
pip install google-auth-oauthlib ; python obtener_token.py client_secret.json"""
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"])
c = flow.run_local_server(port=0, prompt="consent", access_type="offline")
print("\nGuarda estos 3 valores como secretos del repositorio:\nYT_CLIENT_ID =", c.client_id, "\nYT_CLIENT_SECRET =", c.client_secret, "\nYT_REFRESH_TOKEN =", c.refresh_token)
