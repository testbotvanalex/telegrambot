import os
import aiosqlite
from datetime import datetime

DB_PATH = os.getenv("DB_FILE", "./bot.db") # Используем переменную окружения

def now():
    return datetime.utcnow().isoformat()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            name TEXT,
            address TEXT,
            city TEXT,
            categories TEXT,
            contact TEXT,
            latitude REAL,
            longitude REAL,
            approved INTEGER DEFAULT 0,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS part_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            part_name TEXT,
            quantite TEXT,
            car TEXT,
            photo TEXT,
            requested_at TEXT
        );

        CREATE TABLE IF NOT EXISTS part_request_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            name TEXT,
            qty TEXT,
            FOREIGN KEY (request_id) REFERENCES part_requests(id)
        );

        CREATE TABLE IF NOT EXISTS part_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            request_id INTEGER,
            response_type TEXT,
            responded_at TEXT,
            responder_id INTEGER,
            price TEXT,
            eta TEXT,
            delivery TEXT
        );

        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            responder_id INTEGER,
            responder_username TEXT,
            offer_text TEXT,
            selected INTEGER DEFAULT 0,
            created_at TEXT,
            price TEXT, -- Добавлено для унификации с part_responses.offers
            eta TEXT,     -- Добавлено для унификации
            delivery TEXT -- Добавлено для унификации
        );

        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            part_number TEXT,
            part_name TEXT,
            quantity INTEGER,
            price REAL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            role TEXT DEFAULT 'admin',
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            plan TEXT NOT NULL DEFAULT 'Free',
            status TEXT DEFAULT 'active',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            payment_method TEXT,
            transaction_id TEXT,
            amount REAL,
            payment_date TEXT
        );

        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            button TEXT,
            target TEXT,
            start_date TEXT,
            end_date TEXT,
            active INTEGER DEFAULT 1,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            client_id INTEGER,
            approved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            business TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_telegram_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        await db.commit()

