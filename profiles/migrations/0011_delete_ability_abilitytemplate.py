from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_profile_user_userprofile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Ability',
        ),
        migrations.DeleteModel(
            name='AbilityTemplate',
        ),
    ]
