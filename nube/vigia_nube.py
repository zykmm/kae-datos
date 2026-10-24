"""Vigía EN LA NUBE (GitHub Actions, cada 2 h; funciona con el PC de Alexis apagado). 24-oct-2026.

Comprueba que AnimeAV1 se sigue leyendo como lo lee Kae (catálogo, ficha, episodio con servidores conocidos) y que
el dominio no se mudó. Si el estado CAMBIA (deja de funcionar o vuelve) avisa al móvil por ntfy (secreto NTFY_TEMA).
El estado se guarda en `nube/estado.json` del propio repo (lo sube el workflow).
"""
import json
import os
import pathlib
import re
import urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
SERVIDORES = ('HLS', 'Voe', 'UPNShare', 'MP4Upload', 'Mp4Upload')
AQUI = pathlib.Path(__file__).resolve().parent
ESTADO = AQUI / 'estado.json'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'es-419,es;q=0.9'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.geturl(), r.read().decode('utf-8', 'replace')


def dominio_actual():
    datos = json.loads((AQUI.parent / 'datos.json').read_text(encoding='utf-8'))
    return json.loads(datos['cuerpo']).get('animeav1') or 'https://animeav1.com'


def comprobar(base):
    fallos = []
    final, _ = get(base + '/')
    llegada = re.match(r'https?://[^/]+', final).group(0)
    if llegada.rstrip('/') != base.rstrip('/'):
        fallos.append(f'el sitio redirige a {llegada} (la app se cambia sola si es la misma web)')
    _, cat = get(llegada + '/catalogo?order=popular')
    i = cat.find('results:[')
    items = re.findall(r'\{id:"?(\d+)"?,title:"[^"]*"[^{}]*?slug:"([a-z0-9-]+)"', cat[i:]) if i >= 0 else []
    if len(items) < 10:
        return fallos + [f'catálogo: {len(items)} animes leídos (cambió el formato)']
    slug = items[0][1]
    _, ficha = get(f'{llegada}/media/{slug}')
    if 'media:{' not in ficha or 'episodes:' not in ficha:
        fallos.append(f'ficha de {slug}: no se encuentra media/episodes')
    _, ep = get(f'{llegada}/media/{slug}/1')
    if 'embeds:' not in ep:
        fallos.append(f'episodio 1 de {slug}: sin embeds')
    elif not any(f'server:"{s}"' in ep for s in SERVIDORES):
        fallos.append(f'episodio 1 de {slug}: ningún servidor conocido')
    return fallos


def avisar(titulo, texto):
    tema = os.environ.get('NTFY_TEMA', '').strip()
    if not tema:
        return
    req = urllib.request.Request(f'https://ntfy.sh/{tema}', data=texto.encode('utf-8'),
                                 headers={'Title': titulo.encode('ascii', 'ignore').decode(), 'Tags': 'kae'})
    urllib.request.urlopen(req, timeout=20).read()


def main():
    base = dominio_actual()
    try:
        fallos = comprobar(base)
    except OSError as e:
        fallos = [f'sin respuesta de {base}: {e}']
    antes = json.loads(ESTADO.read_text()) if ESTADO.exists() else {'fallos': []}
    if fallos != antes.get('fallos'):
        if fallos:
            avisar('Kae: AnimeAV1 cambio', '\n'.join(fallos) + '\n\nCambiar dominio: GitHub > kae-datos > Actions > Cambiar dominio')
        else:
            avisar('Kae: todo bien otra vez', f'AnimeAV1 ({base}) se lee bien.')
        ESTADO.write_text(json.dumps({'fallos': fallos}, ensure_ascii=False), encoding='utf-8')
    print('OK' if not fallos else 'FALLOS: ' + ' | '.join(fallos))


if __name__ == '__main__':
    main()
