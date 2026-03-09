import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

# 1. Obtenemos la ruta absoluta de la carpeta donde está ESTE archivo (db.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Unimos esa ruta con el nombre del archivo de la DB
# Esto garantiza que siempre apunte a catalog_service/DataBase/dataBase.db
DB_PATH = os.path.join(BASE_DIR, "dataBase.db")


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_categoria TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Marcas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_marca TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_categoria NUMERIC NOT NULL,
                id_marca NUMERIC NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL,
                FOREIGN KEY (id_categoria) REFERENCES Categorias(id),
                FOREIGN KEY (id_marca) REFERENCES Marcas(id)
            );

            CREATE TABLE IF NOT EXISTS Variantes_producto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_producto NUMERIC NOT NULL,
                calce REAL NOT NULL,
                color TEXT NOT NULL,
                stock NUMERIC,
                FOREIGN KEY (id_producto) REFERENCES Productos(id)
            );
        """)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None] : 
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()