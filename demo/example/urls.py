from django.urls import path

from . import views
from .views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path('people/', views.FancyPersonList.as_view(), name='person-list'),
    path('test/', views.TemplateView.as_view(template_name='example/test.html'), name='test-view'),
    path('institutions/', views.FancyInstitutionList.as_view(), name='institution-list'),
    path('subjects/', views.FancySubjectList.as_view(), name='subject-list'),
    path('people/<int:pk>/edit/', views.EditPerson.as_view(), name='person-edit'),
    path('people/add/', views.AddPerson.as_view(), name='person-add'),
    path('institutions/<int:pk>/edit/', views.EditInstitution.as_view(), name='institution-edit'),
    path('institutions/add/', views.AddInstitution.as_view(), name='institution-add'),
    path('subjects/<int:pk>/edit/', views.EditSubject.as_view(), name='subject-edit'),
    path('subjects/add/', views.AddSubject.as_view(), name='subject-add'),
    path('people/<int:pk>/delete/', views.DeletePerson.as_view(), name='person-delete'),
    path('institutions/<int:pk>/delete/', views.DeleteInstitution.as_view(), name='institution-delete'),
    path('subjects/<int:pk>/delete/', views.DeleteSubject.as_view(), name='subject-delete'),

]

