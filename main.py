# -*- coding: utf-8 -*-
"""
Main entry point alias for Vercel, Gunicorn, Render, Railway, etc.
Exposes standard WSGI 'app' and 'application' variables.
"""
import server
import wsgi_adapter

app = wsgi_adapter.create_wsgi_app(server)
application = app
handler = server.MinhAnServerHandler

if __name__ == "__main__":
    server.run()
