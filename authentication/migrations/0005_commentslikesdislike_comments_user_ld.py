# Generated by Django 4.1.3 on 2023-02-02 15:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_user_pfp'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentsLikesDislike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('liked', models.BooleanField(default=False)),
                ('disliked', models.BooleanField(default=False)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.comments')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='comments',
            name='user_ld',
            field=models.ManyToManyField(through='authentication.CommentsLikesDislike', to=settings.AUTH_USER_MODEL),
        ),
    ]
