"""
ASGI config for ncjm project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

import environ
from django.core.asgi import get_asgi_application

env = environ.Env()
environ.Env.read_env()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", env("DJANGO_SETTINGS_MODULE"))

application = get_asgi_application()
