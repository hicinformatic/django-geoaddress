from rest_framework.fields import JSONField

class AddressField(JSONField):
    """Custom field for address with personalized metadata."""

    extra_metadata = {
        "type": "address",
    }

    def __init__(self, **kwargs: any):
        """Initialize with custom metadata."""
        kwargs.setdefault("required", True)
        kwargs.setdefault("read_only", False)
        kwargs.setdefault("label", "Address")
        kwargs.setdefault("help_text", "Address information")
        super().__init__(**kwargs)

    def get_url_search_address(self) -> str:
        """Return the URL to search for addresses."""
        from django.urls import reverse
        return reverse("djgeoaddress:search_addresses")

    def get_fields_info(self) -> dict:
        from geoaddress import GEOADDRESS_FIELDS_ESSENTIALS
        return {
            field_name: {
                "label": field_info["label"],
                "description": field_info["description"],
                "format": field_info["format"],
            }
            for field_name, field_info in GEOADDRESS_FIELDS_ESSENTIALS.items()
        }

    def get_extra_metadata(self) -> dict:
        """Get extra metadata, computing URLs lazily."""
        metadata = self.extra_metadata.copy()
        metadata["url_search_address"] = self.get_url_search_address()
        metadata["arg_search_address"] = "query"
        metadata["fields_info"] = self.get_fields_info()
        return metadata