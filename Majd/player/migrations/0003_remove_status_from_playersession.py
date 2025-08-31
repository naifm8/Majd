from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('player', '0002_playerprofile_position'),  # ← تأكد من اسم آخر migration فعلي
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE player_playersession DROP COLUMN status;",
            reverse_sql="ALTER TABLE player_playersession ADD COLUMN status VARCHAR(20);"
        ),
    ]
