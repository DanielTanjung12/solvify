# Generated by Django 5.0 on 2024-01-02 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_meeting'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='zoom_link',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]