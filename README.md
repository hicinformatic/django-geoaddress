# django-geoaddress

Django integration for address verification and geocoding. Provides Django fields, widgets, and admin integration for the [geoaddress](https://github.com/hicinformatic/python-geoaddress) library.

## Installation

```bash
pip install django-geoaddress
```

## Features

- **Django Model Fields**: `GeoaddressField` for storing address data in Django models
- **Autocomplete Widget**: Interactive address autocomplete widget with real-time suggestions
- **Admin Integration**: Django admin interface for managing addresses and providers
- **Multiple Providers**: Support for multiple geocoding providers (Google Maps, Mapbox, Nominatim, etc.)
- **Virtual Models**: Uses `django-virtualqueryset` for dynamic provider and address models
- **Address Management**: View, search, and manage addresses through Django admin

## Quick Start

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'djgeoaddress',
]
```

### 2. Include URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('geoaddress/', include('djgeoaddress.urls')),
]
```

### 3. Use in Models

```python
from django.db import models
from djgeoaddress.fields import GeoaddressField

class MyModel(models.Model):
    address = GeoaddressField()
    # ... other fields
```

### 4. Use in Forms

The `GeoaddressField` automatically uses the `GeoaddressAutocompleteWidget` which provides:
- Real-time address autocomplete
- Address search across multiple providers
- Structured address data storage

## Address Field

The `GeoaddressField` stores address data as JSON with the following structure:

```python
{
    "text": "Full formatted address string",
    "reference": "Backend reference ID",
    "address_line1": "Street number and name",
    "address_line2": "Building, apartment (optional)",
    "city": "City name",
    "postal_code": "Postal/ZIP code",
    "state": "State/region/province",
    "country": "Country name",
    "country_code": "ISO country code (e.g., FR, US, GB)",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "backend_name": "nominatim",
    "geoaddress_id": "nominatim-123456"
}
```

## Admin Interface

Django-geoaddress provides admin interfaces for:

- **Address Management**: View and manage addresses with search and filtering
- **Provider Management**: View available geocoding providers and their capabilities
- **Address Autocomplete**: Interactive autocomplete in admin forms

Access the admin at:
- Addresses: `/admin/djgeoaddress/address/`
- Providers: `/admin/djgeoaddress/provider/`

## Supported Providers

The library supports multiple geocoding providers through the `geoaddress` library:

**Free providers** (no API key required):
- Nominatim (OpenStreetMap)
- Photon (Komoot/OSM)

**Paid/API key providers**:
- Google Maps
- Mapbox
- LocationIQ
- OpenCage
- Geocode Earth
- Geoapify
- Maps.co
- HERE

## Configuration

### Provider Configuration

Configure geocoding providers in your Django settings or through environment variables. Each provider may require API keys or specific configuration.

Example:

```python
# settings.py
GEOADDRESS_PROVIDERS = {
    'google_maps': {
        'api_key': 'your-api-key',
    },
    'mapbox': {
        'api_key': 'your-api-key',
    },
}
```

## Requirements

- Django >= 3.2
- Python >= 3.10
- geoaddress (automatically installed as dependency)
- django-virtualqueryset (for virtual models)

## Development

```bash
# Clone the repository
git clone https://github.com/hicinformatic/django-geoaddress.git
cd django-geoaddress

# Install in development mode
pip install -e .
pip install -e ".[dev]"
```

## License

MIT License - see LICENSE file for details.

## Links

- **Homepage**: https://github.com/hicinformatic/django-geoaddress
- **Repository**: https://github.com/hicinformatic/django-geoaddress
- **Issues**: https://github.com/hicinformatic/django-geoaddress/issues
- **geoaddress library**: https://github.com/hicinformatic/python-geoaddress

