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
    response = json.dumps(response or {}, ensure_ascii=False)
    async with aiosqlite.connect('parser_users.db') as db:
        await db.execute("INSERT INTO users (tg_id, cookie, response) VALUES (?, ?, ?) ON CONFLICT (tg_id) DO UPDATE SET cookie=excluded.cookie, response = excluded.response", (tg_id, cookie, response))
        await db.commit()

async def get_users():
    async with aiosqlite.connect('parser_users.db') as db:
        cursor = await db.execute("SELECT tg_id, cookie, response FROM users")
        return await cursor.fetchall()