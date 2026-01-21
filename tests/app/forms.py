"""Forms for tests.app."""

from django import forms

from .models import Location


class LocationForm(forms.ModelForm):
    """Form for Location model."""

    class Meta:
        model = Location
        fields = ["name", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter location name"}),
        }
