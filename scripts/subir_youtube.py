"""Sube a YouTube cada carpeta de cola/ con meta.json y sin resultado.json.
meta.json: {"video": "video.mp4", "miniatura": "mini.jpg", "titulo": "...", "descripcion": "...",
            "tags": [...], "categoria": "25", "privacidad": "private"}
Deja resultado.json con el id del vídeo."""
import json, os, glob
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
                    client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
                    scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"])
yt = build("youtube", "v3", credentials=creds)
for meta in sorted(glob.glob("cola/*/meta.json")):
    d = os.path.dirname(meta)
    if os.path.exists(os.path.join(d, "resultado.json")):
        continue
    m = json.load(open(meta))
    body = {"snippet": {"title": m["titulo"][:100], "description": m["descripcion"], "tags": m.get("tags", []),
                        "categoryId": m.get("categoria", "25"), "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": {"privacyStatus": m.get("privacidad", "private"), "selfDeclaredMadeForKids": False}}
    if m.get("publicar_en"):
        body["status"].update(privacyStatus="private", publishAt=m["publicar_en"])
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(os.path.join(d, m["video"]), chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    if m.get("miniatura"):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(d, m["miniatura"]))).execute()
        except Exception as e:
            print("miniatura no aplicada:", e)
    json.dump({"id": vid, "url": f"https://youtu.be/{vid}", "estado": resp["status"]}, open(os.path.join(d, "resultado.json"), "w"), ensure_ascii=False, indent=1)
    print("subido", d, vid)
