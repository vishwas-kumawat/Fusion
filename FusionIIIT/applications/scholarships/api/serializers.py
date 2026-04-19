"""
api/serializers.py ΓÇô Award & Scholarship Module
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


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# ScholarshipType Serializers
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# ScholarshipApplication Serializers
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Award Serializers
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# MeritList Serializers
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

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