# Generated by Django 3.1.12 on 2022-05-19 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0028_auto_20211212_0747'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content',
            field=models.CharField(max_length=1000),
        ),
    ]