import hashlib
import json
import aiosqlite

async def init_db():
    async with aiosqlite.connect('parser_users.db') as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (tg_id BIGINT PRIMARY KEY, cookie TEXT, response TEXT)")
        await db.commit()

async def get_cookie_from_database(tg_id):
    async with aiosqlite.connect("parser_users.db") as db:
        cursor = await db.execute("SELECT cookie FROM users WHERE tg_id =?", (tg_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def add_to_database(tg_id, cookie, response):
    response = await hash_result(response or {})
    if response is not None:
        async with aiosqlite.connect('parser_users.db') as db:
            await db.execute("INSERT INTO users (tg_id, cookie, response) VALUES (?, ?, ?) ON CONFLICT (tg_id) DO UPDATE SET cookie=excluded.cookie, response = excluded.response", (tg_id, cookie, response))
            await db.commit()

async def get_users():
    async with aiosqlite.connect('parser_users.db') as db:
        cursor = await db.execute("SELECT tg_id, cookie, response FROM users")
        return await cursor.fetchall()

async def remove_user(tg_id):
    async with aiosqlite.connect('parser_users.db') as db:
        await db.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
        await db.commit()

async def hash_result(response):
    try:
        response_to_hash = ""
        for exam in response["Result"]["Exams"]:
            if exam["HasResult"]:
                response_to_hash += exam["Subject"] + str(exam["TestMark"])
        return hashlib.md5(response_to_hash.encode("utf-8")).hexdigest()
    except Exception as e:
        print("Ошибка хеширования")
        return None