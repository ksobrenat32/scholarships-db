# Generated by Django 5.1.5 on 2025-01-30 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_becario_fecha_nacimiento_remove_becario_sexo'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudnormal',
            name='tipo',
            field=models.CharField(default='A', max_length=1),
        ),
    ]
