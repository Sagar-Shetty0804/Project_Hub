# Generated by Django 5.1.2 on 2024-11-04 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='group_code',
            field=models.CharField(max_length=20),
        ),
    ]