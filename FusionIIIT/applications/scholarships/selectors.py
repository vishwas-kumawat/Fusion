<<<<<<< HEAD
"""
selectors.py – Award & Scholarship Module
All database READ operations live here. No business logic.
Views and services must call these functions instead of using
.objects directly.
"""

from django.db.models import Count, Q

from applications.academic_information.models import Student
from applications.academic_procedures.models import Dues, FeePayments, course_registration
from applications.online_cms.models import Student_grades
from applications.programme_curriculum.models import Batch, Programme

from .models import (
    Award,
    AwardRecipient,
    MeritList,
    MeritListEntry,
    ScholarshipApplication,
    ScholarshipType,
)


# ─────────────────────────────────────────────
# ScholarshipType Selectors
# ─────────────────────────────────────────────

def get_all_scholarship_types():
    """Return all active scholarship types."""
    return ScholarshipType.objects.filter(is_active=True).prefetch_related(
        "applicable_programmes", "applicable_batches"
    )


def get_scholarship_type_by_id(scholarship_type_id: int):
    """Return a single ScholarshipType or raise DoesNotExist."""
    return ScholarshipType.objects.get(id=scholarship_type_id)


def get_scholarship_types_by_category(category: str):
    """Return active scholarship types filtered by category."""
    return ScholarshipType.objects.filter(is_active=True, category=category)


# ─────────────────────────────────────────────
# ScholarshipApplication Selectors
# ─────────────────────────────────────────────

def get_all_applications():
    """Return all scholarship applications with related data."""
    return ScholarshipApplication.objects.select_related(
        "student", "scholarship_type", "reviewed_by"
    ).all()


def get_applications_for_user(user):
    """Return only the applications belonging to a specific user's student record."""
    return ScholarshipApplication.objects.select_related(
        "student", "scholarship_type", "reviewed_by"
    ).filter(student__id__user=user)


def get_application_by_id(application_id: int):
    """Return a single ScholarshipApplication or raise DoesNotExist."""
    return ScholarshipApplication.objects.select_related(
        "student", "scholarship_type", "reviewed_by"
    ).get(id=application_id)


def get_applications_by_student(student):
    """Return all applications submitted by a student."""
    return ScholarshipApplication.objects.filter(student=student).select_related(
        "scholarship_type"
    )


def get_applications_by_status(status: str):
    """Return all applications with a given status."""
    return ScholarshipApplication.objects.filter(status=status).select_related(
        "student", "scholarship_type"
    )


def get_applications_by_academic_year(academic_year: str):
    """Return all applications for a given academic year."""
    return ScholarshipApplication.objects.filter(academic_year=academic_year).select_related(
        "student", "scholarship_type"
    )


def application_exists(student, scholarship_type, academic_year: str, semester: int) -> bool:
    """Check if a duplicate application exists."""
    return ScholarshipApplication.objects.filter(
        student=student,
        scholarship_type=scholarship_type,
        academic_year=academic_year,
        semester=semester,
    ).exists()


# ─────────────────────────────────────────────
# Award Selectors
# ─────────────────────────────────────────────

def get_all_awards():
    """Return all active awards."""
    return Award.objects.filter(is_active=True).prefetch_related("applicable_programmes")


def get_award_by_id(award_id: int):
    """Return a single Award or raise DoesNotExist."""
    return Award.objects.get(id=award_id)


def get_awards_by_category(category: str):
    """Return active awards filtered by category."""
    return Award.objects.filter(is_active=True, category=category)


# ─────────────────────────────────────────────
# AwardRecipient Selectors
# ─────────────────────────────────────────────

def get_all_award_recipients():
    """Return all award recipient records."""
    return AwardRecipient.objects.select_related("award", "student", "awarded_by").all()


def get_recipients_by_award(award_id: int):
    """Return all recipients for a specific award."""
    return AwardRecipient.objects.filter(award_id=award_id).select_related("student")


def get_awards_for_student(student):
    """Return all awards received by a student."""
    return AwardRecipient.objects.filter(student=student).select_related("award")


def recipient_exists(award, student, academic_year: str) -> bool:
    """Check if this student already received this award in the given year."""
    return AwardRecipient.objects.filter(
        award=award, student=student, academic_year=academic_year
    ).exists()


# ─────────────────────────────────────────────
# MeritList Selectors
# ─────────────────────────────────────────────

def get_merit_list(batch, academic_year: str, semester: int):
    """Return a MeritList for a batch/year/semester or raise DoesNotExist."""
    return MeritList.objects.get(batch=batch, academic_year=academic_year, semester=semester)


def get_merit_list_by_id(merit_list_id: int):
    """Return a single MeritList or raise DoesNotExist."""
    return MeritList.objects.select_related("batch").get(id=merit_list_id)


