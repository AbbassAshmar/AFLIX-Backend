# Generated by Django 4.2.13 on 2024-05-29 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_remove_movie_commentsnumber'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='movie',
            name='contentRate',
        ),
        migrations.AddField(
            model_name='movie',
            name='contentRating',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movies', to='api.contentrating'),
        ),
    ]