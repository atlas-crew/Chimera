#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create the application instance
app = create_app()
