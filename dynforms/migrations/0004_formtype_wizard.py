# Generated by Django 5.2.1 on 2025-06-24 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynforms', '0003_formtype_help_bar_alter_formtype_header'),
    ]

    operations = [
        migrations.AddField(
            model_name='formtype',
            name='wizard',
            field=models.BooleanField(default=False, verbose_name='Wizard Mode'),
        ),
    ]
