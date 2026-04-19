<<<<<<< HEAD
"""
api/serializers.py – Award & Scholarship Module
Responsible for data serialization, deserialization, and field-level validation.
No business logic here; service calls belong in views.py.
"""

from rest_framework import serializers

from ..models import (
    ApplicationStatus,
    Award,
    AwardCategory,
    AwardRecipient,
    FrequencyChoice,
    MeritList,
    MeritListEntry,
    ScholarshipApplication,
    ScholarshipCategory,
    ScholarshipType,
)


# ─────────────────────────────────────────────
# ScholarshipType Serializers
# ─────────────────────────────────────────────

class ScholarshipTypeSerializer(serializers.ModelSerializer):
    category_display  = serializers.CharField(source="get_category_display", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)

    class Meta:
        model  = ScholarshipType
        fields = [
            "id", "name", "category", "category_display",
            "description", "amount", "frequency", "frequency_display",
            "eligibility_criteria", "cpi_cutoff", "annual_family_income_limit", "max_backlogs",
            "applicable_categories", "applicable_programmes",
            "applicable_batches", "deadline", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Scholarship amount must be a positive value.")
        return value

    def validate_max_backlogs(self, value):
        if value < 0:
            raise serializers.ValidationError("Max backlogs cannot be negative.")
        return value

    def validate_category(self, value):
        valid = [c.value for c in ScholarshipCategory]
        if value not in valid:
            raise serializers.ValidationError(f"Invalid category. Choose from: {valid}")
        return value

    def validate_frequency(self, value):
        valid = [f.value for f in FrequencyChoice]
        if value not in valid:
            raise serializers.ValidationError(f"Invalid frequency. Choose from: {valid}")
        return value


# ─────────────────────────────────────────────
# ScholarshipApplication Serializers
# ─────────────────────────────────────────────

class ScholarshipApplicationSerializer(serializers.ModelSerializer):
    status_display           = serializers.CharField(source="get_status_display", read_only=True)
    scholarship_type_name    = serializers.CharField(source="scholarship_type.name", read_only=True)
    student_roll             = serializers.CharField(source="student.id_id", read_only=True)
    category                 = serializers.ChoiceField(
        choices=["GEN", "SC", "ST", "OBC"], write_only=True, required=False
    )
    cpi                      = serializers.FloatField(required=False, allow_null=True)
    annual_family_income     = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model  = ScholarshipApplication
        fields = [
            "id", "student", "student_roll",
            "scholarship_type", "scholarship_type_name",
            "academic_year", "semester", "category", "cpi", "annual_family_income",
            "category_at_application", "contact_number",
            "application_date", "supporting_documents", "remarks",
            "status", "status_display",
            "reviewed_by", "review_date", "review_remarks",
            "amount_approved", "disbursement_date", "transaction_reference",
        ]
        read_only_fields = [
            "id", "application_date", "category_at_application",
            "status", "reviewed_by", "review_date", "review_remarks",
            "amount_approved", "disbursement_date", "transaction_reference",
        ]
        # We rely on create_scholarship_application service to check duplicates,
        # so we disable the default model validator that throws a 400 error.
        validators = []

    def validate_academic_year(self, value):
        # Expected format: YYYY-YY e.g. "2024-25"
        import re
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise serializers.ValidationError(
                "academic_year must be in the format 'YYYY-YY' (e.g., '2024-25')."
            )
        return value

    def validate_semester(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Semester must be between 1 and 12.")
        return value

    def validate_supporting_documents(self, value):
        max_size = 200 * 1024
        if value and value.name and value.name.endswith('mcm_documents.zip'):
            max_size = 6 * 200 * 1024
        if value and value.size > max_size:
            raise serializers.ValidationError(f"File size must not exceed {max_size // 1024}KB.")
        return value

class ScholarshipApplicationDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer for the detail view with full student info."""
    status_display           = serializers.CharField(source="get_status_display", read_only=True)
    scholarship_type_name    = serializers.CharField(source="scholarship_type.name", read_only=True)
    student_roll             = serializers.CharField(source="student.id_id", read_only=True)
    student_name             = serializers.SerializerMethodField()
    student_programme        = serializers.CharField(source="student.programme", read_only=True)
    student_batch            = serializers.IntegerField(source="student.batch", read_only=True)
    student_category         = serializers.CharField(source="student.category", read_only=True)
    student_cpi              = serializers.FloatField(source="student.cpi", read_only=True)

    class Meta:
        model  = ScholarshipApplication
        fields = [
            "id", "student", "student_roll", "student_name",
            "student_programme", "student_batch", "student_category", "student_cpi",
            "scholarship_type", "scholarship_type_name",
            "academic_year", "semester",
            "category_at_application", "cpi", "annual_family_income", "contact_number",
            "application_date", "supporting_documents", "remarks",
            "status", "status_display",
            "reviewed_by", "review_date", "review_remarks",
            "amount_approved", "disbursement_date", "transaction_reference",
        ]

    def get_student_name(self, obj):
        user = obj.student.id.user
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.username


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Used for PATCH requests to update application status (approve / reject / disburse)."""
    new_status              = serializers.ChoiceField(choices=ApplicationStatus.choices)
    review_remarks          = serializers.CharField(required=False, allow_blank=True, default="")
    amount_approved         = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )

    def validate(self, attrs):
        if attrs["new_status"] == ApplicationStatus.APPROVED and attrs.get("amount_approved") is None:
            raise serializers.ValidationError(
                {"amount_approved": "amount_approved is required when approving an application."}
            )
        return attrs


class DisbursementSerializer(serializers.Serializer):
    """Used for POST /disburse/ endpoint."""
    transaction_reference = serializers.CharField(max_length=100)

    def validate_transaction_reference(self, value):
        if not value.strip():
            raise serializers.ValidationError("Transaction reference cannot be blank.")
        return value.strip()


# ─────────────────────────────────────────────
# Award Serializers
# ─────────────────────────────────────────────

class AwardSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model  = Award
        fields = [
            "id", "name", "category", "category_display",
            "description", "criteria", "prize_amount",
            "certificate_provided", "applicable_programmes", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_category(self, value):
        valid = [c.value for c in AwardCategory]
        if value not in valid:
            raise serializers.ValidationError(f"Invalid category. Choose from: {valid}")
        return value

    def validate_prize_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Prize amount cannot be negative.")
        return value


class AwardRecipientSerializer(serializers.ModelSerializer):
    award_name   = serializers.CharField(source="award.name", read_only=True)
    student_roll = serializers.CharField(source="student.id_id", read_only=True)

    class Meta:
        model  = AwardRecipient
        fields = [
            "id", "award", "award_name",
            "student", "student_roll",
            "academic_year", "award_date",
            "citation", "certificate_issued", "awarded_by",
        ]
        read_only_fields = ["id"]

    def validate_academic_year(self, value):
        import re
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise serializers.ValidationError(
                "academic_year must be in the format 'YYYY-YY' (e.g., '2024-25')."
            )
        return value


# ─────────────────────────────────────────────
# MeritList Serializers
# ─────────────────────────────────────────────

class MeritListEntrySerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.id_id", read_only=True)

    class Meta:
        model  = MeritListEntry
        fields = ["id", "rank", "student", "student_roll"]


class MeritListSerializer(serializers.ModelSerializer):
    entries      = MeritListEntrySerializer(many=True, read_only=True)
    batch_name   = serializers.CharField(source="batch.name", read_only=True)

    class Meta:
        model  = MeritList
        fields = ["id", "batch", "batch_name", "academic_year", "semester", "generated_date", "entries"]
        read_only_fields = ["id", "generated_date"]

    def validate_semester(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Semester must be between 1 and 12.")
        return value


class MeritListGenerateSerializer(serializers.Serializer):
    """Input for POST /merit-list/generate/"""
    batch_id      = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)
    semester      = serializers.IntegerField(min_value=1, max_value=12)

    def validate_academic_year(self, value):
        import re
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise serializers.ValidationError(
                "academic_year must be in the format 'YYYY-YY' (e.g., '2024-25')."
            )
        return value


class EligibleStudentSerializer(serializers.Serializer):
    """Read-only representation of an eligible student for a scholarship."""
    roll_no     = serializers.CharField(source="id_id")
    category    = serializers.CharField()
    programme   = serializers.CharField()
    batch_year  = serializers.IntegerField(source="batch_id.year")
    batch_name  = serializers.CharField(source="batch_id.name")
=======
﻿from rest_framework import serializers
from ..models import (
    Award_and_scholarship, Release, Application, Mcm,
    ExtendedScholarshipType, ScholarshipApplication,
    Award, AwardRecipient, MeritList, MeritListEntry
)


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    award = AwardSerializer(read_only=True)

    class Meta:
        model = Release
        fields = ['id', 'award', 'startdate', 'enddate', 'batch', 'programme']


class ApplicationReadSerializer(serializers.ModelSerializer):
    award_name = serializers.CharField(source='award.award_name', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'award_name', 'status', 'created_at', 'remarks']


class McmCreateSerializer(serializers.Serializer):
    award_id = serializers.IntegerField(required=True)
    brother_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    brother_occupation = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    sister_name = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    sister_occupation = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    income_father = serializers.IntegerField(default=0)
    income_mother = serializers.IntegerField(default=0)
    income_other = serializers.IntegerField(default=0)
    father_occ = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)
    mother_occ = serializers.CharField(max_length=100, allow_blank=True, allow_null=True, required=False)


class MedalCreateSerializer(serializers.Serializer):
    award_id = serializers.IntegerField(required=True)
    correspondence_address = serializers.CharField(required=True)
    financial_assistance = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    grand_total = serializers.FloatField(required=True)
    nearest_policestation = serializers.CharField(max_length=100, required=True)
    nearest_railwaystation = serializers.CharField(max_length=100, required=True)
    academic_achievements = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    title_of_project = serializers.CharField(max_length=200, allow_blank=True, allow_null=True, required=False)


class AwardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = ['award_name', 'catalog', 'award_type']

    def validate_award_name(self, value):
        if Award_and_scholarship.objects.filter(award_name__iexact=value).exists():
            raise serializers.ValidationError("Award with this name already exists.")
        return value


class StudentDetailSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    batch = serializers.CharField()
    programme = serializers.CharField()
    category = serializers.CharField()
    cgpa = serializers.FloatField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    department = serializers.CharField(allow_null=True)
    eligibility_status = serializers.CharField()
    ineligibility_reasons = serializers.ListField(child=serializers.CharField(), required=False)


class EligibilityCheckSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    scholarship_id = serializers.IntegerField()


class MeritListEntrySerializer(serializers.Serializer):
    student = StudentDetailSerializer()
    rank = serializers.IntegerField()
    cgpa = serializers.FloatField()
    eligible_for_scholarships = serializers.BooleanField()


class BatchStatisticsSerializer(serializers.Serializer):
    batch = serializers.CharField()
    programme = serializers.CharField()
    category = serializers.CharField()
    total_students = serializers.IntegerField()
    applied_scholarships = serializers.IntegerField()
    approved_scholarships = serializers.IntegerField()


class ReleaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = ['award', 'startdate', 'enddate', 'batch', 'programme', 'notif_visible']


# ========== EXTENDED SCHOLARSHIP TYPE SERIALIZERS ==========

class ExtendedScholarshipTypeSerializer(serializers.ModelSerializer):
    applicable_programmes = serializers.SerializerMethodField()
    applicable_batches = serializers.SerializerMethodField()

    class Meta:
        model = ExtendedScholarshipType
        fields = [
            'id', 'name', 'category', 'description', 'amount', 'frequency',
            'eligibility_criteria', 'max_backlogs', 'applicable_categories',
            'minimum_cgpa', 'maximum_income', 'applicable_programmes',
            'applicable_batches', 'is_active', 'created_at'
        ]

    def get_applicable_programmes(self, obj):
        return list(obj.applicable_programmes.values('id', 'name', 'category'))

    def get_applicable_batches(self, obj):
        return list(obj.applicable_batches.values('id', 'name', 'year'))


class ExtendedScholarshipTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedScholarshipType
        fields = [
            'name', 'category', 'description', 'amount', 'frequency',
            'eligibility_criteria', 'max_backlogs', 'applicable_categories',
            'minimum_cgpa', 'maximum_income', 'applicable_programmes',
            'applicable_batches', 'is_active'
        ]


# ========== SCHOLARSHIP APPLICATION SERIALIZERS ==========

class ScholarshipApplicationReadSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id.id', read_only=True)
    student_name = serializers.CharField(source='student.id.user.username', read_only=True)
    scholarship_name = serializers.CharField(source='scholarship_type.name', read_only=True)
    scholarship_category = serializers.CharField(source='scholarship_type.category', read_only=True)
    amount = serializers.DecimalField(source='scholarship_type.amount', max_digits=10, decimal_places=2, read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ScholarshipApplication
        fields = [
            'id', 'student_id', 'student_name', 'scholarship_name', 'scholarship_category',
            'academic_year', 'semester', 'category_at_application', 'application_date',
            'status', 'remarks', 'reviewed_by_name', 'review_date', 'review_remarks',
            'amount', 'amount_approved', 'disbursement_date', 'transaction_reference'
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.user.username
        return None


class ScholarshipApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScholarshipApplication
        fields = ['scholarship_type', 'academic_year', 'semester', 'remarks']

    def validate_academic_year(self, value):
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError("Academic year must be in format YYYY-YY (e.g. 2024-25)")
        return value

    def validate_semester(self, value):
        if not (1 <= value <= 12):
            raise serializers.ValidationError("Semester must be between 1 and 12.")
        return value


class ScholarshipApplicationApproveSerializer(serializers.Serializer):
    STATUS_CHOICES = ['UNDER_REVIEW', 'APPROVED', 'REJECTED', 'DISBURSED']
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    review_remarks = serializers.CharField(allow_blank=True, required=False, default='')
    amount_approved = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    transaction_reference = serializers.CharField(max_length=100, allow_blank=True, required=False, default='')


# ========== AWARD (GENERAL) SERIALIZERS ==========

class AwardDetailSerializer(serializers.ModelSerializer):
    applicable_programmes = serializers.SerializerMethodField()
    recipient_count = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = [
            'id', 'name', 'category', 'description', 'criteria',
            'prize_amount', 'certificate_provided', 'applicable_programmes',
            'is_active', 'created_at', 'recipient_count'
        ]

    def get_applicable_programmes(self, obj):
        return list(obj.applicable_programmes.values('id', 'name', 'category'))

    def get_recipient_count(self, obj):
        return obj.recipients.count()


class AwardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = [
            'name', 'category', 'description', 'criteria',
            'prize_amount', 'certificate_provided', 'applicable_programmes', 'is_active'
        ]


class AwardRecipientSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id.id', read_only=True)
    student_name = serializers.CharField(source='student.id.user.username', read_only=True)
    award_name = serializers.CharField(source='award.name', read_only=True)
    awarded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AwardRecipient
        fields = [
            'id', 'award', 'award_name', 'student_id', 'student_name',
            'academic_year', 'award_date', 'citation',
            'certificate_issued', 'awarded_by_name'
        ]

    def get_awarded_by_name(self, obj):
        if obj.awarded_by:
            return obj.awarded_by.user.username
        return None


class AwardRecipientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardRecipient
        fields = ['award', 'student', 'academic_year', 'award_date', 'citation', 'certificate_issued']

from ..models import McmApplication, SingleParentApplication

class McmApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = McmApplication
        fields = '__all__'
        read_only_fields = ['student', 'submitted_at']

class SingleParentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleParentApplication
        fields = '__all__'
        read_only_fields = ['student', 'submitted_at']

>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
