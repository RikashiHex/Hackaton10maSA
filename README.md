# Gestor de Residuos

Aplicación de escritorio local para registrar, clasificar y consultar residuos. Los datos se almacenan en SQLite y las fotografías se copian a `assets/residuos/`; no requiere internet, servidor ni servicios externos.

## Requisitos

- Python 3.10 o superior

## Instalación y ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flet run main.py
```

También puede iniciarse con `python main.py` después de instalar las dependencias. La app requiere Flet 1.x.

## Contenido

- Dashboard con totales, categorías y registros recientes.
- CRUD de residuos con búsqueda, filtro por categoría/estado y fotografías.
- CRUD de categorías con protección contra eliminar categorías en uso.
- Base SQLite creada automáticamente en `data/residuos.db`.
