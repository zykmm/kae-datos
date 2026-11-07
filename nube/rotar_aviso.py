"""Cambia cada 6 h el número del aviso de mudanza que lee la app vieja (GitHub Actions, sin el PC). 7-nov-2026.

La 3.6.1 calla el aviso por número de versión al tocar «Más tarde»: con otro número, vuelve a salir. Los teléfonos consultan
Cloudflare Y GitHub y se quedan con la config firmada más nueva, así que basta con firmarla aquí; publicar.py usa el mismo
cálculo, de modo que nunca baja el número. Si el aviso no está activo no toca nada.
"""
import base64
import json
import os
import pathlib
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

DATOS = pathlib.Path(__file__).resolve().parent.parent / 'datos.json'
AVISO_CADA_S = 6 * 3600


def main():
    datos = json.loads(DATOS.read_text(encoding='utf-8'))
    cfg = json.loads(datos['cuerpo'])
    app = cfg.get('app') or {}
    if not app.get('avisoRotativo'):
        print('aviso no activo: no se toca nada')
        return
    tanda = int(time.time() // AVISO_CADA_S)
    if app.get('versionCode', 0) >= tanda:
        print(f'el número ya es {app.get("versionCode")}')
        return
    app['versionCode'] = tanda
    cfg['emitido'] = int(time.time())
    cuerpo = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))
    clave = serialization.load_pem_private_key(os.environ['CLAVE_DATOS'].encode(), password=None)
    firma = clave.sign(cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    clave.public_key().verify(firma, cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    DATOS.write_text(json.dumps({'cuerpo': cuerpo, 'firma': base64.b64encode(firma).decode()}), encoding='utf-8')
    print(f'número del aviso: {tanda}')


if __name__ == '__main__':
    main()
