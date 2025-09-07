
import random
from itertools import zip_longest

from django import template
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe

from dynforms.fields import FieldType
from dynforms.utils import FormFieldManager, FIELD_SEPARATOR

register = template.Library()


def _get_field_value(context, field):
    field_name = field['name']
    default = field.get('defaults', '')
    form = context.get('form')

    if not form:
        return default

    if form.is_bound:
        data = form.cleaned_data.get('details', {})
        value = data.get(field_name)
        if value is not None:
            return value

    if getattr(form, 'instance', None) and hasattr(form.instance, 'get_field_value') and form.instance.pk:
        value = form.instance.get_field_value(field_name)
        if value is not None:
            return value

    value = form.initial.get(field_name, default)
    return '' if value is None else value


@register.simple_tag(takes_context=True)
def render_field(context, field: FormFieldManager, repeatable: bool = False):
    all_data = field.get_data(context)

    if field.type:
        if field.type.is_multi_valued():
            all_data = [] if all_data == '' else all_data
        field_type = field.type
    else:
        field_type = FieldType

    if not (repeatable and isinstance(all_data, list)):
        all_data = [all_data]

    if repeatable and all_data == []:
        all_data = ['']
    ctx = {
        'repeatable': f" {field.name}-repeatable" if repeatable else '',
        'required': " required" if 'required' in field.get_options() else '',
        'floating': " form-floating" if 'floating' in field.get_options() else '',
        'repeat_name': f'{field.name}{FIELD_SEPARATOR}?' if repeatable else f'{field.name}',
    }
    ctx.update(context.flatten())

    rendered = ""
    choices = field.get_choices()
    options = field.get_options()
    for i, data in enumerate(all_data):
        if choices and "other" in options and isinstance(data, list):
            oc_set = set(data) - set(choices)
            if oc_set:
                field.set_attr('other_choice', next(iter(oc_set)))
        repeat_index = i if repeatable else ""

        ctx.update({
            'field': field.specs(repeatable=repeatable, index=i),
            'data': data, 'repeat_index': repeat_index
        })
        rendered += field_type.render(ctx)
    return mark_safe(rendered)


@register.simple_tag(takes_context=True)
def subfield_require(context, field_name: str) -> str:
    """
    Returns whether a subfield is required based on the field's options and the field type
    :param context: The template context.
    :param field_name: The name of the field to check.
    :return: 'required' if the subfield is required, otherwise an empty string.
    """
    field_specs = context.get('field')
    if not field_specs:
        return ''
    field_type = field_specs.get('type')
    if not field_type:
        return ''

    if field_type and 'required' in field_specs.get('options', []) and field_name in field_type.required_subfields:
        return 'required'
    return ''


@register.filter
def group_choices(field, defaults):

    if not defaults:
        defaults = field.get('default', [])
    choices = field.get('choices', [])
    values = field.get('values', choices)
    return [{
        'label': choice,
        'value': choice,
        'selected': (choice in defaults) or (value in defaults),
    } for choice, value in zip(choices, values)]


@register.filter
def likert_choices(field, data):
    if not data:
        data = field.get('default', [])

    defaults = {item.get('name', ''): item.get('value') for item in data}
    choices = field.get('choices', [])

    return [{
        'name': name,
        'index': i,
        'value': defaults.get(name),
    } for i, name in enumerate(choices)]


@register.filter
def likert_scores(field):

    scores = field.get('scores', [])
    rubrics = field.get('rubrics', [])
    return [{
        'value': int(score),
        'rubric': rubric,
    } for score, rubric in zip(scores, rubrics)]


@register.filter
def show_sublabels(field):
    """
    Returns whether the field should show sublabels based on its options.
    :param field: The field dictionary which contains options.
    :return: True if 'sublabels' is in options, otherwise False.
    """
    return bool({'labels', 'floating'} & set(field.get('options', [])))


@register.filter
def group_scores(field, default):
    return [
        {
            'score': score,
            'rubric': '' if rubric is None else rubric,
            'checked': default in [score, str(score)],
        } for score, rubric in zip_longest(
            field.get('scores', []), field.get('rubrics', []), fillvalue=''
        )
    ]


@register.filter
def required(field):
    if 'required' in field.get('options', []):
        return 'required'
    else:
        return ''


@register.filter
def randomize_choices(choices, field):
    tmp = choices[:]
    if 'randomize' in field.get('options', []):
        random.shuffle(tmp)
    return tmp


@register.filter
def page_errors(validation, page):
    return {} if not isinstance(validation, dict) else validation.get('pages', {}).get(page, {})


@register.filter
def readable(value):
    return value.replace('_', ' ').capitalize()


@register.simple_tag(takes_context=True)
def define(context, **kwargs):
    for k, v in list(kwargs.items()):
        context[k] = v


@register.simple_tag(takes_context=True)
def check_error(context, field_name, errors, label='error'):
    if field_name in errors:
        return label
    return ""


@register.simple_tag(takes_context=True)
def field_label(context, field_name):
    page = context.get('page')
    if not page:
        return ''
    field = page.get_field(field_name)
    return field.label if field else ''


"""
Set of "markup" template filters for Django.  These filters transform plain text
markup syntaxes to HTML; currently there is support for:

    * Textile, which requires the PyTextile library available at
      http://loopcore.com/python-textile/

    * Markdown, which requires the Python-markdown library from
      http://www.freewisdom.org/projects/python-markdown

    * reStructuredText, which requires docutils from http://docutils.sf.net/
"""


@register.filter(name='textile', is_safe=False)
def textile(value):
    try:
        import textile
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in {% textile %} filter: The Python textile library isn't installed.")
        return value
    else:
        return mark_safe(textile.textile(smart_str(value), encoding='utf-8', output='utf-8'))


@register.filter(name='markdown', is_safe=True)
def markdown(value, arg=''):
    """
    Runs Markdown over a given value, optionally using various
    extensions python-markdown supports.

    Syntax::

        {{ value|markdown:"extension1_name,extension2_name..." }}

    To enable safe mode, which strips raw HTML and only returns HTML
    generated by actual Markdown syntax, pass "safe" as the first
    extension in the list.

    If the version of Markdown in use does not support extensions,
    they will be silently ignored.

    """
    try:
        import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in {% markdown %} filter: The Python markdown library isn't installed.")
        return value
    else:
        # markdown.version was first added in 1.6b. The only version of markdown
        # to fully support extensions before 1.6b was the shortlived 1.6a.
        if hasattr(markdown, 'version'):
            extensions = [e for e in arg.split(",") if e]
            if len(extensions) > 0 and extensions[0] == "safe":
                extensions = extensions[1:]

            # Unicode support only in markdown v1.7 or above. Version_info
            # exist only in markdown v1.6.2rc-2 or above.
            if getattr(markdown, "version_info", None) < (1, 7):
                return mark_safe(markdown.markdown(smart_str(value), extensions=extensions))
            else:
                return mark_safe(markdown.markdown(value, extensions=extensions))
        else:
            return mark_safe(markdown.markdown(smart_str(value)))


@register.filter(name='restructuredtext', is_safe=True)
def restructuredtext(value):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in {% restructuredtext %} filter: The Python docutils library isn't installed.")
        return value
    else:
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_str(value), writer_name="html4css1", settings_overrides=docutils_settings)
        return mark_safe(parts["fragment"])
