# Generated by Django 3.1.1 on 2020-10-21 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formsaurus', '0003_auto_20201019_2133'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='show_branding',
            field=models.BooleanField(default=True),
        ),
    ]
