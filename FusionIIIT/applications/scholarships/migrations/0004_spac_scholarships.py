from django.db import migrations

def create_default_scholarships(apps, schema_editor):
    ScholarshipType = apps.get_model('scholarships', 'ScholarshipType')
    ScholarshipType.objects.get_or_create(
        name='Merit Cum Means Scholarship',
        defaults={
            'category': 'NEED',
            'description': 'A scholarship for students who have merit but lack the means.',
            'amount': 25000,
            'frequency': 'ANNUAL',
            'eligibility_criteria': 'CPI > 6.0 and family income < 5 LPA',
            'max_backlogs': 0,
            'applicable_categories': 'GEN,OBC,SC,ST',
            'is_active': True,
        }
    )
    ScholarshipType.objects.get_or_create(
        name='Single Parent Scholarship',
        defaults={
            'category': 'CATEGORY',
            'description': 'A scholarship specifically designed to assist students from single parent households.',
            'amount': 20000,
            'frequency': 'ANNUAL',
            'eligibility_criteria': 'Student must be from a single-parent family. Minimum CPI 6.0.',
            'max_backlogs': 1,
            'applicable_categories': 'GEN,OBC,SC,ST',
            'is_active': True,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('scholarships', '0003_auto_20260314_1649'),
    ]

    operations = [
        migrations.RunPython(create_default_scholarships),
    ]