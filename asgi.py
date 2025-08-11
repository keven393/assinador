# asgi.py
from asgiref.wsgi import WsgiToAsgi
from app import app
# Converte Flask (WSGI) para ASGI para usar com Uvicorn
asgi_app = WsgiToAsgi(app)