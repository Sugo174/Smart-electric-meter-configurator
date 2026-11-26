"""Шифрование выгрузки открытым ключом инженерной службы."""

import base64
import json

from nacl.public import PublicKey, SealedBox


EXPORT_HEADER = b"EMIS-SNAPSHOT-2\n"
EMIS_PUBLIC_KEY = PublicKey(bytes.fromhex("833f565ef4a27acea21886988630b54912d7b9e2f464a05de24ae5481008e513"))


def encrypt_snapshot(data):
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    encrypted = SealedBox(EMIS_PUBLIC_KEY).encrypt(payload)
    return EXPORT_HEADER + base64.b64encode(encrypted) + b"\n"
