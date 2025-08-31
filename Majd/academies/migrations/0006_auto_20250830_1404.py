from django.db import migrations

def fix_academy_links(apps, schema_editor):
    Program = apps.get_model("academies", "Program")
    Session = apps.get_model("academies", "Session")
    Academy = apps.get_model("academies", "Academy")

    fixed_programs = 0
    fixed_sessions = 0

    # Fix Programs
    for program in Program.objects.select_related("academy"):
        academy = program.academy
        if academy and hasattr(academy, "owner"):
            correct_academy = academy.owner.academy
            if program.academy_id != correct_academy.id:
                program.academy_id = correct_academy.id
                program.save(update_fields=["academy"])
                fixed_programs += 1

    # Fix Sessions
    for session in Session.objects.select_related("program__academy"):
        program = session.program
        if program:
            correct_academy = program.academy
            if session.program.academy_id != correct_academy.id:
                # This should rarely happen unless DB is corrupted
                session.program.academy_id = correct_academy.id
                session.program.save(update_fields=["academy"])
                fixed_sessions += 1

    print(f"✅ Fixed {fixed_programs} Programs and {fixed_sessions} Sessions")

def reverse_fix(apps, schema_editor):
    # no-op (can't reverse safely)
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("academies", "0005_delete_subscriptionplan"),  # replace with your last migration name
    ]

    operations = [
        migrations.RunPython(fix_academy_links, reverse_fix),
    ]
