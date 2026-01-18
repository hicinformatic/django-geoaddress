"""Admin for provider model."""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django_boosted import AdminBoostModel

from ..models.provider import ProviderModel


class PackagesInstalledFilter(admin.SimpleListFilter):
    """Filter for packages installed status using pkg alias."""

    title = _("Packages installed")
    parameter_name = "pkg"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


class ServicesImplementedFilter(admin.SimpleListFilter):
    """Filter for services implemented status using svc alias."""

    title = _("Services implemented")
    parameter_name = "svc"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


class ConfigReadyFilter(admin.SimpleListFilter):
    """Filter for config ready status using cfg alias."""

    title = _("Config ready")
    parameter_name = "cfg"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


@admin.register(ProviderModel)
class ProviderAdmin(AdminBoostModel):
    """Simple admin for geoaddress providers."""

    list_display = [
        "name",
        "display_name",
        "description",
        "are_packages_installed",
        "are_services_implemented",
        "is_config_ready",
        "has_search_addresses",
        "cost_search_addresses",
        "has_addresses_autocomplete",
        "cost_addresses_autocomplete",
        "has_reverse_geocode",
        "cost_reverse_geocode",
    ]
    list_filter = [PackagesInstalledFilter, ServicesImplementedFilter, ConfigReadyFilter]
    search_fields = ["name", "display_name", "description"]
    readonly_fields = [
        "name",
        "display_name",
        "description",
        "required_packages",
        "config_keys",
        "config_required",
        "config_prefix",
        "services",
        "are_packages_installed",
        "are_services_implemented",
        "is_config_ready",
        "missing_config_keys_display",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "display_name",
                    "description",
                    "status_url",
                    "documentation_url",
                    "site_url",
                ],
            },
        ),
        (
            _("Packages"),
            {
                "fields": [
                    "required_packages_display",
                    "are_packages_installed",
                    "missing_packages_display",
                ],
            },
        ),
        (
            _("Config"),
            {
                "fields": [
                    "config_prefix_display",
                    "config_keys_display",
                    "config_required_display",
                    "is_config_ready",
                    "missing_config_keys_display",
                ],
            },
        ),
        (
            _("Services"),
            {
                "fields": [
                    "services_display",
                    "are_services_implemented",
                    "missing_services_display",
                ],
            },
        ),
    ]

    def change_fieldsets(self):
        self.add_to_fieldset("Packages", ["required_packages"])

    def get_queryset(self, request):
        """Get queryset with query_string and attribute_search parameters from request."""
        from ..managers.provider import ProviderManager

        query_string = request.GET.get("q", "").strip()
        attribute_search = {}

        for alias, attr_name in ProviderManager.param_aliases.items():
            alias_value = request.GET.get(alias, "").strip()
            if alias_value:
                attribute_search[attr_name] = alias_value

        manager = ProviderModel.objects
        if query_string or attribute_search:
            return manager.search(
                query_string=query_string,
                attribute_search=attribute_search if attribute_search else None,
            )
        return manager.get_queryset()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def config_prefix_display(self, obj):
        """Display config prefix as warning labels."""
        if not obj or not obj.config_prefix:
            return "-"
        html = self.format_label(obj.config_prefix, label_type="info")
        return self.format_with_help_text(html, _("Configuration prefix"))

    config_prefix_display.short_description = _("Config prefix")

    def config_keys_display(self, obj):
        """Display config keys as warning labels."""
        if not obj or not obj.config_keys:
            return "-"
        labels = [self.format_label(key, label_type="primary") for key in obj.config_keys]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Configuration keys"))

    config_keys_display.short_description = _("Config keys")

    def config_required_display(self, obj):
        """Display config required as warning labels."""
        if not obj or not obj.config_required:
            html = self.format_label("No required configuration keys", label_type="info")
            return self.format_with_help_text(html, _("No required configuration keys"))
        labels = [self.format_label(key, label_type="warning") for key in obj.config_required]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Required configuration keys"))

    config_required_display.short_description = _("Config required")
    config_required_display.help_text = _("Required configuration keys")

    def missing_config_keys_display(self, obj):
        """Display missing config keys as warning labels."""
        if not obj or not obj.missing_config_keys:
            html = self.format_label("All configuration keys are present", label_type="success")
            return self.format_with_help_text(html, _("All configuration keys are present"))
        labels = [self.format_label(key, label_type="danger") for key in obj.missing_config_keys]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Missing configuration keys"))

    missing_config_keys_display.short_description = _("Missing config keys")

    def required_packages_display(self, obj):
        """Display required packages as warning labels."""
        if not obj or not obj.required_packages:
            html = self.format_label("No required packages", label_type="info")
            return self.format_with_help_text(html, _("No required packages"))
        labels = [
            self.format_label(package, label_type="primary") for package in obj.required_packages
        ]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Required packages"))

    required_packages_display.short_description = _("Required packages")

    def missing_packages_display(self, obj):
        """Display missing packages as warning labels."""
        if not obj or not obj.missing_packages:
            html = self.format_label("All packages are installed", label_type="success")
            return self.format_with_help_text(html, _("All packages are installed"))
        labels = [self.format_status(key, status=False) for key in obj.missing_packages]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Missing packages"))

    missing_packages_display.short_description = _("Missing packages")

    def services_display(self, obj):
        """Display services as warning labels."""
        if not obj or not obj.services:
            html = self.format_label("All services are implemented", label_type="success")
            return self.format_with_help_text(html, _("All services are implemented"))
        labels = [self.format_label(service, label_type="primary") for service in obj.services]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Services"))

    services_display.short_description = _("Services")

    def missing_services_display(self, obj):
        """Display missing services as warning labels."""
        if not obj or not obj.missing_services:
            html = self.format_label("All services are implemented", label_type="success")
            return self.format_with_help_text(html, _("All services are implemented"))
        labels = [
            self.format_label(service, label_type="danger") for service in obj.missing_services
        ]
        html = mark_safe(" ".join(labels))
        return self.format_with_help_text(html, _("Missing services"))

    missing_services_display.short_description = _("Missing services")

    def has_search_addresses(self, obj):
        """Check if search_addresses service is implemented."""
        if not obj or not obj.services:
            return False
        if "search_addresses" not in obj.services:
            return False
        missing = obj.missing_services or []
        return "search_addresses" not in missing

    has_search_addresses.short_description = _("Search addresses")
    has_search_addresses.boolean = True

    def has_addresses_autocomplete(self, obj):
        """Check if addresses_autocomplete service is implemented."""
        if not obj or not obj.services:
            return False
        if "addresses_autocomplete" not in obj.services:
            return False
        missing = obj.missing_services or []
        return "addresses_autocomplete" not in missing

    has_addresses_autocomplete.short_description = _("Autocomplete")
    has_addresses_autocomplete.boolean = True

    def has_reverse_geocode(self, obj):
        """Check if reverse_geocode service is implemented."""
        if not obj or not obj.services:
            return False
        if "reverse_geocode" not in obj.services:
            return False
        missing = obj.missing_services or []
        return "reverse_geocode" not in missing

    has_reverse_geocode.short_description = _("Reverse geocode")
    has_reverse_geocode.boolean = True

    def cost_search_addresses(self, obj: ProviderModel | None) -> str:
        """Display cost for search_addresses service.
        
        Args:
            obj: ProviderModel instance
            
        Returns:
            Cost string or "-" if free/not available
        """
        if not obj:
            return "-"
        cost = getattr(obj, "cost_search_addresses", None)
        if cost is None or cost == 0 or cost == "free":
            return "-"
        return f"${cost:.5f}"

    cost_search_addresses.short_description = _("Cost (search)")

    def cost_addresses_autocomplete(self, obj: ProviderModel | None) -> str:
        """Display cost for addresses_autocomplete service.
        
        Args:
            obj: ProviderModel instance
            
        Returns:
            Cost string or "-" if free/not available
        """
        if not obj:
            return "-"
        cost = getattr(obj, "cost_addresses_autocomplete", None)
        if cost is None or cost == 0 or cost == "free":
            return "-"
        return f"${cost:.5f}"

    cost_addresses_autocomplete.short_description = _("Cost (autocomplete)")

    def cost_reverse_geocode(self, obj: ProviderModel | None) -> str:
        """Display cost for reverse_geocode service.
        
        Args:
            obj: ProviderModel instance
            
        Returns:
            Cost string or "-" if free/not available
        """
        if not obj:
            return "-"
        cost = getattr(obj, "cost_reverse_geocode", None)
        if cost is None or cost == 0 or cost == "free":
            return "-"
        return f"${cost:.5f}"

    cost_reverse_geocode.short_description = _("Cost (reverse)")
