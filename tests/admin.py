"""Admin for test models."""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgeoaddress.models import AddressBackendInfo, AddressLookup
from .models import TestLocation


class BackendAutocompleteWidget(AutocompleteSelect):
    """Autocomplete widget using Django admin native widget."""
    
    def __init__(self, attrs=None):
        class VirtualRemoteField:
            model = AddressBackendInfo
            name = "backend"
            
            def get_related_field(self):
                class VirtualRelatedField:
                    name = "pk"
                return VirtualRelatedField()
        
        remote_field = VirtualRemoteField()
        remote_field.remote_field = remote_field
        super().__init__(remote_field, admin.site, attrs=attrs)
    
    def optgroups(self, name, value, attrs=None):
        return []
    
    def get_url(self):
        try:
            app_label = AddressBackendInfo._meta.app_label
            model_name = AddressBackendInfo._meta.model_name
            url_name = f"admin:{app_label}_{model_name}_autocomplete"
            return reverse(url_name)
        except Exception:
            try:
                app_label = AddressBackendInfo._meta.app_label
                model_name = AddressBackendInfo._meta.model_name
                return f"/admin/{app_label}/{model_name}/autocomplete/"
            except Exception:
                return "/admin/djgeoaddress/addressbackendinfo/autocomplete/"
    
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if "data-autocomplete-url" not in attrs:
            attrs["data-autocomplete-url"] = self.get_url()
        return attrs
    
    def value_from_datadict(self, data, files, name):
        hidden_name = f"{name}_id"
        value = data.get(hidden_name)
        if value:
            try:
                backend = AddressBackendInfo.objects.get(pk=value)
                return backend.name
            except AddressBackendInfo.DoesNotExist:
                return value
        return value
    
    def format_value(self, value):
        if not value:
            return ""
        try:
            backend = AddressBackendInfo.objects.get(name=value)
            return str(backend.pk)
        except AddressBackendInfo.DoesNotExist:
            return value


class BackendAutocompleteField(forms.CharField):
    """Field with native Django admin autocomplete."""
    
    widget = BackendAutocompleteWidget
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("help_text", "Backend used for geocoding")
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        if value:
            return str(value).strip()
        return ""
    
    def validate(self, value):
        super().validate(value)
        if value:
            try:
                AddressBackendInfo.objects.get(name=value)
            except AddressBackendInfo.DoesNotExist:
                raise forms.ValidationError(
                    _("Backend '%(backend)s' does not exist.") % {"backend": value}
                )


class AddressAutocompleteWithEditWidget(forms.MultiWidget):
    """Widget combining native autocomplete with detailed address editing."""
    
    template_name = "admin/widgets/address_autocomplete_with_edit.html"
    
    def __init__(self, attrs=None):
        from django.utils.translation import gettext_lazy as _
        
        autocomplete_widget = AddressAutocompleteWidget(attrs=attrs)
        address_widgets = [
            forms.TextInput(attrs={"placeholder": _("Address line 1"), "class": "address-line1"}),
            forms.TextInput(attrs={"placeholder": _("Address line 2"), "class": "address-line2"}),
            forms.TextInput(attrs={"placeholder": _("Address line 3"), "class": "address-line3"}),
            forms.TextInput(attrs={"placeholder": _("Postal code"), "class": "address-postal-code"}),
            forms.TextInput(attrs={"placeholder": _("City"), "class": "address-city"}),
            forms.TextInput(attrs={"placeholder": _("State / Region"), "class": "address-state"}),
            forms.TextInput(attrs={"placeholder": _("Country (ISO code)"), "class": "address-country"}),
        ]
        
        widgets = [autocomplete_widget] + address_widgets
        super().__init__(widgets, attrs)
        self._autocomplete_widget = autocomplete_widget
    
    def decompress(self, value):
        if not value:
            return [None, "", "", "", "", "", "", ""]
        if isinstance(value, dict):
            address_parts = [
                value.get("line1") or value.get("address_line1") or "",
                value.get("line2") or value.get("address_line2") or "",
                value.get("line3") or value.get("address_line3") or "",
            ]
            city_parts = [
                value.get("postal_code") or "",
                value.get("city") or "",
            ]
            state_country = [
                value.get("state") or "",
                value.get("country") or "",
            ]
            formatted_address = ", ".join(
                filter(None, address_parts + 
                      [" ".join(filter(None, city_parts))] + 
                      state_country)
            )
            return [
                formatted_address,
                value.get("line1") or value.get("address_line1") or "",
                value.get("line2") or value.get("address_line2") or "",
                value.get("line3") or value.get("address_line3") or "",
                value.get("postal_code") or "",
                value.get("city") or "",
                value.get("state") or "",
                value.get("country") or "",
            ]
        return [value, "", "", "", "", "", "", ""]
    
    def value_from_datadict(self, data, files, name):
        autocomplete_value = self._autocomplete_widget.value_from_datadict(data, files, name)
        if autocomplete_value and isinstance(autocomplete_value, dict) and any(autocomplete_value.values()):
            return autocomplete_value
        
        address_values = [
            data.get(f"{name}_1", ""),
            data.get(f"{name}_2", ""),
            data.get(f"{name}_3", ""),
            data.get(f"{name}_4", ""),
            data.get(f"{name}_5", ""),
            data.get(f"{name}_6", ""),
            data.get(f"{name}_7", ""),
        ]
        
        if not any(address_values):
            return {}
        
        address_dict = {
            "line1": address_values[0],
            "line2": address_values[1],
            "line3": address_values[2],
            "postal_code": address_values[3],
            "city": address_values[4],
            "state": address_values[5],
            "country": address_values[6],
        }
        return {key: value for key, value in address_dict.items() if value}
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["name"] = name
        
        decompressed = self.decompress(value)
        autocomplete_value = decompressed[0] if decompressed else None
        
        if autocomplete_value and isinstance(autocomplete_value, str) and autocomplete_value.strip():
            context["autocomplete_widget_html"] = self._autocomplete_widget.render(name, autocomplete_value, attrs)
        else:
            context["autocomplete_widget_html"] = self._autocomplete_widget.render(name, None, attrs)
        
        for i, subwidget in enumerate(self.widgets[1:], start=1):
            subwidget_value = decompressed[i] if i < len(decompressed) else ""
            subwidget_html = subwidget.render(f"{name}_{i}", subwidget_value, {})
            context["widget"]["subwidgets"][i]["html"] = subwidget_html
        
        return context
    
    class Media:
        js = ("admin/js/address_autocomplete_with_edit.js",)


