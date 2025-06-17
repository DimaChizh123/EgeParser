import hashlib
import re

import aiohttp
import base64

from aiogram.types import BufferedInputFile


def simplify(s, n, p):
    fio = (s + n + p).lower()
    fio = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]+', '', fio)
    fio = fio.replace('ё', 'е').replace('й', 'и')
    return fio

def get_hash(s, n, p):
    return hashlib.md5(simplify(s, n, p).encode("utf-8")).hexdigest()

async def get_captcha():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://checkege.rustest.ru/api/captcha") as resp:
            captcha = await resp.json()
            image_b64 = captcha["Image"]
            token = captcha["Token"]
            image_bytes = base64.b64decode(image_b64)
            return token, BufferedInputFile(image_bytes, filename="captcha.jpg")

async def register(surname, name, patronymic, doc_type, document, region, token, captcha_code):
    async with aiohttp.ClientSession() as session:
        data = {
            "Hash": get_hash(surname, name, patronymic),
            "Region": region,
            "AgereeCheck": "on",
            "Captcha": captcha_code,
            "Token": token,
            "reCaptureToken": captcha_code
        }
        if doc_type == "code":
            data["Code"] = str(document)
        else:
            data["Document"] = ("0" * (12 - len(str(document)))) + str(document)

        async with session.post("https://checkege.rustest.ru/api/participant/login", data=data) as cookie:
            if cookie.status == 204:
                return cookie.headers["Set-Cookie"]
    return ""

