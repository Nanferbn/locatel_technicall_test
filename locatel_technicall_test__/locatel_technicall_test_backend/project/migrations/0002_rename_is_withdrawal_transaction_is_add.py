# Generated by Django 5.0.4 on 2024-04-14 02:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='is_withdrawal',
            new_name='is_add',
        ),
    ]
