def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        mobile1 TEXT,
        mobile2 TEXT,
        role TEXT,
        address TEXT,
        bank_details TEXT,
        username TEXT UNIQUE,
        password TEXT,
        company TEXT,
        photo TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)
    conn.commit()
    conn.close()