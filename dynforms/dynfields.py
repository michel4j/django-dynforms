from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Callable

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


class ParagraphText(SingleLineText):
    name = _("Paragraph")
    icon = "paragraph"
    options = ['hide', 'required', 'counter']
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
    settings = ['scores']
    choices_type = 'radio'

    def clean(self, value):
        return int(value)


class Number(SingleLineText):
    name = _("Number")
    icon = "number-4"
    units = ['digits', 'value']
    settings = ['minimum', 'maximum', 'units', 'default']

    def clean(self, value):
        return int(value)


class Progress(FieldType):
    hidden = True
    name = _("Form Progress")
    settings = []
    options = []
    multi_valued = False

    @staticmethod
    def clean_total(value: Any) -> Any:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def clean_required(value: Any) -> Any:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


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

    def is_multi_valued(self, subfield: str = None) -> bool:
        return True


class DropDown(MultipleChoice):
    name = _("Dropdown")
    icon = "dropdown"
    options = ['required', 'randomize', 'inline', 'hide', 'multiple', 'repeat']
    settings = ['choices']


class PhoneNumber(SingleLineText):
    name = _("Phone #")
    icon = "phone"
    settings = []


class Date(SingleLineText):
    name = _("Date")
    icon = "calendar"
    settings = []
    options = ['hide', 'required', 'list', 'floating', 'no-label']


class Time(SingleLineText):
    name = _("Time")
    icon = "clock"
    settings = []
    options = ['hide', 'required', 'no-label']


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

    @staticmethod
    def clean_subfield(value, name, required=True):
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, list) and len(value) == 1:
            value = value[0].strip()
        if not value and required:
            raise ValidationError(_(f"{name} is required."))
        return value

    def clean_first_name(self, value):
        return self.clean_subfield(value, _("First Name"), required=True)

    def clean_last_name(self, value):
        return self.clean_subfield(value, _("Last Name"), required=True)

    def clean_other_names(self, value):
        return self.clean_subfield(value, _("Other Names"), required=False)


class Address(FullName):
    name = _("Address")
    icon = "address"
    options = ['required', 'hide', 'department', 'labels', 'floating']
    settings = []
    required_subfields = ['street', 'city', 'region', 'country', 'code']

    def clean_department(self, value):
        return self.clean_subfield(value, _("Department"), required=False)

    def clean_street(self, value):
        return self.clean_subfield(value, _("Street"), required=True)

    def clean_city(self, value):
        return self.clean_subfield(value, _("City"), required=True)

    def clean_region(self, value):
        return self.clean_subfield(value, _("Region"), required=True)

    def clean_country(self, value):
        return self.clean_subfield(value, _("Country"), required=True)

    def clean_code(self, value):
        return self.clean_subfield(value, _("Postal Code"), required=True)


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


class Likert(FancyMixin, FieldType):
    name = _("Likert")
    icon = "list-details"
    options = ['required', 'hide']
    settings = ['choices', 'scores']
    subfields = ['name', 'value']

    def is_multi_valued(self, subfield: str = None) -> bool:
        if subfield:
            return False
        return True

    @staticmethod
    def clean_name(value):
        if isinstance(value, list) and len(value) == 1:
            return str(value[0].strip())
        elif isinstance(value, str):
            return str(value.strip())
        return ''

    @staticmethod
    def clean_value(value):
        if isinstance(value, list) and len(value) == 1:
            try:
                value = int(value[0])
            except (ValueError, TypeError):
                value = None
        elif isinstance(value, str):
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = None
        elif not isinstance(value, int):
            value = None
        return value

    def clean(self, value):
        if isinstance(value, list):
            return [v for v in value if 'name' in v and 'value' in v and v['value'] is not None]
        else:
            return []


class Throttle(FancyMixin, FieldType):
    name = _("Throttle")
    icon = "stoplights"
    options = ['hide']
    settings = []

    def clean(self, value):
        if isinstance(value, list):
            value = value[0]

        start = datetime.now() - timedelta(seconds=20)
        try:
            message = Crypt.decrypt(value)
        except ValueError:
            raise ValidationError('Something funny happened with the form. Reload the page and start again.')
        else:
            start = parser.parse(message)
        now = datetime.now()
        if (now - start).total_seconds() < 10:
            raise ValidationError('Did you take the time to read the questions?')

        return value
