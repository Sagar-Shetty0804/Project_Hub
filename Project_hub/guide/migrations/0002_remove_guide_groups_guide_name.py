# Generated by Django 5.1 on 2024-10-01 04:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('guide', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='guide_groups',
            name='guide_name',
        ),
    ]
