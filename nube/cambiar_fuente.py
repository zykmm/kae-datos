"""Pasa TODOS los teléfonos a la fuente de respaldo (JKAnime) o los devuelve a AnimeAV1 (GitHub Actions). 25-nov-2026.

Se lanza desde el botón del aviso de ntfy («AnimeAV1 caído» → «Cambiar a respaldo»), que abre el workflow «Cambiar
fuente»; funciona con el PC apagado. Igual que `cambiar_dominio.py`: toca `"fuente"` en el cuerpo de `datos.json`, sube
`emitido` y lo vuelve a firmar con el secreto CLAVE_DATOS. Los teléfonos se quedan con la config firmada más nueva
(Cloudflare o GitHub) y la app la relee al momento cuando nota AnimeAV1 caído. Cuando el PC vuelva, `publicar.py` adopta
la fuente de aquí (`adoptar_cambios_nube`) para no pisarla.

`"fuente": {"activa": "jkanime"}` = respaldo; sin `activa` (o `"animeav1"`) = lo normal. El resto de `"fuente"` (p. ej.
el dominio de JKAnime) se conserva.
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
FUENTES = ('jkanime', 'animeav1')


def con_fuente(cfg, fuente):
    """[cfg] con la fuente activa cambiada (sin tocar el resto de `"fuente"`). Puro: lo prueba el test."""
    cfg = dict(cfg)
    resto = {k: v for k, v in (cfg.get('fuente') or {}).items() if k != 'activa' and v}
    nueva = {**resto, 'activa': fuente} if fuente != 'animeav1' else resto
    if nueva:
        cfg['fuente'] = nueva
    else:
        cfg.pop('fuente', None)
    return cfg


def main():
    fuente = sys.argv[1].strip().lower()
    if fuente not in FUENTES:
        sys.exit(f'fuente no válida: {fuente} (vale: {", ".join(FUENTES)})')
    datos = json.loads(DATOS.read_text(encoding='utf-8'))
    cfg = con_fuente(json.loads(datos['cuerpo']), fuente)
    cfg['emitido'] = int(time.time())
    cuerpo = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))
    clave = serialization.load_pem_private_key(os.environ['CLAVE_DATOS'].encode(), password=None)
    firma = clave.sign(cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    clave.public_key().verify(firma, cuerpo.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    DATOS.write_text(json.dumps({'cuerpo': cuerpo, 'firma': base64.b64encode(firma).decode()}), encoding='utf-8')
    print(f'fuente de todas las apps: {fuente}')


if __name__ == '__main__':
    main()
