"""Views for tests.app."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import LocationForm
from .models import Location


class LocationChoiceView(TemplateView):
    """View to choose between Django native and REST Framework versions."""

    template_name = "app/choice.html"


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


# Django Native Views
class LocationDjangoListView(ListView):
    """Django native list view for Location model."""

    model = Location
    template_name = "app/django/list.html"
    context_object_name = "locations"
    paginate_by = 10


class LocationDjangoUpdateView(UpdateView):
    """Django native update view for Location model."""

    model = Location
    form_class = LocationForm
    template_name = "app/django/update.html"
    success_url = reverse_lazy("app:location_django_list")

    def form_valid(self, form):
        """Handle valid form submission."""
        messages.success(self.request, "Location updated successfully!")
        return super().form_valid(form)


class LocationDjangoRemoveView(DeleteView):
    """Django native remove view for Location model."""

    model = Location
    template_name = "app/django/remove.html"
    success_url = reverse_lazy("app:location_django_list")

    def delete(self, request, *args, **kwargs):
        """Handle deletion."""
        messages.success(self.request, "Location deleted successfully!")
        return super().delete(request, *args, **kwargs)


# REST Framework Views - Pure JavaScript interface
class LocationRestListView(TemplateView):
    """REST Framework list view - pure JavaScript interface."""

    template_name = "app/rest/list.html"


class LocationRestCreateView(TemplateView):
    """REST Framework create view - pure JavaScript interface."""

    template_name = "app/rest/create.html"


class LocationRestUpdateView(TemplateView):
    """REST Framework update view - pure JavaScript interface."""

    template_name = "app/rest/update.html"

    def get_context_data(self, **kwargs):
        """Add location ID to context."""
        context = super().get_context_data(**kwargs)
        context["location_id"] = kwargs.get("pk")
        return context


class LocationRestRemoveView(TemplateView):
    """REST Framework remove view - pure JavaScript interface."""

    template_name = "app/rest/remove.html"

    def get_context_data(self, **kwargs):
        """Add location ID to context."""
        context = super().get_context_data(**kwargs)
        context["location_id"] = kwargs.get("pk")
        return context
