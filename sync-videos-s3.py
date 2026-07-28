import json
import os
import re
import requests
import isodate
import unidecode
from dotenv import load_dotenv
import boto3

linhas_remover = [
    '⬇️⬇️⬇️ Siga em outras redes sociais ⬇️⬇️⬇️:',
    'https://www.tiktok.com/@thedigitalbricklayer',
    'https://linkedin.com/in/vitorhcs',
    'https://instagram.com/thedigitalbricklayer',
    'https://x.com/dbl_dev',
    'https://bsky.app/profile/digitalbricklayer.bsky.social',
    '☕ Playlist  JAVA  ☕https://youtu.be/lT5m9hLnyy0?si=Zqm7GPd6gyGjJCCr',
    '☁️ Playlist AWS ☁️  https://youtu.be/GYE3Ql_id1Q?si=86abZooxeXggCygq'
]

bucket = 'videos-dbl'
prefix_folder = 'publicar'
client_s3 = boto3.client('s3')
load_dotenv()

api_key = os.getenv('API_KEY')
channel_id = os.getenv('CHANNEL_ID')


def get_all_videos():
    url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    uploads_playlist_id = "PL1m32XfQHqh7fJyEeuftjqdjG_D0T29Vw"

    videos = []
    next_page_token = None

    while True:
        params = {
            'part': 'snippet,contentDetails',
            'playlistId': uploads_playlist_id,
            'maxResults': 50,
            'pageToken': next_page_token,
            'key': api_key
        }
        response = requests.get(url, params=params)
        data = response.json()
        video_ids = [item['contentDetails']['videoId'] for item in data['items']]
        videos.extend(video_ids)

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return videos


def get_youtube_videos(video_ids):
    ja_inseridos = []
    videos = []
    url = 'https://www.googleapis.com/youtube/v3/videos'

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        params = {
            'part': 'snippet,contentDetails,liveStreamingDetails',
            'id': ','.join(batch_ids),
            'key': api_key
        }
        response = requests.get(url, params=params)
        videos_response = response.json()

        for video in videos_response.get('items', []):
            duration = video['contentDetails']['duration']
            duration_seconds = isodate.parse_duration(duration).total_seconds()
            if video['snippet']['title'] not in ja_inseridos:
                video_data = {
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'videoId': video['id'],
                    'publishedAt': video['snippet']['publishedAt'],
                    'duration': duration_seconds
                }
                videos.append(video_data)
                ja_inseridos.append(video['snippet']['title'])
    return videos


def dowloadImage(url_image, dir_image):
    print("Baixando imagem")
    file_name = os.path.basename(url_image)
    image = requests.get(url_image)
    if image.status_code == 200:
        imagem_disco = bucket + "/" + dir_image + "/" + file_name
        client_s3.put_object(
            Bucket=bucket,
            Key=prefix_folder + "/" + dir_image + "/" + file_name,
            Body=image.content
        )
        print(f"Imagem salva em {imagem_disco}")
    else:
        print("Erro ao baixar a imagem")


def limpa_descricao(descricao: str):
    descricao_final = ""
    for linha in descricao.split("\n"):
        if linha.startswith("#"):
            continue
        resultado = re.sub(r'\d{1,2}:\d{2}(?:\s+[^\d\s]+)*', '', linha).strip()
        for texto_remover in linhas_remover:
            resultado = resultado.replace(texto_remover.strip(), "")
        if resultado:
            descricao_final += resultado
    return descricao_final


def recover_folders_already_saved():
    response = client_s3.list_objects_v2(Bucket=bucket, Prefix="publicar/", Delimiter='/')
    if 'CommonPrefixes' in response:
        folders_recovered = [content['Prefix'] for content in response['CommonPrefixes']]
        print(folders_recovered)
        return folders_recovered
    else:
        print("Nenhuma pasta encontrada.")
        return []


def main():
    folders_already_saved = recover_folders_already_saved()
    videos_ids = get_all_videos()
    videos = get_youtube_videos(videos_ids)
    for video in videos:
        video_titulo = unidecode.unidecode(str(video['title']).replace(" ", "-"))
        video_titulo = re.sub(r'[^a-zA-Z0-9-]', '', video_titulo)
        if video_titulo in folders_already_saved:
            print("video was already saved " + video_titulo)
            continue
        dowloadImage(video['thumbnail'], f"{video_titulo}")
        dados = {
            "titulo": video['title'],
            "descrição": limpa_descricao(video['description']),
            "video_id": video['videoId'],
            "url": f"https://www.youtube.com/watch?v={video['videoId']}"
        }
        client_s3.put_object(
            Bucket=bucket,
            Key=prefix_folder + "/" + video_titulo + "/" + f"{video_titulo}.json",
            Body=(bytes(json.dumps(dados, ensure_ascii=False, indent=4).encode('UTF-8')))
        )


def lambda_handler(event, context):
    print("iniciando")
    main()