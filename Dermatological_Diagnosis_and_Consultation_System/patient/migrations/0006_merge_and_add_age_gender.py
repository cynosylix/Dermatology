# Generated manually to merge migrations and add age/gender fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0002_chatmessage'),  # Our chatbot ChatMessage
        ('patient', '0005_prescription'),  # New appointment system
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='age',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='patient',
            name='gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O', max_length=1),
        ),
        migrations.AlterField(
            model_name='patient',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]

