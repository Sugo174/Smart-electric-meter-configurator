"""Ключи инженера и загрузка зашифрованного снимка прибора."""

import base64
import binascii
import json
from pathlib import Path

from nacl import exceptions
from nacl.public import PrivateKey, SealedBox

from snapshot_windows_key import load_windows_key


LEGACY_EXPORT_HEADER = b"EMIS-SNAPSHOT\x01"
EXPORT_HEADER = b"EMIS-SNAPSHOT-2\n"
MAX_SNAPSHOT_SIZE = 1024 * 1024


def _load_engineer_key():
    try:
        from _emis_internal_snapshot_key import PRIVATE_KEY
    except ModuleNotFoundError as error:
        if error.name != "_emis_internal_snapshot_key":
            raise
        try:
            return load_windows_key()
        except FileNotFoundError as missing:
            raise ValueError("Для открытия выгрузки используйте внутреннюю сборку ЭМИС.") from missing
    return PrivateKey(PRIVATE_KEY)


def _read_bounded(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Размер файла превышает допустимый предел.")
    return data


def load_snapshot(path):
    data = _read_bounded(path, MAX_SNAPSHOT_SIZE)
    if data.startswith(EXPORT_HEADER):
        try:
            encrypted = base64.b64decode(data[len(EXPORT_HEADER):].rstrip(b"\r\n"), validate=True)
        except binascii.Error as error:
            raise ValueError("Текстовая выгрузка ЭМИС повреждена.") from error
    elif data.startswith(LEGACY_EXPORT_HEADER):
        encrypted = data[len(LEGACY_EXPORT_HEADER):]
    else:
        raise ValueError("Файл не является выгрузкой настроек ЭМИС поддерживаемой версии.")
    key = _load_engineer_key()
    try:
        payload = SealedBox(key).decrypt(encrypted)
    except exceptions.CryptoError as error:
        raise ValueError("Выгрузка повреждена или зашифрована другим ключом.") from error
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("Версия формата") != 2:
        raise ValueError("Версия данных в выгрузке не поддерживается.")
    return data