# --- Store Management ---
async def get_store_by_telegram_id(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM stores WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def get_store_by_user_id(telegram_id: int): # Дубликат, но оставлен для совместимости, лучше унифицировать
    return await get_store_by_telegram_id(telegram_id)

async def get_pending_store_by_id(store_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM stores WHERE id = ? AND approved = 0", (store_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def get_pending_stores():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM stores WHERE approved = 0 ORDER BY submitted_at DESC")
        return [dict(row) for row in await cur.fetchall()]

async def get_approved_stores():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM stores WHERE approved = 1 ORDER BY submitted_at DESC")
        return [dict(row) for row in await cur.fetchall()]

async def get_all_stores(search_query: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if search_query:
            cur = await db.execute(
                "SELECT * FROM stores WHERE username LIKE ? OR telegram_id LIKE ? OR name LIKE ? ORDER BY id DESC",
                (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            )
        else:
            cur = await db.execute("SELECT * FROM stores ORDER BY id DESC")
        return [dict(row) for row in await cur.fetchall()]

async def save_store(telegram_id, username, name, address, city, categories, contact, approved, latitude=None, longitude=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO stores
                (telegram_id, username, name, address, city, categories, contact, approved, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, username, name, address, city, categories, contact, approved, latitude, longitude))
        await db.commit()

async def update_store_field(telegram_id: int, field: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        # Важно: SQL-инъекции. Проверяйте 'field' на допустимые значения.
        allowed_fields = {"name", "address", "city", "categories", "contact", "latitude", "longitude", "approved", "status"}
        if field not in allowed_fields:
            raise ValueError(f"Field '{field}' is not allowed for update.")
        await db.execute(f"UPDATE stores SET {field} = ? WHERE telegram_id = ?", (value, telegram_id))
        await db.commit()

async def approve_store(telegram_id: int, status: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE stores SET approved = ? WHERE telegram_id = ?", (1 if status else 0, telegram_id))
        await db.commit()

async def reject_store(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM stores WHERE telegram_id = ?", (telegram_id,))
        await db.commit()

async def update_store_status(telegram_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE stores SET status = ? WHERE telegram_id = ?", (status, telegram_id))
        await db.commit()

async def add_user_note(user_telegram_id: int, note: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO user_notes (user_telegram_id, note) VALUES (?, ?)", (user_telegram_id, note))
        await db.commit()

async def get_user_notes(user_telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM user_notes WHERE user_telegram_id = ? ORDER BY created_at DESC", (user_telegram_id,))
        return [dict(row) for row in await cur.fetchall()]

# --- Request & Offer Management ---
async def get_store_id(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM stores WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_part_request(telegram_id, marque, modele, annee, nom_piece, quantite, photo_id=None):
    store_id = await get_store_id(telegram_id)
    if not store_id:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO part_requests
                (store_id, part_name, quantite, car, photo, requested_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (store_id, nom_piece, quantite, f"{marque} {modele} {annee}", photo_id, now()))
        await db.commit()
        return cur.lastrowid

async def save_part_request_with_items(user_id: int, car_description: str, items: list):
    store_id = await get_store_id(user_id)
    if not store_id:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO part_requests (store_id, part_name, quantite, car, requested_at)
            VALUES (?, ?, ?, ?, ?)
        """, (store_id, "Demande groupée", f"{len(items)} pièces", car_description, now()))
        request_id = cur.lastrowid
        for item in items:
            await db.execute("""
                INSERT INTO part_request_items (request_id, name, qty)
                VALUES (?, ?, ?)
            """, (request_id, item['name'], item['qty']))
        await db.commit()
        return request_id

async def get_requests_by_store(telegram_id: int):
    store_id = await get_store_id(telegram_id)
    if not store_id:
        return []
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT * FROM part_requests
            WHERE store_id = ?
            ORDER BY requested_at DESC
            LIMIT 10
        """, (store_id,))
        return [dict(row) for row in await cur.fetchall()]

async def get_request_by_id(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM part_requests WHERE id = ?", (request_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def save_response(telegram_id: int, request_id: int, response_type: str):
    store_id = await get_store_id(telegram_id)
    if not store_id:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO part_responses
                (store_id, request_id, response_type, responded_at)
            VALUES (?, ?, ?, ?)
        """, (store_id, request_id, response_type, now()))
        await db.commit()

async def save_offer(request_id: int, responder_id: int, responder_username: str, offer_text: str, price: str = "-", eta: str = "-", delivery: str = "-"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO offers (request_id, responder_id, responder_username, offer_text, price, eta, delivery, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (request_id, responder_id, responder_username, offer_text, price, eta, delivery, now())
        )
        await db.commit()

async def save_offer_response(request_id: int, store_id: int, price: str, eta: str, delivery: str):
    # Эта функция дублирует save_offer, но с другими параметрами. Лучше унифицировать.
    # Здесь используется 'store_id' для responder_id, что корректно для ответа магазина.
    # offer_text может быть сгенерирован здесь на основе price, eta, delivery.
    offer_text_generated = f"Prix: {price}, ETA: {eta}, Livraison: {delivery}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO offers
                (request_id, responder_id, responder_username, offer_text, price, eta, delivery, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (request_id, store_id, (await get_store_by_telegram_id(store_id))['username'] or "Inconnu", offer_text_generated, price, eta, delivery, now()))
        await db.commit()


async def get_offers_by_request_id(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM offers WHERE request_id = ? ORDER BY created_at ASC", (request_id,))
        return [dict(row) for row in await cur.fetchall()]

async def confirm_offer_selection(offer_id: int, request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE offers SET selected = 1 WHERE id = ?", (offer_id,))
        # Дополнительно: можно обновить статус request_id, чтобы показать, что предложение выбрано
        await db.execute("UPDATE part_requests SET status = 'completed' WHERE id = ?", (request_id,)) # Если есть столбец status
        await db.commit()

async def mark_offer_as_chosen(offer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT request_id, responder_id, responder_username, offer_text FROM offers WHERE id = ?",
            (offer_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        # Отмечаем предложение как выбранное
        await db.execute(
            "UPDATE offers SET selected = 1, offer_text = offer_text || ' ✅ [CHOISI]' WHERE id = ?",
            (offer_id,)
        )
        # Опционально: отметить запрос как завершенный
        await db.execute(
            "UPDATE part_requests SET status = 'completed' WHERE id = ?",
            (row["request_id"],)
        )
        await db.commit()

        return {
            "request_id": row["request_id"],
            "responder_id": row["responder_id"],
            "responder_username": row["responder_username"],
            "offer_text": row["offer_text"]
        }


# --- Statistics ---
async def get_stats_summary():
    async with aiosqlite.connect(DB_PATH) as db:
        row1 = await db.execute("SELECT COUNT(*) FROM stores")
        row2 = await db.execute("SELECT COUNT(*) FROM part_requests")
        row3 = await db.execute("SELECT COUNT(*) FROM offers")
        row4 = await db.execute("SELECT COUNT(*) FROM stores WHERE approved = 1")
        row5 = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE plan = 'Free'")
        row6 = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE plan = 'Pro'")
        row7 = await db.execute("SELECT COUNT(*) FROM subscriptions WHERE plan = 'VIP'")
        row8 = await db.execute("SELECT COUNT(*) FROM ads WHERE active = 1")
        row9 = await db.execute("SELECT SUM(amount) FROM subscriptions")
        
        return {
            "total_stores": (await row1.fetchone())[0],
            "total_requests": (await row2.fetchone())[0],
            "total_offers": (await row3.fetchone())[0],
            "stores_approved": (await row4.fetchone())[0],
            "users_free": (await row5.fetchone())[0],
            "users_pro": (await row6.fetchone())[0],
            "users_vip": (await row7.fetchone())[0],
            "active_ads": (await row8.fetchone())[0],
            "total_revenue": (await row9.fetchone())[0] if (await row9.fetchone())[0] else 0
        }

# --- Stock Management ---
async def save_stock_items(items: list):
    async with aiosqlite.connect(DB_PATH) as db:
        if items:
            store_id = items[0]['store_id']
            # Удаляем старые записи перед добавлением новых, чтобы избежать дубликатов
            await db.execute("DELETE FROM stock WHERE store_id = ?", (store_id,))
        for item in items:
            await db.execute("""
                INSERT INTO stock (store_id, part_number, part_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (item['store_id'], item['part_number'], item['part_name'], item['quantity'], item['price']))
        await db.commit()

async def get_stock_items_by_store(store_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT part_name, quantity, price FROM stock
            WHERE store_id = ?
            ORDER BY part_name ASC
        """, (store_id,))
        return [dict(row) for row in await cur.fetchall()]

async def search_stock_by_name(part_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT store_id, part_name, quantity, price FROM stock
            WHERE part_name LIKE ?
        """, (f"%{part_name}%",))
        return [dict(row) for row in await cur.fetchall()]

# --- Subscriptions ---
async def get_all_subscriptions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT s.*, st.telegram_id, st.username, st.name 
            FROM subscriptions s 
            JOIN stores st ON s.store_id = st.id 
            ORDER BY expires_at DESC
        """)
        return [dict(row) for row in await cur.fetchall()]

async def get_subscription_by_store_id(store_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM subscriptions WHERE store_id = ?", (store_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def update_subscription(telegram_id: int, plan: str, expires_at: str = None, status: str = None, amount: float = None, payment_method: str = None, transaction_id: str = None):
    store = await get_store_by_telegram_id(telegram_id)
    if not store:
        return
    
    store_id = store['id']
    
    async with aiosqlite.connect(DB_PATH) as db:
        existing_sub = await get_subscription_by_store_id(store_id)
        if existing_sub:
            update_query = "UPDATE subscriptions SET plan = ?"
            params = [plan]
            if expires_at:
                update_query += ", expires_at = ?"
                params.append(expires_at)
            if status:
                update_query += ", status = ?"
                params.append(status)
            if amount is not None:
                update_query += ", amount = ?"
                params.append(amount)
            if payment_method:
                update_query += ", payment_method = ?"
                params.append(payment_method)
            if transaction_id:
                update_query += ", transaction_id = ?"
                params.append(transaction_id)
            
            update_query += " WHERE store_id = ?"
            params.append(store_id)
            await db.execute(update_query, tuple(params))
        else:
            await db.execute(
                "INSERT INTO subscriptions (store_id, plan, expires_at, status, amount, payment_method, transaction_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (store_id, plan, expires_at, status if status else 'active', amount, payment_method, transaction_id)
            )
        await db.commit()

# --- Ads ---
async def create_ad(text: str, button: str, target: str, start_date: str, end_date: str, client_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO ads (text, button, target, start_date, end_date, client_id) VALUES (?, ?, ?, ?, ?, ?)",
            (text, button, target, start_date, end_date, client_id)
        )
        await db.commit()

async def get_ads_list():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM ads ORDER BY created_at DESC")
        return [dict(row) for row in await cur.fetchall()]

async def toggle_ad_status(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT active FROM ads WHERE id = ?", (ad_id,))
        current_status = (await cur.fetchone())[0]
        new_status = 1 if current_status == 0 else 0
        await db.execute("UPDATE ads SET active = ? WHERE id = ?", (new_status, ad_id))
        await db.commit()

async def delete_ad(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
        await db.commit()

async def get_ad_by_id(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def approve_ad(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE ads SET approved = 1 WHERE id = ?", (ad_id,))
        await db.commit()

async def reject_ad(ad_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE ads SET approved = 0 WHERE id = ?", (ad_id,)) # Или удалить
        await db.commit()

# --- Clients ---
async def create_client(name: str, phone: str, business: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO clients (name, phone, business) VALUES (?, ?, ?)", (name, phone, business))
        await db.commit()

async def get_all_clients():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM clients ORDER BY created_at DESC")
        return [dict(row) for row in await cur.fetchall()]

async def get_client_by_id(client_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def save_client(name: str, phone: str, business: str): # Используется существующая, но лучше назвать create_client
    return await create_client(name, phone, business)

async def save_client_note(client_id: int, note: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Это обновит заметку. Если нужно добавлять, то нужно поле TEXT и JSON или отдельная таблица.
        await db.execute("UPDATE clients SET notes = ? WHERE id = ?", (note, client_id))
        await db.commit()

# --- Admins ---
async def add_admin_to_db(telegram_id: int, role: str = 'admin'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO admins (telegram_id, role) VALUES (?, ?)", (telegram_id, role))
        await db.commit()

async def remove_admin_from_db(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
        await db.commit()

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM admins")
        return [dict(row) for row in await cur.fetchall()]

async def get_admin_by_telegram_id(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM admins WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

# --- Settings ---
async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row['value'] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

async def get_all_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM settings")
        return {row['key']: row['value'] for row in await cur.fetchall()}
# --- Users ---
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM stores WHERE telegram_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None                       