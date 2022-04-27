# -*- coding: utf-8 -*-
#
# @created: 10.04.2022
# @author: Aleksey Komissarov
# @contact: ad3002@gmail.com
"""Admin settings for movies app."""

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from .models.models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """GenreAdmin class."""


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """PersonAdmin class."""

    search_fields = ["full_name"]


class GenreFilmworkInline(admin.TabularInline):
    """GenreFilmworkInline class."""

    model = GenreFilmwork

    verbose_name_plural = _("genres")


class PersonFilmworkInline(admin.TabularInline):
    """PersonFilmworkInline class."""

    model = PersonFilmwork

    autocomplete_fields = ["person"]

    verbose_name_plural = _("persons")

    list_prefetch_related = (Prefetch('film_work'), Prefetch('person'))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    """FilmworkAdmin class."""

    list_prefetch_related = (Prefetch('genres'), Prefetch('persons'))

    inlines = (GenreFilmworkInline, PersonFilmworkInline)

    list_display = ("title", "film_type", "creation_date", "rating")

    list_filter = ("film_type", "genres")

    search_fields = ("title", "description", "id")

    filter_horizontal = ("persons", "persons")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            *self.list_prefetch_related
        ).all()
