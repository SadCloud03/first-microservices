from  sqlite3 import connect, Connection, Row
import os
from contextlib import contextmanager
from typing import Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dataBase.db")

def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Ordenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado TEXT DEFAULT 'PENDIENTE',
                total REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Ordenes_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER NOT NULL,
                id_variante INTEGER NOT NULL,
                cantidad INTEGER NOT NULL, 
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (id_orden) REFERENCES Ordenes(id)
            );
    """)



@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    conn = connect(DB_PATH)
    conn.row_factory = Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()