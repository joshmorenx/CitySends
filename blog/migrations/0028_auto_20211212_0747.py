# Generated by Django 3.1.12 on 2021-12-12 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0027_auto_20211209_0331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='estado',
            field=models.TextField(default=0, max_length=10),
        ),
    ]
