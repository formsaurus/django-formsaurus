# boot_django.py
#
# This file sets up and configures Django. It's used by scripts that need to
# execute as if running in a Django server.
import os
import django
from django.conf import settings
from django.urls import path, include

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "formsaurus"))

def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        DATABASES={
            "default":{
                "ENGINE":"django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            }
        },
        INSTALLED_APPS=(
            'femtolytics',
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ),
        TIME_ZONE="UTC",
        USE_TZ=True,
        ROOT_URLCONF = 'boot_urls',
    )
    django.setup()