class AddressAutocompleteWidget(AutocompleteSelect):
    """Native Django admin autocomplete widget for addresses."""
    
    def __init__(self, attrs=None):
        class VirtualRemoteField:
            model = AddressLookup
            name = "address"
            
            def get_related_field(self):
                class VirtualRelatedField:
                    name = "pk"
                return VirtualRelatedField()
        
        remote_field = VirtualRemoteField()
        remote_field.remote_field = remote_field
        super().__init__(remote_field, admin.site, attrs=attrs)
    
    def optgroups(self, name, value, attrs=None):
        if value and isinstance(value, str) and value.strip():
            class Option:
                template_name = "django/forms/widgets/select_option.html"
                def __init__(self, value, label):
                    self.value = value
                    self.label = label
                    self.attrs = {}
            return [(None, [Option(value=value, label=value)], 0)]
        return []
    
    def get_url(self):
        try:
            app_label = AddressLookup._meta.app_label
            model_name = AddressLookup._meta.model_name
            url_name = f"admin:{app_label}_{model_name}_autocomplete"
            return reverse(url_name)
        except Exception:
            try:
                app_label = AddressLookup._meta.app_label
                model_name = AddressLookup._meta.model_name
                return f"/admin/{app_label}/{model_name}/autocomplete/"
            except Exception:
                return "/admin/djgeoaddress/addresslookup/autocomplete/"
    
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if "data-autocomplete-url" not in attrs:
            attrs["data-autocomplete-url"] = self.get_url()
        attrs["data-backend-field"] = "id_backend"
        return attrs
    
    def value_from_datadict(self, data, files, name):
        hidden_name = f"{name}_id"
        slug_value = data.get(hidden_name)
        if slug_value:
            try:
                from django.core.cache import cache
                cache_key = f"geoaddress:addresslookup:{slug_value}"
                cached_data = cache.get(cache_key)
                if cached_data and isinstance(cached_data, dict):
                    payload = cached_data.get("payload", {})
                    normalized = payload.get("normalized_address") or payload
                    return normalized
            except Exception:
                pass
        return {}
    
    def format_value(self, value):
        if not value:
            return ""
        if isinstance(value, dict):
            address_parts = [
                value.get("line1") or value.get("address_line1") or "",
                value.get("line2") or value.get("address_line2") or "",
                value.get("line3") or value.get("address_line3") or "",
            ]
            city_parts = [
                value.get("postal_code") or "",
                value.get("city") or "",
            ]
            state_country = [
                value.get("state") or "",
                value.get("country") or "",
            ]
            formatted_address = ", ".join(
                filter(None, address_parts + 
                      [" ".join(filter(None, city_parts))] + 
                      state_country)
            )
            return formatted_address
        return value


class AddressAutocompleteField(forms.Field):
    """Field with native autocomplete returning address dict."""
    
    widget = AddressAutocompleteWithEditWidget
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("help_text", "Full address with geocoding")
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        if not value:
            return {}
        if isinstance(value, str) and value.strip():
            try:
                from django.core.cache import cache
                cache_key = f"geoaddress:addresslookup:{value}"
                cached_data = cache.get(cache_key)
                if cached_data and isinstance(cached_data, dict):
                    payload = cached_data.get("payload", {})
                    normalized = payload.get("normalized_address") or payload
                    return normalized
            except Exception:
                pass
            return {}
        if isinstance(value, dict):
            return value
        return {}


class TestLocationAdminForm(forms.ModelForm):
    """Form with native autocomplete for backend and address."""
    
    backend = BackendAutocompleteField()
    address = AddressAutocompleteField()
    
    class Meta:
        model = TestLocation
        fields = "__all__"


@admin.register(TestLocation)
class TestLocationAdmin(admin.ModelAdmin):
    """Admin for TestLocation with native autocomplete."""
    
    form = TestLocationAdminForm
    
    list_display = ["name", "backend", "created_at"]
    list_filter = ["created_at", "backend"]
    search_fields = ["name", "notes"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (None, {
            "fields": ("name", "address", "backend", "notes"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
