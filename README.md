Projeto para baixar o titulo, a descrição e a thumbnail dos vídeos do youtube
dado um channel_id e a chave de api.
Vcs também devem passar uma playlist_id para o script.
Api do youtube é muito instável não estava trazendo todos os videos, o que eu fiz foi criar uma playlist publica no
canal com todos os vídeos qeu eu queria.'
Estou utilizando a api do youtube logo vc precisa entrar e cadastrar uma chave de api
para fazer o projeto funcionar, se atente pq não é 100% free, passou de uma cota o youtube bloqueia e tem que pagar para
liberar.

Como rodar essa :bomba

instala as dependencias.

cria um .env e coloca isso nele
API_KEY=sua_chave_api
CHANNEL_ID=canal desejado.

python recuperaVideos.Py