# Generated by Django 5.1 on 2024-10-05 19:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Login_page', '0010_alter_registerstudent_groupcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/additional/')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('group_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_files', to='Login_page.registerstudent')),
            ],
        ),
        migrations.CreateModel(
            name='CodeFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/code/')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('group_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='code_files', to='Login_page.registerstudent')),
            ],
        ),
        migrations.CreateModel(
            name='DatabaseFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/database/')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('group_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='database_files', to='Login_page.registerstudent')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/document/')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('group_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='document_files', to='Login_page.registerstudent')),
            ],
        ),
    ]
