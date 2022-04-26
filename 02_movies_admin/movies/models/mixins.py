"""Mixin classes."""

import uuid

from django.db import models


class TimeStampedMixin(models.Model):
    """TimeStampedMixin class."""

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta(object):
        """Meta class."""

        abstract = True


class UUIDMixin(models.Model):
    """UUIDMixin class."""

    id = models.UUIDField(
             primary_key=True,
             default=uuid.uuid4,
             editable=False,
         )

    class Meta(object):
        """Meta class."""

        abstract = True
