import json
import os
import re

import isodate
import requests
import unidecode
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

api_key = os.getenv('API_KEY')

channel_id = os.getenv('CHANNEL_ID')


def get_youtube_videos():
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    next_page_token = None
    # api parece que se perde e retorna resultados repetidos, tenho que olhar com calma
    # por hora isso resolve.
    ja_inseridos = []

    while True:
        search_request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            type='video',
            maxResults=50,
            pageToken=next_page_token
        )
        search_response = search_request.execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            break

        videos_request = youtube.videos().list(
            part='snippet,contentDetails,liveStreamingDetails',
            id=','.join(video_ids)
        )
        videos_response = videos_request.execute()

        for video in videos_response.get('items', []):
            duration = video['contentDetails']['duration']
            duration_seconds = isodate.parse_duration(duration).total_seconds()
            if 'liveStreamingDetails' in video.keys():
                print("pulando video de live {0}".format(video['snippet']['title']))
                continue

            if duration_seconds < 120:
                print("pulando video com duracao menor que 120 segundos aka shorts {0} "
                      "duracao(s) e titulo '{1}'".
                      format(duration_seconds, video['snippet']['title']))
                continue
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

        next_page_token = search_response.get('nextPageToken')
        if not next_page_token:
            break

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


def main():
    videos = get_youtube_videos()
    for video in videos:
        # gambiarra para tirar acento, lixo do windows tava reclamando
        video_titulo = unidecode.unidecode(str(video['title']).replace(" ", "-"))
        video_titulo = re.sub(r'[^a-zA-Z0-9-]', '', video_titulo)
        os.makedirs("videos/" + video_titulo, )
        dowloadImage(video['thumbnail'], "videos/" + video_titulo)
        dados = {
            "titulo": video['title'],
            "descrição": video['description'],
            "video_id": video['videoId'],
            "url": "https://www.youtube.com/watch?v={0}".format(video['videoId'])
        }
        video_json = os.path.join("videos/" + video_titulo, video_titulo + ".json")
        with open(video_json, 'w', encoding='utf-8') as json_file:
            json.dump(dados, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
