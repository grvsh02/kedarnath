# Generated by Django 4.2 on 2023-04-10 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_leaverequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