def get_merit_list_entries(merit_list):
    """Return ordered entries for a MeritList."""
    return MeritListEntry.objects.filter(merit_list=merit_list).select_related("student").order_by("rank")


def merit_list_exists(batch, academic_year: str, semester: int) -> bool:
    """Check if a merit list already exists for this batch/year/semester."""
    return MeritList.objects.filter(
        batch=batch, academic_year=academic_year, semester=semester
    ).exists()


# ─────────────────────────────────────────────
# Cross-Module Eligibility Selectors
# (read-only queries against global / other app tables)
# ─────────────────────────────────────────────

def get_student_by_id(student_id):
    """Return a Student instance or raise DoesNotExist."""
    return Student.objects.select_related("id", "batch_id").get(id=student_id)


def get_students_by_category(category: str, batch=None):
    """Return students filtered by category, optionally scoped to a batch."""
    qs = Student.objects.filter(category=category)
    if batch is not None:
        qs = qs.filter(batch_id=batch)
    return qs.select_related("id", "batch_id")


def get_students_without_backlogs(batch):
    """
    Return students in a batch who have zero backlog registrations.
    Annotates each Student with backlog_count for transparency.
    """
    return (
        Student.objects.filter(batch_id=batch)
        .annotate(
            backlog_count=Count(
                "id__course_registration",
                filter=Q(id__course_registration__registration_type="Backlog"),
            )
        )
        .filter(backlog_count=0)
        .select_related("id", "batch_id")
    )


def get_backlog_count_for_student(student) -> int:
    """Return the number of backlog course registrations for a student."""
    return course_registration.objects.filter(
        student_id=student, registration_type="Backlog"
    ).count()


def get_student_dues(student):
    """Return Dues record for a student or None if not found."""
    return Dues.objects.filter(student_id=student).first()


def get_student_fee_payments(student, semester=None):
    """Return FeePayments queryset for a student, optionally filtered by semester."""
    qs = FeePayments.objects.filter(student_id=student)
    if semester is not None:
        qs = qs.filter(semester_id=semester)
    return qs


def get_verified_grades_for_student(student):
    """Return verified Student_grades records for a student (using roll_no)."""
    roll_no = str(student.id_id)
    return Student_grades.objects.filter(roll_no=roll_no, verified=True)


def get_course_toppers(course_id, grade: str = "A"):
    """Return verified Student_grades for a course filtered by grade."""
    return Student_grades.objects.filter(
        course_id=course_id, grade=grade, verified=True
    )


def get_eligible_students_for_scholarship(scholarship_type):
    """
    Return a queryset of students that pass the basic DB-level filters
    for the given ScholarshipType. Fine-grained eligibility (dues, backlogs)
    is enforced in services.py.
    """
    qs = Student.objects.filter(batch_id__running_batch=True).select_related(
        "id", "batch_id", "batch_id__discipline"
    )

    # Filter by applicable batches if configured
    if scholarship_type.applicable_batches.exists():
        qs = qs.filter(batch_id__in=scholarship_type.applicable_batches.all())

    # Filter by category if configured
    if scholarship_type.applicable_categories:
        valid_cats = [c.strip() for c in scholarship_type.applicable_categories.split(",")]
        qs = qs.filter(category__in=valid_cats)

    return qs
=======
from django.utils import timezone
from applications.academic_information.models import Student
from .models import Award_and_scholarship, Release, Application


def get_student_by_user(user):
    """Safely retrieves the Student record for the authenticated user."""
    if not user or not user.is_authenticated:
        return None

    # User -> ExtraInfo -> Student relation in Fusion data model.
    return Student.objects.select_related(
        "id__user", "id__department", "batch_id__discipline"
    ).filter(id__user=user).first()


def get_active_releases(student_batch: str, student_programme: str):
    """Retrieves scholarship releases that are currently open for a student's demographic."""
    today = timezone.now().date()
    return Release.objects.filter(
        startdate__lte=today,
        enddate__gte=today,
        batch__iexact=student_batch,
        programme__iexact=student_programme,
        notif_visible=True
    ).select_related('award')


def get_student_applications(student_id: str):
    """Retrieves all applications submitted by a specific student."""
    return Application.objects.filter(student__id=student_id).select_related('award')


def get_all_applications_for_convener(status_filter=None):
    """Retrieves applications for the convener, optionally filtered by status."""
    qs = Application.objects.select_related('student', 'award')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return qs


def get_application_by_id(application_id: int):
    """Retrieves a single application by its primary key."""
    return Application.objects.select_related('student', 'award').filter(id=application_id).first()
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
