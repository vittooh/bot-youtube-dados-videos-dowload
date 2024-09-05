import json
import os
import random
from transformers import pipeline


def limpa_descricao(descricao: str):
    linhas_remover = open("textoEliminarDescrição.txt", encoding='utf-8').readlines()
    for s in linhas_remover:
        descricao = descricao.replace("\n", "").replace(s.replace("\n", ""), '')
    # o resto o gpt vai ignorar, vou colocar no prompt
    print(descricao)
    return descricao


diretorios = os.listdir("videos")
qt_videos = len(diretorios)
print(qt_videos)
# gerar numeor aleatorio dado o numero de diretorios na pasta
post_video = 52  # random.randint(0, qt_videos - 1)
print("Número aleatório gerado para fazer o post num :: {0} ".format(post_video))
pasta_post_dia = diretorios[post_video]
print("Post será do vídeo {0} ".format(pasta_post_dia))

nome_json = "videos/" + str(pasta_post_dia) + "/" + pasta_post_dia + ".json"
# dado isso agora vamo ler o arquivo json da pasta
# sabemos sim kk, é o nome da pasta + json
with open(nome_json, encoding="utf-8") as file:
    dados_post = json.load(file)

limpa_descricao(dados_post['descrição'])
print(dados_post['titulo'])

prompt = ("""
Dado o titulo {0}, a descrição {1}, gere um mensagem que chame a
atenção em rede socias, utilizem titulos e descritivos de temas 
parecidos, para gerar o texto. Ignore os links de redes sociais, as hashtags e 
 as timestamps
 """.format(
    dados_post['titulo'],
    limpa_descricao(dados_post['descrição'])
))

# Carregar o modelo GPT-2
generator = pipeline('text-generation', model='gpt2')

# Gerar texto
result = generator("me de ideias de video em kotlin me responda em portugues", max_length=700, num_return_sequences=1)
print(result)
