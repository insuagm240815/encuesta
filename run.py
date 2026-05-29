"""
Punto de entrada de la aplicación.

Uso:
    python run.py                    # desarrollo (lee FLASK_ENV del .env)
    FLASK_ENV=production python run.py

El archivo .env se carga automáticamente si existe.
"""
import os
from pathlib import Path

# Cargar .env si existe (sin dependencia de python-dotenv)
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    port = int(os.environ.get("PORT", 5000))
    debug = env != "production"
    print(f"▶ Iniciando en modo '{env}' — http://localhost:{port}")
    app.run(debug=debug, host="0.0.0.0", port=port)
