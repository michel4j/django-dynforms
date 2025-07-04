import re
from collections import defaultdict
from datetime import timedelta
from typing import Any

from django.contrib import messages
from django.db import models
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe

from .fields import FieldType, ValidationError
from .utils import Queryable, build_Q, FormPage, FormField


def default_pages():
    return [
        {"name": "Page 1", "fields": []}
    ]


def default_actions():
    return [
        ('save', 'Save'),
        ('submit', 'Submit'),
    ]


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class FormType(TimeStampedModel):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    header = models.BooleanField(_("Show header"), default=False)
    help_bar = models.BooleanField(_("Show help bar"), default=False)
    wizard = models.BooleanField(_("Wizard Mode"), default=False)

    pages = models.JSONField(default=default_pages, null=True, blank=True)
    actions = models.JSONField(default=default_actions, null=True, blank=True)

    class Meta:
        ordering = ['-modified']

    def add_field(self, page: int, pos: int, field: dict):
        if page < len(self.pages):
            self.pages[page]['fields'].insert(pos, field)
            self.save()

    def update_field(self, page, pos, field):
        if page < len(self.pages) and pos < len(self.pages[page]['fields']):
            self.pages[page]['fields'][pos] = field
            self.save()

    def remove_field(self, page, pos):
        if page < len(self.pages) and pos < len(self.pages[page]['fields']):
            self.pages[page]['fields'].pop(pos)
            self.save()

    def get_field(self, page, pos):
        if page < len(self.pages) and pos < len(self.pages[page]['fields']):
            return self.pages[page]['fields'][pos]
        return None

    def add_page(self, page_title):
        self.pages.append({'name': page_title, 'fields': []})
        self.save()

    def update_pages(self, titles):
        for page, title in enumerate(titles):
            if page < len(self.pages):
                self.pages[page]['name'] = title
            else:
                self.pages.append({'name': title, 'fields': []})
        if len(self.pages) > len(titles) and len(self.pages[-1]['fields']) == 0:
            self.pages.pop()
        self.save()

    def remove_page(self, page: int):
        """
        Remove a page from the form type.
        :param page: The index of the page to remove (1-based).
        """
        pg = page - 1
        if len(self.pages[pg]['fields']) == 0:
            self.pages.pop(pg)
            self.save()
        else:
            raise ValueError(f"Cannot remove page {page} as it contains fields. Please remove fields first.")

    def get_page(self, page):
        if page < len(self.pages):
            return self.pages[page]
        return None

    def page_names(self):
        return [p['name'] for p in self.pages]

    def move_page(self, old_pos, new_pos):
        if old_pos != new_pos and old_pos < len(self.pages):
            pg = self.pages.pop(old_pos)
            self.pages.insert(new_pos, pg)
            self.save()

    def move_field(self, page, old_pos, new_pos, new_page=None):
        if page < len(self.pages) and old_pos < len(self.pages[page]['fields']):
            if new_page is None and (old_pos == new_pos):
                return
            fld = self.pages[page]['fields'].pop(old_pos)
            if new_page is not None and new_page != page:
                page = new_page
            self.pages[page]['fields'].insert(new_pos, fld)
            self.save()

    def clone_field(self, page, pos):
        if page < len(self.pages) and pos < len(self.pages[page]['fields']):
            field = self.pages[page]['fields'][pos]
            new_field = field.copy()
            new_field['name'] += '_copy'
            self.pages[page]['fields'].insert(pos + 1, new_field)
            self.save()
            return new_field
        return None

    def field_specs(self):
        """
        Get a mapping of field names to their specifications.
        """
        return {f['name']: f for p in self.pages for f in p['fields']}

    def field_pages(self):
        """
        Get a mapping of field names to their respective page numbers.
        """
        return {
            f['name']: i + 1 for i, page in enumerate(self.pages) for f in page['fields']
        }

    def check_form(self):
        warnings = []
        exists = set()
        missing = set()
        for i, page in enumerate(self.pages):
            for field in page['fields']:
                print(field['name'])
                if field['name'] in exists:
                    warnings.append(f'Page {i + 1}: Field `{field["name"]}` defined more than once!')
                if field['name'] in missing:
                    missing.remove(field['name'])
                if re.search(r'\.', field['name']):
                    warnings.append(f'Page {i + 1}: Field `{field["name"]}` contains invalid character `.`!')
                if re.search(r'_{2,}', field['name']):
                    warnings.append(
                        f'Page {i + 1}: Field `{field["name"]}` should not have multiple underscores!'
                    )
                exists.add(field['name'])
        if missing:
            warnings.extend([f'Missing field `{f}`' for f in missing])
        return warnings

    def get_pages(self):
        return [FormPage(**page, number=(i + 1)) for i, page in enumerate(self.pages)]

    def clean_data(self, data: Any, validate: bool = False) -> Any:
        """
        Clean the data for the form, ensuring it is in the correct format.
        :param data: The data to clean.
        :param validate: Whether to validate the data.
        :return: The cleaned data.
        """

        cleaned_data = {}
        failures = defaultdict(dict)
        field_pages = self.field_pages()
        if not validate:
            validate = any((name == 'submit' for name, _ in self.actions if name in data))

        for name, label in self.actions:
            if label in data.get(name, []):
                cleaned_data["form_action"] = name

        # active page is a special numeric field, increment if save_continue
        page_field = FieldType.get_field(name='active_page', field_type='number')
        active_page = page_field.clean(data.get('active_page', 1))
        if cleaned_data.get('form_action') == 'save_continue':
            cleaned_data['active_page'] = min(active_page + 1, len(self.pages))
        else:
            cleaned_data['active_page'] = active_page

        # extract field data
        for field_name, field_spec in self.field_specs().items():

            page_no = field_pages.get(field_name, 0)
            field_type = FieldType.get_type(field_spec['field_type'])
            if field_type is None:
                continue

            field = field_type.get_field(**field_spec)

            if field_name in data:
                try:
                    cleaned_value = field.clean(data[field_name])
                except (ValidationError, ValueError, KeyError, AttributeError) as err:
                    failures[page_no][field_name] = str(err)
                    cleaned_value = cleaned_data

                if cleaned_value is not None:
                    cleaned_data[field_name] = cleaned_value

            required = "required" in field_spec.get('options', [])
            if validate and required and not cleaned_data.get(field_name):
                failures[page_no][field_name] = "required"

        # Second loop to check other validations
        query_data = Queryable(cleaned_data)
        for field_name, field_spec in list(self.field_specs().items()):
            page_no = field_pages.get(field_name, 0)
            required_rules = [r for r in field_spec.get('rules', []) if r['action'] == 'require']
            if required_rules:
                required_queryable = build_Q(required_rules)
                if validate and query_data.matches(required_queryable) and not cleaned_data.get(field_name):
                    failures[page_no][field_name] = "required together with another field you have filled."

        return cleaned_data, failures

    def __str__(self):
        return self.name


class BaseFormModel(TimeStampedModel):
    details = models.JSONField(default=dict, null=True, blank=True, editable=False)
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, null=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def get_field_value(self, key, default=None):
        """
        Get the value of a field from the details JSON.
        If the key is not found, return the default value.
        If the key is a dot-separated path, traverse the JSON structure.
        :param key: The key to look for in the details JSON.
        :param default: The default value to return if the key is not found.
        :return: The value of the field or the default value if not found.
        """
        keys = key.split('.')
        if hasattr(self, key) and not callable(getattr(self, key)):
            return getattr(self, key)
        else:
            value = self.details
            for k in keys:
                value = value.get(k, None)
                if not value:
                    return default
            return value

    def validate(self, data=None):
        """
        Validate the form data against the field specifications.
        :param data: The data to validate. If None, use the details of the instance.
        :return: A dictionary with validation results, including progress and any validation errors.
        """
        if data is None:
            data = self.details

        # Do not validate if item has not been modified since creation
        if not all((self.modified, self.created)) or (self.modified - self.created) < timedelta(seconds=1):
            return {}

        cleaned_data, errors = self.form_type.clean_data(data, validate=True)
        return {'pages': dict(errors)}


class DynEntry(BaseFormModel):
    pass
