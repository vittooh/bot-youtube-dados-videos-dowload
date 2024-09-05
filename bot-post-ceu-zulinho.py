import os
import re
from typing import List, Dict


from atproto import Client
import dotenv

dotenv.load_dotenv()

usuario = os.getenv("USUARIO_CEU_ZULINHO")
pwd = os.getenv("PWD_CEU_ZULINHO")
client = Client(base_url='https://bsky.social')
tokens = client.login(
    login=usuario,
    password=pwd
)
post = "🪖🤖  Eu sou o marretinha digital 🤖🪖 Post Mortem: Uma reunião bem importante!! Vídeo no canal, Deixe seu like e se inscreva no canal O pedreiro digital ama vcs, no entanto eu sou o bot dele Vídeo Novo Aqui https://www.youtube.com/watch?v=r09oSOFg1Vo".lstrip().rstrip()


def parse_urls(text: str) -> List[Dict]:
    spans = []
    url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
    text_bytes = text.encode("UTF-8")
    for m in re.finditer(url_regex, text_bytes):
        spans.append({
            "start": m.start(1),
            "end": m.end(1),
            "url": m.group(1).decode("UTF-8"),
        })
    return spans


def parse_facets(text: str):
    facets = []
    for u in parse_urls(text):
        facets.append({
            "index": {
                "byteStart": u["start"],
                "byteEnd": u["end"],
            },
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": u["url"],
                }
            ],
        })
    return facets


post = client.send_post(
    text=post,
    facets=parse_facets(post)
)
