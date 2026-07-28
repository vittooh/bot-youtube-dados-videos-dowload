import json
import os
import re

import isodate
import requests
import unidecode
from dotenv import load_dotenv
from googleapiclient.discovery import build

linhas_remover = open("textoEliminarDescrição.txt", encoding='utf-8').readlines()
load_dotenv()

api_key = os.getenv('API_KEY')

channel_id = os.getenv('CHANNEL_ID')

youtube = build('youtube', 'v3', developerKey=api_key)


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

        # Check if there is a next page
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return videos


def get_youtube_videos(videos_ids):
    ja_inseridos = []
    videos = []
    youtube = build('youtube', 'v3', developerKey=api_key)

    for i in range(0, len(videos_ids), 50):
        batch_ids = videos_ids[i:i + 50]
        videos_request = youtube.videos().list(
            part='snippet,contentDetails,liveStreamingDetails',
            id=','.join(batch_ids)
        )
        videos_response = videos_request.execute()

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
        imagem_disco = os.path.join(dir_image, file_name)
        with open(imagem_disco, 'wb') as file:
            file.write(image.content)
            print("Imagem salva em {0}".format(imagem_disco))
    else:
        print("deu ruim pra pegar a imagem, pede ajuda pra alguém ")


def limpa_descricao(descricao: str):
    descricao_final = ""
    for linha in descricao.split("\n"):
        if linha.startswith("#"):
            continue
        resultado = re.sub(r'\d{1,2}:\d{2}(?:\s+[^\d\s]+)*', '', linha).strip()
        for texto_remover in linhas_remover:
            resultado = resultado.replace(texto_remover.replace("\n", ""), "")
        if len(resultado) != 0:
            descricao_final = descricao_final + resultado
    return descricao_final


def main():
    videos_ids = get_all_videos()
    videos = get_youtube_videos(videos_ids)
    for video in videos:
        # gambiarra para tirar acento, lixo do windows tava reclamando
        video_titulo = unidecode.unidecode(str(video['title']).replace(" ", "-"))
        video_titulo = re.sub(r'[^a-zA-Z0-9-]', '', video_titulo)
        os.makedirs("videos/" + video_titulo, )
        dowloadImage(video['thumbnail'], "videos/" + video_titulo)
        dados = {
            "titulo": video['title'],
            "descrição": limpa_descricao(video['description']),
            "video_id": video['videoId'],
            "url": "https://www.youtube.com/watch?v={0}".format(video['videoId'])
        }
        video_json = os.path.join("videos/" + video_titulo, video_titulo + ".json")
        with open(video_json, 'w', encoding='utf-8') as json_file:
            json.dump(dados, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
