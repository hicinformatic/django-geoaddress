from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset import InMemoryQuerySet


class AddressLookupQuerySet(InMemoryQuerySet):
    """In-memory queryset for address lookup suggestions."""

    pass


class AddressLookupManager(models.Manager):
    def get_queryset(self):
        return AddressLookupQuerySet(model=self.model, data=[])


class AddressLookup(models.Model):
    label = models.CharField(max_length=512, verbose_name=_("Suggested address"))
    backend_used = models.CharField(
        max_length=64, blank=True, verbose_name=_("Backend used")
    )
    backend_reference = models.CharField(
        max_length=128, blank=True, verbose_name=_("Backend reference")
    )
    raw_payload = models.JSONField(default=dict, blank=True)

    objects = AddressLookupManager()

    class Meta:
        managed = False
        verbose_name = _("Address suggestion")
        verbose_name_plural = _("Address suggestions")
        ordering = ["label"]
        default_permissions = ()

    def __str__(self):
        return self.label or _("Address suggestion")
