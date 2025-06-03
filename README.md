# Django Dynamic Forms

A Django reusable App for dynamically designing and generating forms.

### Features

- Visual form builder interface
- Dynamic field addition and configuration
- Drag-and-drop field creation/arrangement
- Support for complex field types with sub-fields
- Multi-Page forms
- Live form preview
- Works with Bootstrap 5
- Support for light/dark themes
- Additional field types created in other django apps, are auto-detected and can be used in the form builder
- Supports custom validation and error handling
- Ability to associate rules with fields, allowing for conditional logic to hide or show fields based on user input on
  other fields

### Installation

1. Install the package using pip:
   ```bash
   pip install django-dynforms
   ```

2. Add `dynforms` and it's requirements to your `INSTALLED_APPS` in `settings.py`:
   ```python
    INSTALLED_APPS = [
         ...
         'crispy_forms',        # for form rendering
         'crispy_bootstrap5',   # for Bootstrap 5 support 
         'crisp_modals',        # for modal dialogs
         'dynforms',
         ...
    ]
    ```

3. Include the app URLs in your project’s `urls.py`:

   ```python
   from django.urls import path, include

   urlpatterns = [
       ...
       path('dynforms/', include('dynforms.urls')),
       ...
   ]
   ```

4. Create the necessary database tables by running the migrations:

   ```bash
   python manage.py migrate
   ```

## Usage

- Access the form builder at `/dynforms/`.
- Create a new form by clicking "Add Form" icon on the off-canvas Form Types sidebar or select a form from the list to
  edit it.
- The search bar allows you to filter the form list.
- Use the sidebar to add fields or drag a field from the sidebar onto the form to add it.
- To edit for field click on it and edit the settings using the form on the left-sidebar. Many of the field parameters
  will auto-apply and update the form in real-time.
- Undo/Redo capabilities are not yet implemented. All changes are currently saved automatically as you edit the form.
- To delete a field, click the trash icon on the field settings form.
- Fields can be rearranged by dragging within the form. Move a field from one page to another by dragging it onto the
  desired page tab.

## Abstract Model Classes

Inherit from the abstract class `BaseForm`, to create a model which records data from a dynamic form. This class
provides
the necessary fields and methods to handle form data. The `BaseForm` class provides the following fields:

- `created`: DateTime field that records when the form was created.
- `modified`: DateTime field that records when the form was last modified.
- `form_type`: A Foreign key to the form.
- `details`: A JSON field that stores the form data submitted by the user.
- `is_complete`: A Boolean field that indicates whether the form data is complete. Partial submissions are allowed to be
  saved, and the form can be completed later.

Additionally, the `BaseForm` class provides the following methods:

- `get_field_value(self, field_name, default=None)`: Returns the value of a specific field in the form.
- `validate(self, data=None)`: Sets the value of a specific field in the form. The validation login uses either the
  provided data or the current saved form data.

## Adding custom fields

To add custom fields to the form builder from another app, add a `dynfields.py`  module to your App's top-level
directory and define a new field inheriting from `dynforms.fields.FieldType`. Implement the necessary methods to handle
rendering, validation, and type conversion.

### Example Custom Field

```python
from dynforms.fields import FieldType
from django.utils.translation import gettext_lazy as _


class CoolField(FieldType):
    section = _('My Apps Fields')  # This will group the field under a custom section in the field menu
    name = _('Cool Field')
    ...  # other field attributes

    def render(self, context):
        # Custom rendering logic
        return f'<input type="text" name="{self.name}" value="{value or ""}">'

    def clean(self, value, multi=False, validate=True):
        """ 
        Custom cleaning logic for the field value.
        If `validate` is True, it will perform validation on the value.
        If `multi` is True, it will handle multiple values (e.g., for checkboxes).
        """
        if not value:
            raise ValueError('This field cannot be empty.')
        return value
```

### Field Attributes:

When defining a custom field, you can specify the following attributes:

- `name`: The name of the field.
- `section`: The section under which the field will be grouped in the field menu.
- `template_name`: The template used to render the field. If not provided, the field will try to find a template with
  the same name as the slugified field class name. Alternatively, you can override the `render()` method to provide
  custom HTML rendering.
- `options`: A list of options for the field, if applicable. They will be shown as checkboxes in the field form
  Supported options include:
    - "required": Whether the field is required.
    - "unique": Whether the field is unique,
    - "randomize": Randomize the choices, useful for multiple-choice fields.
    - "hide": The field should be hidden by default, used together with rules to reveal fields based on conditions
    - "inline": Use inline form fields
    - "other": Add an "Other" option for checkboxes or radio choices,
    - "repeat": The field can be repeatable.
    - Any other custom options specific to the field type can be added as a string.
- `settings`: A list of settings for the field. By default, all fields will have the following settings:
    - "label": The label for the field.
    - "instructions": Help text for the field.
    - "name": Placeholder text for the field.
    - "default": Default value for the field.
    - "choices": Choices for select fields, if applicable.

### Field Methods

#### `render(context)`
Renders the field in the given context. By default, the field is rendered using the template
specified with `template_name`. This attribute can be specified directly, or the `get_template_name` method can be
overridden to return the template name.

#### `clean(value, multi=False, validate=True)`
Cleans the value of the field. If `validate` is True, it will
perform validation on the value and raise a Validation error on failure. If `multi` is True, it will handle multiple 
values (e.g., for checkboxes).

## Screenshots

![Field Settings Sidebar](docs/src/field-editor.png)
*Field settings sidebar*

![Live Form Preview](docs/src/add-form.png)
*Form Creation*

![Live Form Preview](docs/src/form-list.png)
*List of forms*

![Form Builder UI](docs/src/field-panel.png)
*Form Builder interface showing the field menu and main designer area*

![Multi-Page Forms](docs/src/form-editor.png)
*Form editor showing multi-page form support*

## Contributing

Pull requests and issues are welcome!

## License

[MIT License](LICENSE)

---

Adjust the details as needed for your specific app and distribution method.   

 