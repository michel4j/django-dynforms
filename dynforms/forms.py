from datetime import datetime
from itertools import zip_longest
from crisp_modals.forms import ModalModelForm, Row, FullWidth, ModalForm
from crispy_forms.bootstrap import PrependedText, InlineCheckboxes, AppendedText
from crispy_forms.bootstrap import StrictButton, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, HTML
from django import forms
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.urls import reverse_lazy
from django.utils.datastructures import MultiValueDict
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from . import models
from .fields import FieldType, LayoutType
from .models import FormType
from .utils import Queryable, DotExpandedDict, build_Q, Crypt


class MultipleTextInput(forms.TextInput):
    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, [])

    def compress(self, data_list):
        return data_list

    def decompress(self, value):
        return value


class RepeatableCharField(forms.MultipleChoiceField):
    widget = MultipleTextInput

    def validate(self, value):
        """
        Validates that the input is a list or tuple.
        """
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')


FIELD_SETTINGS = {
    'label': (forms.CharField, {'label': _("Label"), 'required': True}),
    'name': (forms.CharField, {'label': _("Field Name"), 'required': True}),
    'instructions': (forms.CharField, {'label': _("Instructions"), 'widget': forms.Textarea(attrs={'rows': 2})}),
    'tags': (forms.CharField, {'label': _("Style tags")}),
    'size': (forms.ChoiceField, {'label': _("Size")}),
    'max_repeat': (forms.IntegerField, {'label': _("Max Repeat"), 'required': False}),
    'width': (forms.ChoiceField, {'label': _("Width")}),
    'options': (forms.MultipleChoiceField, {'label': _("Options"), 'widget': forms.CheckboxSelectMultiple}),
    'minimum': (forms.IntegerField, {'label': _("Min")}),
    'maximum': (forms.IntegerField, {'label': _("Max"), }),
    'units': (forms.ChoiceField, {'label': _("Units"), }),
    'default': (forms.CharField, {'label': _("Default value"), }),
    'choices': (RepeatableCharField, {'label': _("Choices"), 'required': True}),
    'scores': (RepeatableCharField, {'label': _("Scores"), 'required': True}),
    'rubrics': (RepeatableCharField, {'label': _("Rubrics"), 'required': True}),
    'values': (RepeatableCharField, {'label': _("Values"), 'required': True}),
    'names': (RepeatableCharField, {'label': _("Internal Names"), 'required': True}),
    'default_choices': (RepeatableCharField, {'label': _("Default")}),
}

CHOICES_TEMPLATE = "{% include 'dynforms/field-choices.html' %}"
NAMED_CHOICES_TEMPLATE = "{% include 'dynforms/field-named-choices.html' %}"
VALUES_TEMPLATE = "{% include 'dynforms/field-values.html' %}"
SCORES_TEMPLATE = "{% include 'dynforms/field-scores.html' %}"


class FieldSettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.field_type = kwargs.pop('field_type')
        action_url = kwargs.pop('action_url')
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'df-menu-form'
        self.helper.form_action = action_url
        if self.field_type is not None:
            self.helper.layout = Layout(
                self.create_layout(self.field_type)
            )
        else:
            self.helper.layout = self.create_layout()

    def clean(self):
        if self.field_type is None:
            raise ValidationError(_("Field type is not defined. Cannot save settings."))
        cleaned_data = super().clean()
        if 'default_choices' in cleaned_data:
            cleaned_data['default_choices'] = list(map(int, cleaned_data['default_choices']))
            cleaned_data['default'] = [cleaned_data['choices'][i - 1] for i in cleaned_data['default_choices']]
        return cleaned_data

    def add_custom_field(self, name, **kwargs):
        ft, kw = FIELD_SETTINGS[name]
        kwargs.update(kw)
        kwargs['required'] = kwargs.get('required', False)
        self.fields[name] = ft(**kwargs)

    def create_type_layout(self, field_type):
        fieldset = Div(
            Field('label'),
            Field('instructions', rows=2)
        )

        if field_type.options:
            self.add_custom_field('options', choices=field_type.get_choices('options'))
            fieldset.append(InlineCheckboxes('options'))

        row = Div(
            Div('width', css_class='col'),
            css_class="row"
        )
        if 'repeat' in field_type.options:
            self.add_custom_field('max_repeat', min_value=1)
            row.append(Div('max_repeat', css_class='col'))

        if 'size' in field_type.settings:
            self.add_custom_field('size', choices=field_type.get_choices('size'))
            row.append(Div(Field('size', css_class='select'), css_class='col'))

        fieldset.append(row)

        if {'minimum', 'maximum', 'units'} & set(field_type.settings):
            self.add_custom_field('minimum')
            self.add_custom_field('maximum')
            entries = [Div('minimum', css_class='col'), Div('maximum', css_class='col')]
            if 'units' in field_type.settings:
                self.add_custom_field('units', choices=field_type.get_choices('units'))
                entries.append(Div('units', css_class='col-auto'))
            fieldset.append(Div(*entries, css_class="row"))

        if 'named-choices' in field_type.settings:
            self.add_custom_field('default_choices')
            self.add_custom_field('choices')
            self.add_custom_field('names')

            self.initial['choices_info'] = [
                {'label': label, 'name': name}
                for label, name in zip_longest(
                    self.initial.get('choices', []),
                    self.initial.get('names', []),
                    fillvalue=''
                )
            ]
            fieldset.append(HTML(NAMED_CHOICES_TEMPLATE))
        else:
            # separate choices and values
            if 'choices' in field_type.settings:
                self.add_custom_field('default_choices')
                self.add_custom_field('choices')
                self.initial['choices_type'] = field_type.choices_type
                fieldset.append(HTML(CHOICES_TEMPLATE))

            if 'values' in field_type.settings:
                self.add_custom_field('values')
                fieldset.append(HTML(VALUES_TEMPLATE))

        if 'scores' in field_type.settings:
            self.add_custom_field('scores')
            self.add_custom_field('rubrics')
            self.initial['scores_info'] = [
                {
                    'score': score,
                    'rubric': rubric
                }
                for score, rubric in zip_longest(
                    self.initial.get('scores', []),
                    self.initial.get('rubrics', []),
                    fillvalue=''
                )
            ]
            fieldset.append(HTML(SCORES_TEMPLATE))

        if 'default' in field_type.settings:
            self.add_custom_field('default')
            fieldset.append('default'),
        fieldset.append('tags')
        return fieldset

    def create_layout(self, field_type=None):
        # All field types have these in common
        for nm in ['name', 'label', 'instructions', 'width', 'tags']:
            self.add_custom_field(nm)
        self.add_custom_field('width', choices=LayoutType)

        if field_type:
            fieldset = Div(
                AppendedText(
                    'name', mark_safe(f"<small>🗲&nbsp;{field_type.name}</small>"),
                    title="This is the internal reference name for the field. Change with caution!"
                ),
                self.create_type_layout(field_type),
            )
        else:
            fieldset = Div(
                HTML(
                    '<div class="alert alert-warning">'
                    '   <div class="panel-body">'
                    '       <h4>Field Type Undefined</h4>'
                    '       <p>Please delete this field, or select a different field to edit its settings.</p>'
                    '   </div>'
                    '</div>'
                ),
                AppendedText(
                    'name', mark_safe(f"⚠<small>&nbsp;Unknown</small>"),
                    title="This is the internal reference name for the field. Change with caution!"
                ),
            )

        if self.initial.get('rules', []):
            rule_html = "Rules <span class='badge bg-info'>%d</span>" % (len(self.initial['rules']))
        else:
            rule_html = "Rules"

        fieldset.append(
            FormActions(
                HTML('<hr class="mt-5"/>'),
                Div(
                    StrictButton(
                        'Apply', name='apply-field', id='apply-field', value="apply-field",
                        css_class="btn btn-primary"
                    ),
                    StrictButton(rule_html, css_class='btn btn-secondary', id='edit-rules',
                                 value="edit-rules"),
                    StrictButton(
                        'Delete', name='delete-field', value="delete-field", id="delete-field",
                        css_class="btn btn-danger pull-right"
                    ),
                    css_class="col-12 text-condensed d-flex flex-row justify-content-between"
                )
            )
        )
        return fieldset


PAGES_TEMPLATE = "{% include 'dynforms/form-pages.html' %}"
ACTIONS_TEMPLATE = "{% include 'dynforms/form-actions.html' %}"


