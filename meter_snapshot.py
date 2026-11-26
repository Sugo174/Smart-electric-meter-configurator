"""Ключи инженера и загрузка зашифрованного снимка прибора."""

import json
from pathlib import Path

from nacl import exceptions, pwhash, secret, utils
from nacl.public import PrivateKey, SealedBox

from snapshot_windows_key import load_windows_key


EXPORT_HEADER = b"EMIS-SNAPSHOT\x01"
KEY_HEADER = b"EMIS-ENGINEER-KEY\x01"
PRIVATE_KEY_NAME = "emis_export_engineer.key"
MAX_SNAPSHOT_SIZE = 1024 * 1024


def _key_cipher(password, salt):
    key = pwhash.argon2id.kdf(
        secret.SecretBox.KEY_SIZE, password.encode("utf-8"), salt,
        opslimit=pwhash.argon2id.OPSLIMIT_INTERACTIVE,
        memlimit=pwhash.argon2id.MEMLIMIT_INTERACTIVE,
    )
    return secret.SecretBox(key)


class SnapshotKeyError(ValueError):
    """Снимок не открывается текущим ключом."""


def backup_engineer_key(directory, password):
    if len(password) < 12:
        raise ValueError("Пароль должен содержать не менее 12 символов.")
    private_path = Path(directory) / PRIVATE_KEY_NAME
    private_key = load_windows_key()
    salt = utils.random(pwhash.argon2id.SALTBYTES)
    encrypted = KEY_HEADER + salt + _key_cipher(password, salt).encrypt(bytes(private_key))
    with private_path.open("xb") as stream:
        stream.write(encrypted)


def _read_bounded(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Размер файла превышает допустимый предел.")
    return data


def _read_portable_key(key_path, password):
    key_data = _read_bounded(key_path, 256)
    if not key_data.startswith(KEY_HEADER):
        raise ValueError("Выбранный файл не является закрытым ключом ЭМИС.")
    salt_start = len(KEY_HEADER)
    salt_end = salt_start + pwhash.argon2id.SALTBYTES
    expected_size = salt_end + secret.SecretBox.NONCE_SIZE + secret.SecretBox.MACBYTES + PrivateKey.SIZE
    if len(key_data) != expected_size:
        raise ValueError("Файл закрытого ключа повреждён.")
    try:
        return PrivateKey(_key_cipher(password, key_data[salt_start:salt_end]).decrypt(key_data[salt_end:]))
    except exceptions.CryptoError as error:
        raise ValueError("Неверный пароль или повреждён файл закрытого ключа.") from error


def load_snapshot(path, key_path=None, password=None):
    encrypted = _read_bounded(path, MAX_SNAPSHOT_SIZE)
    if not encrypted.startswith(EXPORT_HEADER):
        raise ValueError("Файл не является выгрузкой настроек ЭМИС поддерживаемой версии.")
    key = load_windows_key() if key_path is None else _read_portable_key(key_path, password)
    try:
        payload = SealedBox(key).decrypt(encrypted[len(EXPORT_HEADER):])
    except exceptions.CryptoError as error:
        raise SnapshotKeyError("Выгрузка повреждена или зашифрована другим ключом.") from error
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("Версия формата") != 2:
        raise ValueError("Версия данных в выгрузке не поддерживается.")
    return data
