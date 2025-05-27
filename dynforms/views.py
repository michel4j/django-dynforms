from crisp_modals.views import ModalUpdateView, ModalDeleteView, ModalCreateView, AjaxFormMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.messages.views import SuccessMessageMixin
from django.db import DEFAULT_DB_ALIAS
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse

from django.views.generic import TemplateView, View, detail
from django.views.generic import edit
from django.views.generic.edit import FormView, UpdateView
from itemlist.views import ItemListView
from django.utils.module_loading import import_string
from dynforms.fields import FieldType
from dynforms.models import FormType

from . import utils, forms
from .forms import FieldSettingsForm, FormSettingsForm, RulesForm, DynForm
from .models import DynEntry


MIXINS = getattr(settings, 'DYNFORMS_MIXINS', {})

VIEW_MIXINS = [import_string(mixin) for mixin in MIXINS.get('VIEW',[])]
EDIT_MIXINS = [import_string(mixin) for mixin in MIXINS.get('EDIT', [])]


utils.load('dynfields')


class DynFormViewMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'object' in context:
            context['active_page'] = context['object'].details.get('active_page', 0)
        else:
            context['active_page'] = 0
        return context


class DynUpdateView(*EDIT_MIXINS, DynFormViewMixin, edit.UpdateView):
    pass


class DynCreateView(*EDIT_MIXINS, DynFormViewMixin, edit.CreateView):
    pass


class DynFormView(DynCreateView):
    template_name = 'dynforms/test-form.html'
    form_class = DynForm
    model = DynEntry

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_type = FormType.objects.get(pk=self.kwargs.get('pk'))
        kwargs['form_type'] = form_type
        return kwargs

    def form_valid(self, form):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.request.get_full_path()


class AddFieldView(*EDIT_MIXINS, TemplateView):
    template_name = "dynforms/field.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        field_type = FieldType.get_type(self.kwargs.get('type'))
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        num = len(form.get_page(page)['fields'])
        field = field_type.get_default(page, num)
        form.add_field(page, pos, field)
        context['field'] = field
        return context


class GetFieldView(*EDIT_MIXINS, TemplateView):
    template_name = "dynforms/field.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        field = form.get_field(page, pos)
        context['field'] = field
        return context


class MoveFieldView(*EDIT_MIXINS, TemplateView):
    template_name = 'dynforms/blank.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        src = int(self.kwargs.get('from_pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.move_field(page, src, pos)
        return context


class PageFieldView(*VIEW_MIXINS, TemplateView):
    template_name = 'dynforms/blank.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        next_page = int(self.kwargs.get('to'))
        src = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.move_field(page, src, src, next_page)
        return context


RULE_ACTIONS = [
    ("", ""),
    ("show", "Show if"),
    ("hide", "Hide if"),
    ("require", "Require if"),
]


class ModalFormView(AjaxFormMixin, FormView):
    """
    A FormView that returns a JsonResponse if the request is AJAX.
    """
    template_name = 'crisp_modals/form.html'


class FieldRulesView(*EDIT_MIXINS, ModalFormView):
    form_class = RulesForm
    template_name = "dynforms/rule-editor.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        kwargs['form_action'] = reverse_lazy("dynforms-field-rules", kwargs={"pk": form.pk, "page": page, "pos": pos})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        field = form.get_field(page, pos)
        field['rules'] = field.get('rules', [])
        context['field'] = field
        context['page'] = form.get_page(page)
        context['field_choices'] = [
            (f['name'], f['label']) for p in form.pages
            for f in p['fields'] if
            ((f['field_type'] != 'new-section') and (f['label'] != field['label']))
        ]
        context['action_url'] = reverse_lazy("dynforms-field-rules", kwargs={"pk": form.pk, "page": page, "pos": pos})
        context['field_operators'] = utils.FIELD_OPERATOR_CHOICES
        context['rule_actions'] = RULE_ACTIONS
        return context

    def form_valid(self, form):
        form_obj = FormType.objects.get(pk=self.kwargs.get('pk'))
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        field = form_obj.get_field(page, pos)
        rules = form.cleaned_data['rules']
        field['rules'] = rules
        form_obj.update_field(page, pos, field)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.get_full_path()


class DeleteFieldView(*EDIT_MIXINS, TemplateView):
    template_name = "dynforms/edit-settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.remove_field(page, pos)
        return context


class EditFieldView(*EDIT_MIXINS, FormView):
    template_name = "dynforms/edit-settings.html"
    form_class = FieldSettingsForm

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        field = form.get_field(page, pos)
        kw['field_type'] = FieldType.get_type(field['field_type'])
        kw['action_url'] = reverse_lazy("dynforms-put-field", kwargs={"pk": form.pk, "page": page, "pos": pos})
        kw['initial'] = field
        return kw

    def form_valid(self, form):
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form_obj = FormType.objects.get(pk=self.kwargs.get('pk'))
        field = form_obj.get_field(page, pos)
        field.update(form.cleaned_data)
        form_obj.update_field(page, pos, field)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.get_full_path()


class EditFormView(*EDIT_MIXINS, UpdateView):
    template_name = 'dynforms/builder.html'
    form_class = FormSettingsForm
    queryset = FormType.objects.all()

    def check_allowed(self):
        return super().check_allowed() and settings.DEBUG

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_type = FormType.objects.get(pk=self.kwargs.get('pk'))
        form = form_type
        initial = model_to_dict(form)
        initial.pop('pages')
        initial.pop('actions')
        initial['page_names'] = form.page_names()
        context['form_settings_form'] = FormSettingsForm(initial=initial, instance=form)
        context['fieldtypes'] = FieldType.get_all()
        context['form_spec'] = form
        context['warnings'] = form.check_form()
        context['active_page'] = self.request.GET.get('page', 1)
        context['active_form'] = self.request.GET.get('form', 1)
        return context

    def get_success_url(self):
        return self.request.get_full_path()


class DeletePageView(*EDIT_MIXINS, TemplateView):
    template_name = "dynforms/edit-settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.remove_page(page)
        return context


class FormTypeList(*EDIT_MIXINS, ItemListView):
    queryset = FormType.objects.all()
    template_name = "dynforms/list.html"
    tool_template = "dynforms/formtype-tools.html"
    paginate_by = 10
    link_url = 'dynforms-builder'
    list_columns = ['name', 'code', 'description']
    list_filters = ['created', 'modified']
    list_styles = {'description': 'col-xs-6'}
    list_search = ['name', 'url_slug', 'description']
    order_by = ['-created']


class CreateFormType(SuccessMessageMixin, *EDIT_MIXINS, ModalCreateView):
    form_class = forms.FormTypeForm
    model = FormType
    success_url = reverse_lazy('dynforms-list')
    success_message = "FormType '%(name)s' has been created."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(request=self.request)
        return kwargs

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({
            'pk': self.object.pk,
            'name': str(self.object),
        })


class EditTemplate(SuccessMessageMixin, *EDIT_MIXINS, ModalUpdateView):
    form_class = forms.FormTypeForm

    model = FormType
    success_url = reverse_lazy('dynforms-list')
    success_message = "FormType '%(name)s' has been updated."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(request=self.request)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_url'] = reverse_lazy('dynforms-edit-type', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({
            'pk': self.object.pk,
            'name': str(self.object),
        })


class DeleteFormType(*EDIT_MIXINS, ModalDeleteView):
    model = FormType

    def get_success_url(self):
        return reverse('dynforms-list')


class CheckFormAPI(*EDIT_MIXINS, detail.DetailView):
    template_name = "dynforms/warnings.html"
    model = FormType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['warnings'] = self.object.check_form()
        return context
