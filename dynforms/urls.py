from django.urls import path

from dynforms import views
###
# The field urls are used to manage the fields of a form from javascript. Since the javascript any changes to these
# urls will require changes to the javascript. The form urls are used to manage the form itself.
###
urlpatterns = [
    path('', views.FormList.as_view(), name='dynforms-list'),
    path('new/', views.CreateFormType.as_view(), name='dynforms-create-type'),
    path('<int:pk>/', views.FormBuilder.as_view(), name='dynforms-builder'),
    path('<int:pk>/run/', views.TestFormView.as_view(), name='dynforms-run'),
    path('<int:pk>/check/', views.CheckFormAPI.as_view(), name='dynforms-check'),
    path('<int:pk>/edit/', views.EditTemplate.as_view(), name='dynforms-edit-template'),
    path('<int:pk>/delete/', views.DeleteFormType.as_view(), name='dynforms-delete-type'),


    # field urls
    path('<int:pk>/<int:page>/add/<slug:type>/<int:pos>/', views.AddFieldView.as_view(), name='dynforms-add-field'),
    path('<int:pk>/<int:page>/del/<int:pos>/', views.DeleteFieldView.as_view(), name='dynforms-del-field'),
    path('<int:pk>/<int:page>/clone/<int:pos>/', views.CloneFieldView.as_view(), name='dynforms-clone-field'),
    path('<int:pk>/<int:page>/del/', views.DeletePageView.as_view(), name='dynforms-del-page'),
    path('<int:pk>/<int:page>/put/<int:pos>/', views.EditFieldView.as_view(), name='dynforms-put-field'),
    path('<int:pk>/<int:page>/get/<int:pos>/', views.GetFieldView.as_view(), name='dynforms-get-field'),
    path('<int:pk>/move/', views.MoveFieldView.as_view(), name='dynforms-move-field'),
    path('<int:pk>/<int:page>/rules/<int:pos>/', views.FieldRulesView.as_view(), name='dynforms-field-rules'),

]