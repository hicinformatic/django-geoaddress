# Test App - GeoaddressField Example

Cette application de test démontre l'utilisation du champ `GeoaddressField` dans un modèle Django.

## Modèle Location

Le modèle `Location` utilise le champ `GeoaddressField` pour stocker des données d'adresse complètes selon le format standardisé de geoaddress.

### Exemple d'utilisation

```python
from tests.app.models import Location

# Créer une location avec une adresse
location = Location.objects.create(
    name="Bureau principal",
    address={
        "text": "123 Rue de la République, 75001 Paris, France",
        "address_line1": "123 Rue de la République",
        "city": "Paris",
        "postal_code": "75001",
        "country": "France",
        "country_code": "FR",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "backend_name": "nominatim",
    }
)

# Accéder aux données d'adresse
print(location.address["text"])  # "123 Rue de la République, 75001 Paris, France"
print(location.address["city"])  # "Paris"
print(location.address["latitude"])  # 48.8566
```

## Champs disponibles

Le champ `GeoaddressField` accepte tous les champs définis dans `GEOADDRESS_FIELDS_DESCRIPTIONS` :

- `text`: Adresse complète formatée
- `reference`: ID de référence du backend
- `address_line1`, `address_line2`, `address_line3`: Lignes d'adresse
- `city`: Ville
- `postal_code`: Code postal
- `state`, `region`: État/Région
- `country`, `country_code`: Pays
- `municipality`, `neighbourhood`: Municipalité, quartier
- `address_type`: Type d'adresse
- `latitude`, `longitude`: Coordonnées
- `osm_id`, `osm_type`: Identifiants OpenStreetMap
- `confidence`, `relevance`: Scores de confiance et pertinence
- `backend`, `backend_name`: Informations sur le backend
- `geoaddress_id`: ID combiné

## Validation

Le champ valide automatiquement :
- Que toutes les clés correspondent aux champs valides de geoaddress
- Que les types de données sont corrects (float pour latitude/longitude/confidence/relevance, string pour les autres)

## Admin

Le modèle est enregistré dans l'admin Django et permet de gérer les locations avec leurs adresses.

