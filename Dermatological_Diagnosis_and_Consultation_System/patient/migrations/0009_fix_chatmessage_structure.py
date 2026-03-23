# Generated manually to fix ChatMessage table structure
from django.db import migrations


def fix_chatmessage_table(apps, schema_editor):
    """Fix the ChatMessage table structure using raw SQL"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # Check if appointment_id column exists (wrong structure)
        cursor.execute("PRAGMA table_info(patient_chatmessage)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'appointment_id' in columns:
            # Table has wrong structure, need to recreate it
            # First, drop the old table
            cursor.execute("DROP TABLE IF EXISTS patient_chatmessage")
            
            # Create the correct table structure
            cursor.execute("""
                CREATE TABLE patient_chatmessage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    image VARCHAR(100),
                    created_at DATETIME NOT NULL,
                    patient_id INTEGER NOT NULL REFERENCES patient_patient(id) DEFERRABLE INITIALLY DEFERRED
                )
            """)
            
            # Create index on patient_id
            cursor.execute("CREATE INDEX patient_chatmessage_patient_id_idx ON patient_chatmessage(patient_id)")


def reverse_fix(apps, schema_editor):
    """Reverse migration - recreate old structure if needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0008_alter_appointmentchatmessage_appointment_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_chatmessage_table, reverse_fix),
    ]
