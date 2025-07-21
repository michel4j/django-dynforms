from crisp_modals.views import ModalUpdateView, ModalDeleteView, ModalCreateView, AjaxFormMixin
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.template.response import TemplateResponse
from django.urls import reverse_lazy, reverse
from django.utils.module_loading import import_string
from django.views import View
from django.views.generic import TemplateView, detail
from django.views.generic import edit
from django.views.generic.edit import FormView, UpdateView

from dynforms.fields import FieldType
from dynforms.models import FormType
from . import utils, forms
from .forms import FieldSettingsForm, FormSettingsForm, RulesForm, DynModelForm, DynForm
from .models import DynEntry
from .utils import FormFieldManager

import yaml

MIXINS = getattr(settings, 'DYNFORMS_MIXINS', {})

VIEW_MIXINS = [import_string(mixin) for mixin in MIXINS.get('VIEW', [])]
EDIT_MIXINS = [import_string(mixin) for mixin in MIXINS.get('EDIT', [])]

utils.load('dynfields')


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
        context['field'] = FormFieldManager(**field, index=pos)
        return context


class GetFieldView(*EDIT_MIXINS, TemplateView):
    template_name = "dynforms/field.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        field = form.get_field(page, pos)
        context['field'] = FormFieldManager(**field, index=pos)
        return context


class MoveFieldView(*EDIT_MIXINS, View):

    def post(self, request, **kwargs):
        from_page = request.POST.get('from_page', None)
        to_page = request.POST.get('to_page', None)
        from_pos = request.POST.get('from_pos', None)
        to_pos = request.POST.get('to_pos', None)

        invalid = (
            from_page is None or to_page is None or from_pos is None or to_pos is None
        )
        if not invalid:
            from_page = int(from_page)
            to_page = int(to_page)
            from_pos = int(from_pos)
            to_pos = int(to_pos)
            form = FormType.objects.get(pk=self.kwargs.get('pk'))
            form.move_field(from_page, from_pos, to_pos, to_page)
            return JsonResponse({})

        return JsonResponse({})


class CloneFieldView(*EDIT_MIXINS, View):

    def post(self, request, **kwargs):
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.clone_field(page, pos)
        return JsonResponse({})


class PageFieldView(*VIEW_MIXINS, View):

    def post(self, request, **kwargs):
        page = int(self.kwargs.get('page'))
        next_page = int(self.kwargs.get('to'))
        src = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.move_field(page, src, src, next_page)
        return JsonResponse({})


class DeleteFieldView(*EDIT_MIXINS, View):
    template_name = "dynforms/edit-settings.html"

    def post(self, request, **kwargs):
        page = int(self.kwargs.get('page'))
        pos = int(self.kwargs.get('pos'))
        form = FormType.objects.get(pk=self.kwargs.get('pk'))
        form.remove_field(page, pos)
        return TemplateResponse(request, self.template_name, {})


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
        field_obj = FormFieldManager(**field, index=pos)
        if field_obj.type:
            field.update(form.cleaned_data)
            form_obj.update_field(page, pos, field)
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.get_full_path()


class FormList(*EDIT_MIXINS, TemplateView):
    template_name = 'dynforms/builder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_types'] = FormType.objects.all()
        return context


class FormBuilder(*EDIT_MIXINS, UpdateView):
    template_name = 'dynforms/builder.html'
    form_class = FormSettingsForm
    queryset = FormType.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_types'] = FormType.objects.all()
        form_type = FormType.objects.get(pk=self.kwargs.get('pk'))
        form = form_type
        initial = model_to_dict(form)
        initial.pop('pages')
        initial.pop('actions')
        initial['page_names'] = form.page_names()
        context['form_settings_form'] = FormSettingsForm(initial=initial, instance=form)
        context['field_types'] = FieldType.get_all()
        context['form_type'] = form
        context['warnings'] = form.check_form()
        context['active_page'] = self.request.GET.get('page', 1)
        context['active_form'] = self.request.GET.get('form', 1)
        return context

    def get_success_url(self):
        return self.request.get_full_path()


class DeletePageView(*EDIT_MIXINS, View):

    def post(self, request, **kwargs):
        page = int(self.kwargs.get('page'))
        form_type = FormType.objects.get(pk=self.kwargs.get('pk'))
        try:
            form_type.remove_page(page)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({})


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
        return JsonResponse(
            {
                'pk': self.object.pk,
                'name': str(self.object),
            }
        )


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
        context['submit_url'] = reverse_lazy('dynforms-builder', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse(
            {
                'pk': self.object.pk,
                'name': str(self.object),
            }
        )


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


class DynUpdateView(edit.UpdateView):
    template_name = 'dynforms/test-form.html'
    form_class = DynModelForm
    model = DynEntry

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.object = self.get_object()
        kwargs['form_type'] = self.object.form_type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_type = self.object.form_type
        context['form_type'] = form_type
        context['active_page'] = max(1, context['object'].details.get('active_page', 1))
        return context


class DynCreateView(edit.CreateView):
    template_name = 'dynforms/test-form.html'
    form_class = DynModelForm
    model = DynEntry

    def get_form_type(self) -> FormType:
        """
        Get the FormType instance.
        """
        form_type = FormType.objects.filter(pk=self.kwargs.get('pk')).first()
        if not form_type:
            raise Http404("FormType does not exist.")
        return form_type

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_type'] = self.get_form_type()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = self.get_form_type()
        context['active_page'] = 1
        return context

    def form_valid(self, form):
        import pprint
        pprint.pprint(form.cleaned_data)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.request.get_full_path()


class DynFormView(FormView):
    template_name = 'dynforms/test-form.html'
    form_class = DynForm

    def get_form_type(self) -> FormType:
        """
        Get the FormType instance.
        """
        form_type = FormType.objects.filter(pk=self.kwargs.get('pk')).first()
        if not form_type:
            raise Http404("FormType does not exist.")
        return form_type

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_type'] = self.get_form_type()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_page = self.request.GET.get('page', 1)
        context['form_type'] = self.get_form_type()
        context['active_page'] = active_page
        return context

    def get_success_url(self):
        return self.request.get_full_path()


class TestFormView(DynFormView):
    def form_valid(self, form):
        print('-'*79)
        print(yaml.dump(form.cleaned_data['details']))
        print('-'*79)
        return self.form_invalid(form)

