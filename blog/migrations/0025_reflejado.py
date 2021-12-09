# Generated by Django 3.1.12 on 2021-12-08 06:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0024_remove_post_mexico_states'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reflejado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=1000)),
                ('date_posted', models.DateTimeField(default=django.utils.timezone.now)),
                ('likes', models.IntegerField(default=0)),
                ('dislikes', models.IntegerField(default=0)),
                ('latitude', models.FloatField(default=0, max_length=140)),
                ('longitude', models.FloatField(default=0, max_length=140)),
                ('header_image', models.ImageField(blank=True, null=True, upload_to='gallery/')),
                ('mexico_states', models.TextField(default=0, max_length=1000)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]