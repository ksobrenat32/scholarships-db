from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becas_sntsa', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trabajador',
            name='pending_email',
            field=models.EmailField(blank=True, null=True),
        ),
    ]
