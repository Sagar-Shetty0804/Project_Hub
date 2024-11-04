# Generated by Django 5.1.2 on 2024-11-04 17:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login_page', '0013_registerstudent_class'),
        ('student', '0007_alter_additionalfile_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='reference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=100)),
                ('group_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reference_files', to='Login_page.registerstudent')),
            ],
        ),
    ]
