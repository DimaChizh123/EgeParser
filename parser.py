import asyncio
import hashlib
import re

import aiohttp
import cv2
import numpy as np
import base64
from PIL import Image
from io import BytesIO
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

def simplify(s, n, p):
    fio = (s + n + p).lower()
    fio = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]+', '', fio)
    fio = fio.replace('ё', 'е').replace('й', 'и')
    return fio

def get_hash(s, n, p):
    return hashlib.md5(simplify(s, n, p).encode("utf-8")).hexdigest()

def solve_captcha_sync(image):
    image = image.convert("RGB")
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    image_cv = cv2.resize(image_cv, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)

    lower_gray = np.array([0, 0, 160])
    upper_gray = np.array([180, 40, 255])
    mask_zigzag = cv2.inRange(hsv, lower_gray, upper_gray)

    image_no_zigzag = image_cv.copy()
    image_no_zigzag[mask_zigzag == 255] = [0, 0, 0]

    gray = cv2.cvtColor(image_no_zigzag, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    result = cv2.bitwise_not(binary)

    result_rgb = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
    text_list = reader.readtext(result_rgb, detail=0, allowlist='0123456789')

    captcha_code = ''.join(text_list).replace(" ", "").strip()

    corrections = {'O': '0', 'D': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8', 'Z': '2', 'g': '9'}
    captcha_code = ''.join(corrections.get(c, c) for c in captcha_code)
    captcha_code = ''.join(filter(str.isdigit, captcha_code))[:6]

    return captcha_code

async def solve_captcha(image):
    return await asyncio.to_thread(solve_captcha_sync, image)

async def register(surname, name, patronymic, doc_type, document, region):
    attempt = 0
    async with aiohttp.ClientSession() as session:
        while attempt < 15:
            attempt += 1
            async with session.get("https://checkege.rustest.ru/api/captcha") as resp:
                captcha = await resp.json()
            image_b64 = captcha["Image"]
            token = captcha["Token"]

            image_bytes = base64.b64decode(image_b64)
            image = Image.open(BytesIO(image_bytes))

            captcha_code = await solve_captcha(image)
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

