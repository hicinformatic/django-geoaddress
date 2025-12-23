#!/usr/bin/env python
"""Django's command-line utility for administrative tasks using qualitybase."""
import os

# Import and use qualitybase's django manage.py functions
from qualitybase.services.django.manage import main

# Override DJANGO_SETTINGS_MODULE for this project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

if __name__ == '__main__':
    main()
