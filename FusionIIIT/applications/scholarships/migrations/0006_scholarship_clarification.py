from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('scholarships', '0005_scholarship_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='scholarshipapplication',
            name='clarification_requested',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scholarshipapplication',
            name='clarification_response',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scholarshipapplication',
            name='clarification_document',
            field=models.FileField(blank=True, null=True, upload_to='scholarships/clarification_documents/'),
        ),
        migrations.AlterField(
            model_name='scholarshipapplication',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('UNDER_REVIEW', 'Under Review'), ('NEEDS_INFO', 'Needs Clarification'), ('FORWARDED', 'Forwarded'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('DISBURSED', 'Disbursed')], default='PENDING', max_length=20),
        ),
        migrations.CreateModel(
            name='ScholarshipDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to='scholarships/additional_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='additional_documents', to='scholarships.ScholarshipApplication')),
            ],
            options={
                'db_table': 'scholarships_scholarshipdocument',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]