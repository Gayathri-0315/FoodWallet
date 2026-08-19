import os
import sqlite3

db_path = 'foodwallet.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("--- DB TABLES & COLUMNS ---")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for t in tables:
        table_name = t[0]
        print(f"\nTable: {table_name}")
        cols = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        for col in cols:
            print(f"  Column: {col[1]} ({col[2]})")
else:
    print("DB file not found at", db_path)
