from typing import Literal

from django.forms import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.db.models import TextChoices
from django import template

DEFAULT_SETTINGS = {
    "instructions": "",
    "size": "medium",
    "width": "full",
    "options": [],
    "choices": ["First Choice", "Second Choice"],
    "default_choices": [],
}


class FieldTypeMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.key = slugify(cls.__name__)
        if not hasattr(cls, 'plugins'):
            cls.plugins = {}
        else:
            cls.plugins[cls.key] = cls

    def get_all(self, *args, **kwargs):
        info = {}
        for p in list(self.plugins.values()):
            section = getattr(p, 'section', _("Custom"))
            if section not in info:
                info[section] = []
            info[section].append(p(*args, **kwargs))
        return info

    def get_type(self, key):
        ft = self.plugins.get(key, None)
        if ft is not None:
            return ft()
        return None


OPTION_INFO = {
    'chars': _('Characters'),
    'words': _('Words'),
    'value': _('Value'),
    'digits': _('Digits'),
    'required': _('Required'),
    'randomize': _('Randomize'),
    'hide': _('Hide'),
    'inline': _('Inline'),
    'other': _('Other'),
    'labels': _('Sub-Labels'),
    'counter': _('Counter'),
    'switch': _('Switch'),
    'floating': _('Floating Label'),
    'repeat': _('Repeatable'),
    'no-label': _('No Label'),
}

OPTION_TYPE = Literal[
    'required', 'randomize', 'hide', 'inline', 'other', 'counter', 'switch', 'floating', 'repeat', 'no-label'
]

SETTING_TYPE = Literal['size', 'choices', 'minimum', 'maximum', 'units', 'default']
SIZE_TYPE = Literal['medium', 'small', 'large']
UNITS_TYPE = Literal['chars', 'words', 'value', 'digits']


def build_choices(name, pars) -> TextChoices:
    """
    A factory function to create a TextChoices class for field options.
    """
    opts = {}
    for k in pars:
        if isinstance(k, str):
            v = OPTION_INFO.get(k, k.capitalize())
            opts[k.upper()] = (k, v)
    return TextChoices(name, opts)


def value_to_list(value) -> list:
    """
    Re-map a value to a list.
    """
    if isinstance(value, dict):
        try:
            new_value = {
                int(k): v
                for k, v in list(value.items())
            }
        except ValueError:
            out_value = [x[1] for x in sorted(value.items())]
        else:
            out_value = [x[1] for x in sorted(new_value.items())]
        return out_value
    elif hasattr(value, '__getitem__') and not isinstance(value, str):
        return value
    else:
        return []


class SizeType(TextChoices):
    MEDIUM = 'medium', _('Medium')
    SMALL = 'small', _('Small')
    LARGE = 'large', _('Large')


class LayoutType(TextChoices):
    FULL = ('full', _('Full'))
    HALF = ('half', _('Half'))
    THIRD = ('third', _('Third'))
    QUARTER = ('quarter', _('Quarter'))
    TWO_THIRDS = ('two_thirds', _('Two Thirds'))
    THREE_QUARTERS = ('three_quarters', _('Three Quarters'))


class UnitType(TextChoices):
    CHARS = ('chars', _('Characters'))
    WORDS = ('words', _('Words'))
    VALUE = ('value', _('Value'))


class FieldType(object, metaclass=FieldTypeMeta):
    template_theme = "dynforms/fields"
    template_name = ""
    section = _("Custom")
    name = _("Noname Field")
    icon = "bi-input-cursor"
    multi_valued = False
    sizes: list[str] = ["medium", "small", "large"]
    units: list[UNITS_TYPE] = []
    options: list[OPTION_TYPE] = ["required", "hide", "repeat"]
    choices_type: str = 'checkbox'  # 'radio'
    settings: list[SETTING_TYPE] = []
    required_subfields: list[str] = []

    @classmethod
    def get_template_name(cls):
        """
        Returns the template name for the field type.
        """
        if cls.template_name:
            return cls.template_name
        else:
            return f"{cls.template_theme}/{slugify(cls.__name__)}.html"

    @classmethod
    def render(cls, context):
        """
        Render the field type template with the given context.
        :param context: The context to render the template with.
        :return: Rendered template as a string.
        """
        templates = [
            cls.get_template_name(),
            "dynforms/fields/no-field.html"
        ]
        tmpl = template.loader.select_template(templates)
        return tmpl.render(context)

    def check_entry(self, row):
        if not isinstance(row, dict):
            return {}
        validity = {
            key: bool(row.get(key, '')) for key in self.required_subfields
        }
        return validity

    def get_completeness(self, data) -> float:
        """
        Calculate the completeness of the field based on the provided data.
        """
        if not data:
            return 0.0
        elif len(self.required_subfields) == 0:
            return 1.0
        else:
            invalid_fields = []
            if isinstance(data, list):
                for entry in data:
                    invalid_fields += [k for k, v in list(self.check_entry(entry).items()) if not v]
                total = len(data) * len(self.required_subfields)
            else:
                invalid_fields += [k for k, v in list(self.check_entry(data).items()) if not v]
                total = len(self.required_subfields)
            return 1.0 if total == 0 else (1.0 - len(invalid_fields) / float(total))

    def coerce(self, val):
        """
        Coerce value to a valid type
        """
        if isinstance(val, dict):
            clean_val = {k: v[0] for k, v in list(val.items()) if isinstance(v, list)}
            val.update(clean_val)
            val = {k: v for k, v in list(val.items()) if v}
        return val

    def clean(self, val, multi=False, validate=False):
        """
        Parse and Validate field and return clean value
        """
        try:
            if isinstance(val, dict) and (multi or self.multi_valued):
                val = list(map(dict, zip(*[[(k, v) for v in value] for k, value in val.items()])))
            elif not isinstance(val, list):
                val = [val]
            val = list(map(self.coerce, val))
        except ValueError:
            if validate:
                raise ValidationError(_('Invalid value: %(value)s'), code='invalid', params={'value': val}, )
            return None
        else:
            if not (multi or self.multi_valued) and val:
                return val[0]
            else:
                return [v for v in val if v]

    def get_default(self, page=None, pos=None):
        """
        Generate a default field specification for this field type.
        """
        pos = 0 if pos is None else pos
        page = 0 if page is None else page
        tag = f"{100 * page + pos:03d}"
        field = {
            "field_type": self.key,
            "label": f"{self.name} {tag}",
            "name": slugify(f"{self.name}_{tag}").lower().replace("-", "_"),
        }
        for k in self.settings:
            if k in DEFAULT_SETTINGS:
                if k == "choices":
                    field[k] = DEFAULT_SETTINGS[k]
                    field['default_choices'] = DEFAULT_SETTINGS["default_choices"]
                else:
                    field[k] = DEFAULT_SETTINGS[k]
        return field

    def option_choices(self):
        return build_choices('OptionType', self.options)

    def size_choices(self):
        return build_choices('SizeType', self.sizes)

    def units_choices(self):
        return build_choices('UnitType', self.units)

    def get_choices(self, field_name):
        return {
            'options': build_choices(f'{self.__class__.__name__}Option', self.options),
            'size': SizeType,
            'width': LayoutType,
            'units': build_choices(f'{self.__class__.__name__}Unit', self.units)
        }.get(field_name, [])


