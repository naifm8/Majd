from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('player', '0003_remove_status_from_playersession'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE player_playersession DROP COLUMN remind_me;",
            reverse_sql="ALTER TABLE player_playersession ADD COLUMN remind_me BOOLEAN DEFAULT FALSE;"
        ),
    ]
