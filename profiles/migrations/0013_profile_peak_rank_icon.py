from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0012_profile_peak_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='peak_rank_icon',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
