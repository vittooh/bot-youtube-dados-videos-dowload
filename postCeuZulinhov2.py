import json
import os
import random
import re
from typing import List, Dict
import boto3
import openai
from random import randint
from atproto import Client

client_ceu_azulinho = Client(base_url='https://bsky.social')
client_s3 = boto3.client('s3')

bucket_default = 'videos-dbl'
already_posted_file = "ja_postados.txt"


def save_already_posted(content):
    client_s3.put_object(
        Bucket=bucket_default,
        Key=already_posted_file,
        Body="\n".join(content).encode("utf-8")
    )


def recover_folders():
    response = client_s3.list_objects_v2(Bucket=bucket_default, Prefix="publicar/", Delimiter='/')
    if 'CommonPrefixes' in response:
        folders_recovered = [content['Prefix'] for content in response['CommonPrefixes']]
        print(folders_recovered)
        return folders_recovered
    else:
        print("Nenhuma pasta encontrada.")


def recover_json_data(daily_folder_post):
    json_file = daily_folder_post + daily_folder_post.split("/")[1] + ".json"
    print(json_file)
    object_recovered = client_s3.get_object(
        Bucket=bucket_default,
        Key=json_file)

    content = object_recovered['Body'].read().decode('utf-8')
    return json.loads(content)


def recover_image(daily_folder_post):
    key = daily_folder_post + "hqdefault.jpg"
    print(key)
    object_recovered = client_s3.get_object(
        Bucket=bucket_default,
        Key=key)

    return object_recovered['Body'].read()


def remove_already_processed(already_posted, folders):
    print(len(folders))
    print(already_posted)
    for posted in already_posted:
        folders.remove(posted)
    print(len(folders))


def recover_file_posted(videos_size):
    print("recovering file posted")
    object_recovered = client_s3.get_object(
        Bucket=bucket_default,
        Key=already_posted_file)

    lines = object_recovered['Body'].read().decode('utf-8')
    retornar = lines.split("\n")
    print(len(retornar))
    print(videos_size)

    if len(retornar) == videos_size:
        print("Already post everything, cleaning and returning")
        client_s3.put_object(Bucket=bucket_default, Key=already_posted_file)
        return []

    return retornar


def create_text_post_chatgpt(json_data):
    prompt = ("""
        Dado o titulo {0}, a descrição {1}, gere um mensagem que chame a
        atenção em rede socias, utilizem titulos e descritivos de temas 
        parecidos. único bloco de texto, no máximo 250 caracteres, não pode passar disso e não use negrito remover qualquer mensao ao github e links do mesmo.
         """.format(
        json_data['titulo'],
        json_data['descrição']
    ))
    print(prompt)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    print("Size post chatgpt ->  {0}".format(len(completion.choices[0].message.content)))
    return completion.choices[0].message.content


def login_ceu_zulinho():
    usuario = os.getenv("USUARIO_CEU_ZULINHO")
    pwd = os.getenv("PWD_CEU_ZULINHO")

    tokens = client_ceu_azulinho.login(
        login=usuario,
        password=pwd
    )


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


def set_facet_url(text: str, url: str):
    text_bytes = text.encode("UTF-8")
    start = len(text_bytes) - len("Vídeo Completo Aqui") - 1
    end = len(text_bytes) - randint(2,10)

    return {
        "index": {
            "byteStart": start,
            "byteEnd": end,
        },
        "features": [
            {
                "$type": "app.bsky.richtext.facet#link",
                "uri": url,
            }
        ]
    }


def parse_facets(text: str, url: str):
    facets = []
    facets.append(
        set_facet_url(text, url)
    )
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
            ]
        })
    return facets


def upload_image(image_bytes, titulo_video):
    images = []

    response = client_ceu_azulinho.upload_blob(image_bytes)
    print(response["blob"])
    images.append({"alt": titulo_video,
                   "image": response["blob"]})

    return images


def post_video(image_bytes, text_post: str, url_video):
    images = upload_image(image_bytes, "")
    print(text_post)
    print(len(text_post))
    post = client_ceu_azulinho.send_post(
        text=text_post,
        facets=parse_facets(text_post, url_video),
        embed={
            "$type": "app.bsky.embed.images",
            "images": images
        }
    )


def run():
    print("running")
    folders = recover_folders()
    already_posted = recover_file_posted(len(folders))
    login_ceu_zulinho()
    remove_already_processed(already_posted, folders)
    qt_videos = len(folders)
    print("We have {0} folders to post".format(qt_videos))
    index_folder_id = random.randint(0, qt_videos - 1)
    print("Randon number was generated number :: {0} ".format(index_folder_id))
    daily_folder_post = folders[index_folder_id]
    print("Post will be  {0} ".format(daily_folder_post))
    json_data = recover_json_data(daily_folder_post)
    post_video(
        recover_image(daily_folder_post),
        create_text_post_chatgpt(json_data) + " Vídeo Completo Aqui",
        json_data['url']
    )
    already_posted.append(str(daily_folder_post))
    save_already_posted(already_posted)

def lambda_handler(event, context):
    print("iniciando")
    run()
