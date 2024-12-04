# Generated by Django 5.1.3 on 2024-12-03 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ncjm', '0003_tag_created_at'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='reactiontracker',
            name='ncjm_reacti_joke_id_35c187_idx',
        ),
        migrations.AlterUniqueTogether(
            name='reactiontracker',
            unique_together={('joke', 'ip_address', 'user_agent')},
        ),
        migrations.AddField(
            model_name='joke',
            name='reactions',
            field=models.JSONField(default=dict, help_text='The reactions to the joke stored as totals.'),
        ),
        migrations.AddIndex(
            model_name='joketag',
            index=models.Index(fields=['joke'], name='ncjm_joketa_joke_id_e73529_idx'),
        ),
        migrations.AddIndex(
            model_name='joketag',
            index=models.Index(fields=['tag'], name='ncjm_joketa_tag_id_256c86_idx'),
        ),
        migrations.AddIndex(
            model_name='joketag',
            index=models.Index(fields=['joke', 'tag'], name='ncjm_joketa_joke_id_19ea40_idx'),
        ),
        migrations.AddIndex(
            model_name='reactiontracker',
            index=models.Index(fields=['joke', 'ip_address', 'user_agent'], name='ncjm_reacti_joke_id_be053e_idx'),
        ),
        migrations.RemoveField(
            model_name='reactiontracker',
            name='reaction',
        ),
    ]
