"""Views for tests.app."""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import LocationForm
from .models import Location


class LocationListView(ListView):
    """List view for Location model."""

    model = Location
    template_name = "app/location_list.html"
    context_object_name = "locations"
    paginate_by = 10


class LocationDetailView(DetailView):
    """Detail view for Location model."""

    model = Location
    template_name = "app/location_detail.html"
    context_object_name = "location"


class LocationCreateView(CreateView):
    """Create view for Location model."""

    model = Location
    form_class = LocationForm
    template_name = "app/location_form.html"
    success_url = reverse_lazy("app:location_list")

    def form_valid(self, form):
        """Handle valid form submission."""
        messages.success(self.request, "Location created successfully!")
        return super().form_valid(form)


class LocationUpdateView(UpdateView):
    """Update view for Location model."""

    model = Location
    form_class = LocationForm
    template_name = "app/location_form.html"
    success_url = reverse_lazy("app:location_list")

    def form_valid(self, form):
        """Handle valid form submission."""
        messages.success(self.request, "Location updated successfully!")
        return super().form_valid(form)


class LocationDeleteView(DeleteView):
    """Delete view for Location model."""

    model = Location
    template_name = "app/location_confirm_delete.html"
    success_url = reverse_lazy("app:location_list")

    def delete(self, request, *args, **kwargs):
        """Handle deletion."""
        messages.success(self.request, "Location deleted successfully!")
        return super().delete(request, *args, **kwargs)
