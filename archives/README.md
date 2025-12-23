# django-geoaddress

Django integration for address verification and geocoding using python-geoaddress.

This is a minimal Django app ready for migration of existing tools.

## Installation

```bash
pip install django-geoaddress
```

## Quick Start

```python
INSTALLED_APPS = [
    ...
    'djgeoaddress',
]
```

## Development

```bash
python dev.py venv
python dev.py install-dev
python dev.py update-geoaddress
python dev.py migrate
python dev.py runserver
```

## License

MIT

