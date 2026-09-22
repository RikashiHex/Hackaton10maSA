"""Conexión y preparación de la base de datos local."""
from pathlib import Path
import sqlite3


ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "residuos.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
                descripcion TEXT DEFAULT '',
                tipo TEXT NOT NULL DEFAULT 'Reciclable',
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS residuos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                categoria_id INTEGER NOT NULL,
                cantidad REAL NOT NULL CHECK(cantidad >= 0),
                unidad TEXT NOT NULL,
                fecha_registro TEXT NOT NULL,
                ubicacion TEXT DEFAULT '',
                estado TEXT NOT NULL,
                foto TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT
            );
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
        if not count:
            connection.executemany(
                "INSERT INTO categorias (nombre, descripcion, tipo) VALUES (?, ?, ?)",
                [
                    ("Orgánico", "Residuos biodegradables", "Orgánico"),
                    ("Plástico", "Envases y plásticos", "Reciclable"),
                    ("Papel y cartón", "Papel reciclable", "Reciclable"),
                    ("Vidrio", "Envases de vidrio", "Reciclable"),
                    ("Metal", "Latas y objetos metálicos", "Reciclable"),
                    ("Electrónico", "Aparatos y componentes", "Especial"),
                    ("Peligroso", "Pilas, químicos y similares", "Peligroso"),
                    ("Otros", "Residuos sin clasificar", "No reciclable"),
                ],
            )
