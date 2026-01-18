"""Address suggestion model for geoaddress."""

from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _
from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS
from virtualqueryset.models import VirtualModel

from djgeoaddress import fields_associations
from djgeoaddress.managers.suggest import AddressManager

FIELDS_GEOADDRESS = GEOADDRESS_FIELDS_DESCRIPTIONS

geoaddress_id_config: dict[str, Any] = FIELDS_GEOADDRESS['geoaddress_id']


class BaseAddressModel(VirtualModel):
    """Virtual model for address suggestions from geoaddress."""

    geoaddress_id: models.CharField = models.CharField(
        max_length=500,
        verbose_name=geoaddress_id_config['label'],
        help_text=geoaddress_id_config['description'],
        primary_key=True,
    )

    objects = AddressManager()

    class Meta:
        managed = False
        abstract = True
        verbose_name = _('Address Suggestion')
        verbose_name_plural = _('Address Suggestions')

    def __str__(self) -> str:
        text = getattr(self, 'text', None)
        geoaddress_id = getattr(self, 'geoaddress_id', None)
        if text:
            return str(text)
        return f"Address {geoaddress_id or 'unknown'}"


for field, value in FIELDS_GEOADDRESS.items():
    if field == 'geoaddress_id':
        continue

    db_field = fields_associations[value['format']](
        verbose_name=value['label'], help_text=value['description']
    )

    if value['format'] in ('str', 'text'):
        db_field.blank = True
        if value['format'] == 'text':
            db_field.max_length = None
        elif 'reference' in field or 'id' in field:
            db_field.max_length = 255
        else:
            db_field.max_length = 500
    elif value['format'] == 'float':
        db_field.null = True
        db_field.blank = True

    BaseAddressModel.add_to_class(field, db_field)


class AddressModel(BaseAddressModel):
    """Model for geoaddress addresses."""

    class Meta:
        managed = False
        verbose_name = _('Geoaddress Address')
        verbose_name_plural = _('Geoaddress Addresses')
