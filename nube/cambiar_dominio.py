"""Cambia el dominio de AnimeAV1 en `datos.json` y lo vuelve a firmar (GitHub Actions, desde el móvil). 24-oct-2026.

La clave privada llega como secreto CLAVE_DATOS (el contenido de `~/.kae/clave_datos.pem`). Los teléfonos consultan
Cloudflare Y GitHub y se quedan con la config firmada más nueva, así que esto les llega aunque el PC esté apagado.
Cuando el PC vuelva, `publicar.py` adopta el dominio nuevo (lo lee de aquí) para no pisarlo.
"""
import base64
import json
import os
import pathlib
import sys
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

DATOS = pathlib.Path(__file__).resolve().parent.parent / 'datos.json'


def main():
    dominio = sys.argv[1].strip().rstrip('/')
    if not dominio.startswith('https://') or len(dominio) < 12:
        sys.exit(f'dominio no válido (tiene que empezar por https://): {dominio}')
    datos = json.loads(DATOS.read_text(encoding='utf-8'))
    cfg = json.loads(datos['cuerpo'])
    cfg['animeav1'] = dominio
    cfg['emitido'] = int(time.time())
    cuerpo = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))
    clave = serialization.load_pem_private_key(os.environ['CLAVE_DATOS'].encode(), password=None)
    firma = clave.sign(cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    clave.public_key().verify(firma, cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    DATOS.write_text(json.dumps({'cuerpo': cuerpo, 'firma': base64.b64encode(firma).decode()}), encoding='utf-8')
    print(f'dominio cambiado a {dominio}')


if __name__ == '__main__':
    main()
