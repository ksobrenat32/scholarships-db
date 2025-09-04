"""
ASGI config for the becas project.

This file configures the ASGI application for the project, which is used for
asynchronous web servers and applications.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'becas.settings')

application = get_asgi_application()
