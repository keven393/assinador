# asgi.py
from asgiref.wsgi import WsgiToAsgi
from app import create_app

# Cria a aplicação Flask com configurações de produção
app = create_app('production')

# Converte Flask (WSGI) para ASGI para usar com Uvicorn
asgi_app = WsgiToAsgi(app)