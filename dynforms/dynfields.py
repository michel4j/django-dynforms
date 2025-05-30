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
    template_theme = "dynforms/fields"


class SingleLineText(FieldType, StandardMixin):
    name = _("Single Line")
    icon = "forms"
    options = ['hide', 'required', 'unique', 'repeat']
    units = ['chars', 'words']
    settings = ['label', 'width', 'options', 'minimum', 'maximum', 'units', 'default']

    def clean(self, val, multi=False, validate=True):
        val = super().clean(val, multi=multi, validate=validate)
        if isinstance(val, str):
            val = val.strip()
        return val


class ParagraphText(SingleLineText):
    name = _("Paragraph")
    icon = "paragraph"
    options = ['hide', 'required', 'unique', 'repeat', 'counter']
    settings = ['label', 'size', 'options', 'minimum', 'maximum', 'units', 'default']


class RichText(ParagraphText):
    name = _("Rich Text")
    icon = "rich-text"
    settings = ['label', 'size', 'options', 'minimum', 'maximum', 'units', 'default']


class MultipleChoice(FieldType, StandardMixin):
    name = _("Choices")
    icon = "check-circle"
    options = ['required', 'randomize', 'inline', 'hide', 'other']
    settings = ['label', 'options', 'choices']
    choices_type = 'radio'


class ScoreChoices(FieldType, StandardMixin):
    name = _("Scores")
    icon = "check-circle"
    options = ['required', 'inline', 'hide']
    settings = ['label', 'options', 'choices']
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
    settings = ['label', 'width', 'options', 'minimum', 'maximum', 'units', 'default']

    def coerce(self, value):
        try:
            val = int(value)
        except (TypeError, ValueError):
            val = 0
        return val


class CheckBoxes(FieldType, StandardMixin):
    name = _("Checkboxes")
    icon = "check-square"
    options = ['required', 'randomize', 'inline', 'hide', 'other']
    settings = ['label', 'options', 'choices']
    choices_type = 'checkbox'
    multi_valued = True


class DropDown(MultipleChoice):
    name = _("Dropdown")
    icon = "dropdown"
    options = ['required', 'randomize', 'inline', 'hide', 'multiple']
    settings = ['label', 'options', 'width', 'choices']


class NewSection(FieldType, StandardMixin):
    input_type = None
    name = _("Section")
    icon = "section"
    options = ['hide', 'nolabel']
    settings = ['label', 'options']


# Fancy Fields
class FancyMixin(object):
    section = _("Fancy")
    template_theme = "dynforms/fields"


class FullName(FieldType, FancyMixin):
    name = _("Full Name")
    icon = "user"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]
    required_subfields = ['first_name', 'last_name']


class Address(FullName):
    name = _("Address")
    icon = "address"
    options = ['required', 'hide', 'department', 'labels']
    settings = ['label', 'options', ]
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


class MultiplePhoneNumber(FieldType, FancyMixin):
    name = _("Phone #s")
    icon = "phone"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]


class Equipment(FieldType, FancyMixin):
    name = _("Equipment")
    icon = "plug"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options']


class ContactInfo(FullName):
    name = _("Contact")
    icon = "person-vcard"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]
    required_subfields = ['email', 'phone']


class NameAffiliation(FullName):
    name = _("Name/Affiliation")
    icon = "id-badge"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]
    required_subfields = ['first_name', 'last_name', 'affiliation']


class NameEmail(FullName):
    name = _("Name/Email")
    icon = "id-badge"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]
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


class Email(FieldType, FancyMixin):
    name = _("Email")
    icon = "email"
    options = ['required', 'unique', 'hide', 'repeat']
    units = ['chars']
    settings = ['label', 'width', 'options', 'minimum', 'maximum', 'units', 'default']


class Date(FieldType, FancyMixin):
    name = _("Date")
    icon = "calendar"
    options = ['required', 'unique', 'hide', 'multiple']
    settings = ['label', 'options']


class DatePreference(FieldType, FancyMixin):
    name = _("Date Preferences")
    icon = "calendar-heart"
    options = ['required', 'unique', 'hide', 'multiple']
    settings = ['label', 'options']


class Time(FieldType, FancyMixin):
    name = _("Time")
    icon = "clock"
    settings = ['label']


class WebsiteURL(FieldType, FancyMixin):
    name = _("URL")
    icon = "link"
    options = ['required', 'unique', 'hide', 'repeat']
    units = ['chars', 'words']
    settings = ['label', 'width', 'options', 'minimum', 'maximum', 'units', 'default']


class Likert(FieldType, FancyMixin):
    name = _("Likert")
    icon = "list-details"
    options = ['required', 'hide']
    settings = ['label', 'options', 'choices']

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


class File(FieldType, FancyMixin):
    name = _("File")
    icon = "file"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'options', ]


class PhoneNumber(FieldType, FancyMixin):
    name = _("Phone #")
    icon = "phone"
    options = ['required', 'hide', 'repeat']
    settings = ['label', 'width', 'options', ]


class Throttle(FieldType, FancyMixin):
    name = _("Throttle")
    icon = "stoplights"
    options = ['hide']
    settings = ['label', 'options']

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
