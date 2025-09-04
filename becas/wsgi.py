"""
WSGI config for the becas project.

This file configures the WSGI application for the project, which is used for
synchronous web servers and applications.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'becas.settings')

application = get_wsgi_application()
