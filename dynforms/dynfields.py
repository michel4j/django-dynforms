from collections import OrderedDict
from datetime import datetime, timedelta

from dateutil import parser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from dynforms.fields import FieldType
from dynforms.utils import Crypt


# Standard Fields
class StandardMixin(object):
    section = _("Standard")


class SingleLineText(StandardMixin, FieldType):
    name = _("Single Line")
    icon = "forms"
    options = ['hide', 'required', 'repeat', 'floating', 'no-label']
    units = ['chars', 'words']
    settings = ['minimum', 'maximum', 'units', 'default']

    def clean(self, val, multi=False, validate=True):
        val = super().clean(val, multi=multi, validate=validate)
        if isinstance(val, str):
            val = val.strip()
        return val


class ParagraphText(SingleLineText):
    name = _("Paragraph")
    icon = "paragraph"
    options = ['hide', 'required', 'repeat', 'counter']
    settings = ['size', 'minimum', 'maximum', 'units', 'default']


class RichText(ParagraphText):
    name = _("Rich Text")
    icon = "rich-text"
    options = ['hide', 'required', 'counter']
    settings = ['size', 'minimum', 'maximum', 'units']


class MultipleChoice(StandardMixin, FieldType):
    name = _("Choices")
    icon = "check-circle"
    options = ['required', 'randomize', 'inline', 'hide', 'other', 'no-label']
    settings = ['choices']
    choices_type = 'radio'


class ScoreChoices(StandardMixin, FieldType):
    name = _("Scores")
    icon = "check-circle"
    options = ['required', 'inline', 'hide']
    settings = ['choices']
    choices_type = 'radio'

    def coerce(self, value):
        try:
            val = int(value)
        except (TypeError, ValueError):
            val = 0
        return val


class Number(SingleLineText):
    name = _("Number")
    icon = "number-4"
    units = ['digits', 'value']
    settings = ['minimum', 'maximum', 'units', 'default']

    def coerce(self, value):
        try:
            val = int(value)
        except (TypeError, ValueError):
            val = 0
        return val


class Range(Number):
    name = _("Range")
    icon = "range"
    options = ['required', 'hide', 'repeat']
    settings = ['minimum', 'maximum', 'units', 'default']


class CheckBoxes(StandardMixin, FieldType):
    name = _("Checkboxes")
    icon = "check-square"
    options = ['required', 'randomize', 'inline', 'switch', 'hide', 'other', 'no-label']
    settings = ['choices']
    choices_type = 'checkbox'
    multi_valued = True


class DropDown(MultipleChoice):
    name = _("Dropdown")
    icon = "dropdown"
    options = ['required', 'randomize', 'inline', 'hide', 'multiple']
    settings = ['choices']


class PhoneNumber(SingleLineText):
    name = _("Phone #")
    icon = "phone"
    settings = []


class Date(SingleLineText):
    name = _("Date")
    icon = "calendar"
    settings = []


class Time(SingleLineText):
    name = _("Time")
    icon = "clock"
    settings = []
    options = ['hide', 'required', 'repeat', 'no-label']


class Email(SingleLineText):
    name = _("Email")
    icon = "mail"
    units = ['chars']
    settings = ['default']


class NewSection(StandardMixin, FieldType):
    input_type = None
    name = _("Section")
    icon = "section"
    options = ['hide', 'no-label']
    settings = []


class File(StandardMixin, FieldType):
    name = _("File")
    icon = "file"
    options = ['required', 'hide', 'repeat']
    settings = []


class WebsiteURL(StandardMixin, FieldType):
    name = _("URL")
    icon = "link"
    options = ['required', 'hide', 'repeat']
    settings = ['default']


# Fancy Fields
class FancyMixin(StandardMixin):
    section = _("Fancy")


class FullName(FancyMixin, FieldType):
    name = _("Full Name")
    icon = "user"
    options = ['required', 'hide', 'repeat', 'labels', 'floating', 'no-label']
    settings = []
    required_subfields = ['first_name', 'last_name']


class Address(FullName):
    name = _("Address")
    icon = "address"
    options = ['required', 'hide', 'department', 'labels', 'floating']
    settings = []
    required_subfields = ['street', 'city', 'region', 'country', 'code']

    def clean(self, val, multi=False, validate=True):
        val = super().clean(val, multi=multi, validate=validate)

        if validate:
            invalid_fields = set()
            if isinstance(val, list):
                for entry in val:
                    invalid_fields |= {k for k, v in list(self.check_entry(entry).items()) if not v}
            else:
                invalid_fields |= {k for k, v in list(self.check_entry(val).items()) if not v}

            if invalid_fields:
                raise ValidationError("Must complete {}".format(', '.join(invalid_fields)))
        return val


class MultiplePhoneNumber(FancyMixin, FieldType):
    name = _("Phone #s")
    icon = "phone"
    options = ['required', 'hide', 'repeat']
    settings = []


class Equipment(FancyMixin, FieldType):
    name = _("Equipment")
    icon = "plug"
    options = ['required', 'hide', 'repeat']
    settings = []


class ContactInfo(FullName):
    name = _("Contact")
    icon = "id-badge"
    options = ['required', 'hide', 'repeat']
    settings = []
    required_subfields = ['email', 'phone']


class NameAffiliation(FullName):
    name = _("Name/Affiliation")
    icon = "id-badge"
    options = ['required', 'hide', 'repeat']
    settings = []
    required_subfields = ['first_name', 'last_name', 'affiliation']


class NameEmail(FullName):
    name = _("Name/Email")
    icon = "id-badge"
    options = ['required', 'hide', 'repeat']
    settings = []
    required_subfields = ['first_name', 'last_name', 'email']

    def clean(self, val, multi=False, validate=True):
        val = super().clean(val, multi=multi, validate=validate)
        invalid_fields = set()
        if isinstance(val, list):
            entries = OrderedDict()
            for entry in val:
                key = "{}{}{}".format(
                    entry.get('first_name', '').strip(),
                    entry.get('last_name', '').strip(),
                    entry.get('email', '').strip()
                )
                entries[key.lower()] = entry
                invalid_fields |= {k for k, v in list(self.check_entry(entry).items()) if not v}
            val = list(entries.values())
        else:
            invalid_fields |= {k for k, v in list(self.check_entry(val).items()) if not v}

        if validate and invalid_fields:
            raise ValidationError("Must provide {} for all entries".format(', '.join(invalid_fields)))

        return val


class Likert(FancyMixin, FieldType):
    name = _("Likert")
    icon = "list-details"
    options = ['required', 'hide']
    settings = ['choices']


class Throttle(FancyMixin, FieldType):
    name = _("Throttle")
    icon = "stoplights"
    options = ['hide']
    settings = []

    def clean(self, value, validate=True, multi=False):
        if isinstance(value, list):
            value = value[0]

        start = datetime.now() - timedelta(seconds=20)
        try:
            message = Crypt.decrypt(value)
        except ValueError:
            if validate:
                raise ValidationError('Something funny happened with the form. Reload the page and start again.')
        else:
            start = parser.parse(message)
        now = datetime.now()
        if (now - start).total_seconds() < 10:
            raise ValidationError('Did you take the time to read the questions?')

        return value
