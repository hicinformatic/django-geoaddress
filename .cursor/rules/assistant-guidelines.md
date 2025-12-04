## Assistant Guidelines

### Project Purpose

**django-geoaddress** provides Django integration for **python-geoaddress**, which handles address verification and geocoding. The library provides backends for:
- Address geocoding (address → coordinates)
- Reverse geocoding (coordinates → address)
- Address validation and normalization
- Address autocomplete
- Multiple backend support (Nominatim, Google Maps, postal services, etc.)

Backends in python-geoaddress are organized by **service type** (geocoding, postal, validation).

### Development Guidelines

- Always execute project tooling through `python dev.py <command>`.
- Default to English for comments, docstrings, and translations.
- Keep comments minimal and only when they clarify non-obvious logic.
- Avoid reiterating what the code already states clearly.
- Add comments only when they resolve likely ambiguity or uncertainty.
- Keep integration with `python-geoaddress` clean: use the library for all address operations (geocoding, validation, normalization) without reimplementing core logic in Django models or views.
- Django models should store address data but delegate geocoding/validation logic to `geoaddress` (python-geoaddress module).
- Use Django signals and tasks (Celery/Django-Q) for async operations like batch geocoding.
- Address fields should support multiple formats and international addresses.
- Models should store both structured address components and geocoding results (coordinates, confidence scores).
- API endpoints should follow REST conventions and include proper pagination, filtering, and search capabilities.
- Admin interface should provide address search, geocoding triggers, and map visualization.
- Always handle API rate limits and failures gracefully with proper retry logic.
- Support backend switching and fallback mechanisms for resilience.
