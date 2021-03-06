# Generated by Django 3.1.1 on 2020-10-13 03:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formsaurus', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='position',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='ratingparameters',
            name='shape',
            field=models.CharField(choices=[('ST', 'Stars'), ('HE', 'Hearts'), ('US', 'Users'), ('TU', 'Thumbs'), ('CR', 'Crowns'), ('CA', 'Cats'), ('DO', 'Dogs'), ('CI', 'Circles'), ('FL', 'Flags'), ('DR', 'Droplets'), ('TI', 'Ticks'), ('LI', 'Lightbulbs'), ('TR', 'Trophies'), ('CL', 'Clouds'), ('TH', 'Thunderbolts'), ('PE', 'Pencils'), ('SK', 'Skulls')], max_length=2),
        ),
    ]
