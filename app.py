# -*- coding: utf-8 -*-
"""
Main application entry point for Vercel, Gunicorn, Render, Railway, etc.
Exposes standard WSGI 'app' and 'application' variables.
"""
import server
import wsgi_adapter

# Universal WSGI callable for Vercel, Gunicorn, uWSGI, AWS
app = wsgi_adapter.create_wsgi_app(server)
application = app
handler = server.MinhAnServerHandler

if __name__ == "__main__":
    server.run()
