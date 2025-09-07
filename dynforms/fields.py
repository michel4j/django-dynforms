from typing import Literal, Any

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
    'names': ['first_choice', 'second_choice'],
    "values": ['A', 'B'],
    "scores": [1, 2, 3],
    "rubrics": ["Good", "Average", "Poor"],
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
            if p.hidden:
                continue
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

SETTING_TYPE = Literal['size', 'choices', 'minimum', 'maximum', 'units', 'default', 'max_repeat']
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
    hidden = False
    section = _("Custom")
    name = _("Noname Field")
    icon = "bi-input-cursor"
    multi_valued = []
    sizes: list[str] = ["medium", "small", "large"]
    units: list[UNITS_TYPE] = []
    options: list[OPTION_TYPE] = ["required", "hide", "repeat"]
    choices_type: str = 'checkbox'  # 'radio'
    settings: list[SETTING_TYPE] = []
    required_subfields: list[str] = []
    subfields = {}

    def is_multi_valued(self, subfield: str = None) -> bool:
        """
        Check if the field type is multivalued or if a specific subfield is multivalued.
        :param subfield: Optional subfield name to check.
        :return: True if multivalued, False otherwise.
        """
        return self.multi_valued if isinstance(self.multi_valued, bool) else subfield in self.multi_valued

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

    @classmethod
    def get_field(cls, **specs):
        """
        Factory to Create a FormField instance for this field type.
        """
        from dynforms.utils import FormFieldManager
        return FormFieldManager(**specs)

    def check_entry(self, row) -> dict:
        """
        Check the subfields of an entry.
        :param row: the entry row
        :return: a dictionary mapping the field name to a boolean indicating its presence
        """
        if not isinstance(row, dict):
            return {}
        return {
            key: row.get(key) not in ['', {}, None, []]
            for key in self.required_subfields
        }

    def clean(self, data: Any) -> Any:
        """
        Clean the data for this field type. This is called on a single instance of the field even if it is multi-valued.
        :param data: The data to clean
        :return: Cleaned data.
        """
        return data

    def compress(self, data: Any) -> Any:
        """
        Compress the data for this field type. This is called on a single instance of the field even if it is multi-valued.
        :param data: The data to compress
        :return: Compressed data.
        """
        return data

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
                if k  == "choices":
                    field[k] = DEFAULT_SETTINGS[k]
                    field['default_choices'] = DEFAULT_SETTINGS["default_choices"]
                elif k == "scores":
                    field[k] = DEFAULT_SETTINGS[k]
                    field['rubrics'] = DEFAULT_SETTINGS.get("rubrics", [])
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


