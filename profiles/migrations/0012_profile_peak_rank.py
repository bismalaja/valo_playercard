from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0011_delete_ability_abilitytemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='peak_rank',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