class FormSettingsForm(forms.ModelForm):
    page_names = RepeatableCharField(label=_("Pages"), required=True)
    action_names = RepeatableCharField(label=_("Action Buttons"), required=False)
    action_labels = RepeatableCharField(label=_("Action Buttons"), required=False)

    class Meta:
        model = models.FormType
        fields = (
            'code', 'name', 'description', 'header', 'help_bar', 'wizard', 'page_names',
            'actions', 'pages', 'action_names', 'action_labels'
        )
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'Unique slug, e.g. "feedback-form"'}),
            'name': forms.TextInput(attrs={'placeholder': 'Human friendly name'}),
            'header': forms.CheckboxInput(),
            'help_bar': forms.CheckboxInput(),
            'wizard': forms.CheckboxInput(),
            'description': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Please provide a description content.'}
            ),
            'pages': forms.HiddenInput(),
            'actions': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'df-menu-form'
        delete_url = reverse_lazy('dynforms-delete-type', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Div('code', css_class='col-12'),
                Div("name", css_class='col-12'),
                Div("description", css_class='col-12'),
                Div("header", css_class='col-4'),
                Div("help_bar", css_class='col-4'),
                Div("wizard", css_class='col-4'),
                css_class="row"
            ),
            HTML(PAGES_TEMPLATE),
            HTML(ACTIONS_TEMPLATE),
            FormActions(
                HTML('<hr class="hr-xs mt-5"/>'),
                Div(
                    Submit('apply-form', 'Apply', css_class="btn btn-primary"),
                    HTML(
                        f'<a class="btn btn-danger ms-auto" title="Delete Form" '
                        f'data-modal-url="{delete_url}">Delete</a>'
                    ),
                    css_class="d-flex flex-row"
                )
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['actions'] = list(zip(cleaned_data['action_names'], cleaned_data['action_labels']))

        if self.instance:
            pages = self.instance.pages
        else:
            pages = []

        titles = cleaned_data['page_names']
        for page, title in enumerate(titles):
            if page < len(pages):
                pages[page]['name'] = title
            else:
                pages.append({'name': title, 'fields': []})
        if len(pages) > len(titles) and len(pages[-1]['fields']) == 0:
            pages.pop()
        cleaned_data['pages'] = pages

        return cleaned_data


class RulesForm(ModalForm):
    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['rules'] = []
        data = DotExpandedDict(dict(self.data.lists()))
        if 'rule' in data:
            raw_rules = list(
                map(dict, list(zip(*[[(k, v) for v in value] for k, value in list(data['rule'].items())]))))
            cleaned_data['rules'] = [r for r in raw_rules if any(r.values())]
        return cleaned_data


class DynFormMixin:
    field_specs: dict
    instance: models.DynEntry = None
    form_type: models.FormType = None
    initial: dict
    cleaned_data: dict

    def init_fields(self):
        self.initial['throttle'] = Crypt.encrypt(datetime.now().isoformat())
        if not self.form_type and self.instance and hasattr(self.instance, 'form_type'):
            self.form_type = self.instance.form_type
        self.field_specs = self.form_type.field_specs()

    def get_validation(self):
        if self.instance:
            return self.instance.validate()
        return {}

    def clean(self):
        super().clean()

        # convert dotted notation to nested dict
        if isinstance(self.data, QueryDict):
            data = DotExpandedDict(dict(self.data.lists()))
        else:
            data = DotExpandedDict(self.data)

        # convert lists (same as dotted notation but with an integer key)
        data = data.with_lists()

        self.cleaned_data['form_type'] = self.form_type
        processed_data, errors = self.form_type.clean_data(data)
        self.cleaned_data['details'] = processed_data
        if errors:
            [
                self.add_error(None, f'{field}: {error}')
                for page, field_errors in errors.items()
                for field, error in field_errors.items()
            ]

        return self.cleaned_data


class DynModelForm(DynFormMixin, forms.ModelForm):
    class Meta:
        model = models.DynEntry
        fields = []

    def __init__(self, *args, **kwargs):
        self.form_type = kwargs.pop('form_type')
        super().__init__(*args, **kwargs)
        self.init_fields()


class DynForm(DynFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        self.form_type = kwargs.pop('form_type')
        super().__init__(*args, **kwargs)
        self.init_fields()


class FormTypeForm(ModalModelForm):
    class Meta:
        model = models.FormType
        fields = ('code', 'name', 'description')
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'Unique slug, e.g. "feedback-form"'}),
            'name': forms.TextInput(attrs={'placeholder': 'Human friendly name'}),
            'description': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Please provide a description content.'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

        self.body.form_action = self.request.get_full_path()
        self.body.append(
            Row(
                FullWidth('code'),
                FullWidth("name"),
                FullWidth("description"),
            ),
        )
