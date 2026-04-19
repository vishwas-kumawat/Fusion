"""
services.py ΓÇô Award & Scholarship Module
All WRITE operations, business logic, and custom exceptions live here.
Never import services.py from models.py or selectors.py.
"""

from django.utils import timezone

from .models import (
    ApplicationStatus,
    Award,
    AwardRecipient,
    MeritList,
    MeritListEntry,
    ScholarshipApplication,
    ScholarshipType,
)
from .selectors import (
    application_exists,
    get_award_by_id,
    get_backlog_count_for_student,
    get_eligible_students_for_scholarship,
    get_merit_list_entries,
    get_scholarship_type_by_id,
    get_student_by_id,
    get_student_dues,
    merit_list_exists,
    recipient_exists,
)


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Custom Exceptions
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

class ScholarshipNotFound(Exception):
    """Raised when a ScholarshipType does not exist."""


class ApplicationNotFound(Exception):
    """Raised when a ScholarshipApplication does not exist."""


class AwardNotFound(Exception):
    """Raised when an Award does not exist."""


class DuplicateApplicationError(Exception):
    """Raised when a student applies for the same scholarship twice in a semester."""


class EligibilityError(Exception):
    """Raised when a student fails one or more eligibility criteria."""

    def __init__(self, reasons: list):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


class DuplicateAwardError(Exception):
    """Raised when a student is nominated for an award they already received."""


class MeritListAlreadyExists(Exception):
    """Raised when a merit list for this batch/year/semester already exists."""


class InvalidStatusTransition(Exception):
    """Raised when an application status transition is not permitted."""


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Eligibility Check (internal helper)
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

_VALID_TRANSITIONS = {
    ApplicationStatus.PENDING:      [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWAL_REQUESTED],
    ApplicationStatus.UNDER_REVIEW: [ApplicationStatus.FORWARDED, ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWAL_REQUESTED],
    ApplicationStatus.FORWARDED:    [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWAL_REQUESTED],
    ApplicationStatus.WITHDRAWAL_REQUESTED: [ApplicationStatus.WITHDRAWN, ApplicationStatus.PENDING, ApplicationStatus.UNDER_REVIEW],
    ApplicationStatus.APPROVED:     [ApplicationStatus.DISBURSED],
    ApplicationStatus.REJECTED:     [],
    ApplicationStatus.DISBURSED:    [],
    ApplicationStatus.WITHDRAWN:    [],
}


def check_scholarship_eligibility(student, scholarship_type, cpi=None, annual_family_income=None) -> tuple:
    """
    Validate whether a student meets the eligibility criteria for a given
    ScholarshipType.

    Returns:
        (is_eligible, reasons) ΓÇô reasons is empty when eligible.
    """
    reasons = []

    # 0. Custom dynamic checks for CPI and Family Income
    if scholarship_type.cpi_cutoff > 0:
        actual_cpi = cpi if cpi is not None else student.cpi
        if actual_cpi is None or actual_cpi < float(scholarship_type.cpi_cutoff):
            reasons.append(f"Student CPI {actual_cpi or 'N/A'} is less than the required cutoff of {scholarship_type.cpi_cutoff}.")

    if scholarship_type.annual_family_income_limit > 0:
        if annual_family_income is None or annual_family_income > scholarship_type.annual_family_income_limit:
            reasons.append(f"Annual family income {annual_family_income or 'N/A'} exceeds the limit of {scholarship_type.annual_family_income_limit}.")

    # 1. Backlog check
    backlog_count = get_backlog_count_for_student(student)
    if backlog_count > scholarship_type.max_backlogs:
        reasons.append(
            f"Student has {backlog_count} backlog(s); "
            f"maximum allowed is {scholarship_type.max_backlogs}."
        )

    # 2. Category check
    if scholarship_type.applicable_categories:
        valid_cats = [c.strip() for c in scholarship_type.applicable_categories.split(",")]
        if student.category not in valid_cats:
            reasons.append(
                f"Student category '{student.category}' is not eligible for this scholarship "
                f"(eligible: {', '.join(valid_cats)})."
            )

    # 3. Academic dues check
    dues = get_student_dues(student)
    if dues and dues.academic_due > 0:
        reasons.append(
            f"Student has pending academic dues of Γé╣{dues.academic_due}."
        )

    # 4. Active batch check
    if not student.batch_id.running_batch:
        reasons.append("Student's batch is not currently active.")

    return len(reasons) == 0, reasons


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# ScholarshipType Services
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_scholarship_type(
    name: str,
    category: str,
    description: str,
    amount,
    frequency: str,
    eligibility_criteria: str,
    cpi_cutoff=0.0,
    annual_family_income_limit: int=0,
    max_backlogs: int = 0,
    applicable_categories: str = "",
    programme_ids: list = None,
    batch_ids: list = None,
) -> ScholarshipType:
    """Create a new ScholarshipType record."""
    scholarship_type = ScholarshipType.objects.create(
        name=name,
        category=category,
        description=description,
        amount=amount,
        frequency=frequency,
        eligibility_criteria=eligibility_criteria,
        cpi_cutoff=cpi_cutoff,
        annual_family_income_limit=annual_family_income_limit,
        max_backlogs=max_backlogs,
        applicable_categories=applicable_categories,
    )

    if programme_ids:
        scholarship_type.applicable_programmes.set(programme_ids)
    if batch_ids:
        scholarship_type.applicable_batches.set(batch_ids)

    return scholarship_type


def update_scholarship_type(scholarship_type_id: int, **kwargs) -> ScholarshipType:
    """Update fields on an existing ScholarshipType."""
    try:
        scholarship_type = get_scholarship_type_by_id(scholarship_type_id)
    except ScholarshipType.DoesNotExist:
        raise ScholarshipNotFound(f"ScholarshipType with id={scholarship_type_id} not found.")

    programme_ids = kwargs.pop("programme_ids", None)
    batch_ids = kwargs.pop("batch_ids", None)

    for field, value in kwargs.items():
        setattr(scholarship_type, field, value)
    scholarship_type.save()

    if programme_ids is not None:
        scholarship_type.applicable_programmes.set(programme_ids)
    if batch_ids is not None:
        scholarship_type.applicable_batches.set(batch_ids)

    return scholarship_type


def deactivate_scholarship_type(scholarship_type_id: int) -> ScholarshipType:
    """Soft-delete a scholarship type by marking it inactive."""
    try:
        scholarship_type = get_scholarship_type_by_id(scholarship_type_id)
    except ScholarshipType.DoesNotExist:
        raise ScholarshipNotFound(f"ScholarshipType with id={scholarship_type_id} not found.")

    scholarship_type.is_active = False
    scholarship_type.save(update_fields=["is_active"])
    return scholarship_type


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# ScholarshipApplication Services
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_scholarship_application(
    student_id,
    scholarship_type_id: int,
    academic_year: str,
    semester: int,
    remarks: str = "",
    document=None,
    category: str = "",
    annual_family_income: int = None,
    cpi: float = None,
    status: str = "PENDING",
) -> ScholarshipApplication:
    """
    Create a scholarship application after verifying eligibility.

    Raises:
        ScholarshipNotFound: if the scholarship type does not exist.
        DuplicateApplicationError: if the student already applied.
        EligibilityError: if the student fails eligibility checks.
    """
    from datetime import date

    try:
        scholarship_type = get_scholarship_type_by_id(scholarship_type_id)
    except ScholarshipType.DoesNotExist:
        raise ScholarshipNotFound(f"ScholarshipType id={scholarship_type_id} not found.")

    if scholarship_type.deadline and scholarship_type.deadline < date.today():
        raise EligibilityError([f"The deadline for {scholarship_type.name} has passed ({scholarship_type.deadline})."])

    student = get_student_by_id(student_id)

    if category:
        student.category = category
        student.save(update_fields=["category"])

    if application_exists(student, scholarship_type, academic_year, semester):
        raise DuplicateApplicationError(
            f"An application for '{scholarship_type.name}' in {academic_year} "
            f"Sem-{semester} already exists."
        )

    from .models import ScholarshipApplication
    current_applications_count = ScholarshipApplication.objects.filter(
        student=student,
        academic_year=academic_year,
        semester=semester
    ).count()

    if current_applications_count >= 2:
        raise DuplicateApplicationError(
            f"You have already applied for the maximum allowed limit of 2 scholarships at one time ({academic_year} Sem-{semester})."
        )

    is_eligible, reasons = check_scholarship_eligibility(student, scholarship_type, cpi, annual_family_income)
    if not is_eligible:
        raise EligibilityError(reasons)

    application = ScholarshipApplication.objects.create(
        student=student,
        scholarship_type=scholarship_type,
        academic_year=academic_year,
        semester=semester,
        category_at_application=student.category,
        annual_family_income=annual_family_income,
        cpi=cpi,
        remarks=remarks,
        supporting_documents=document,
        status=status,
    )
    
    if document:
        application.supporting_documents = document
        application.save(update_fields=["supporting_documents"])

    return application


def update_application_status(
    application_id: int,
    new_status: str,
    reviewer,
    review_remarks: str = "",
    amount_approved=None,
) -> ScholarshipApplication:
    """
    Transition an application to a new status.

    Validates allowed status transitions and records reviewer metadata.

    Raises:
        ApplicationNotFound: if the application does not exist.
        InvalidStatusTransition: if the transition is not permitted.
    """
    try:
        application = ScholarshipApplication.objects.get(id=application_id)
    except ScholarshipApplication.DoesNotExist:
        raise ApplicationNotFound(f"Application id={application_id} not found.")

    allowed = _VALID_TRANSITIONS.get(application.status, [])
    if new_status not in allowed:
        raise InvalidStatusTransition(
            f"Cannot transition from '{application.status}' to '{new_status}'."
        )

    application.status = new_status
    application.reviewed_by = reviewer
    application.review_date = timezone.now()

    if review_remarks:
        application.review_remarks = review_remarks

    if amount_approved is not None:
        application.amount_approved = amount_approved

    if new_status == ApplicationStatus.DISBURSED:
        application.disbursement_date = timezone.now()

    application.save()
    return application


def cancel_scholarship_application(application_id: int) -> None:
    """
    Request a withdrawal for a scholarship application.

    Raises:
        ApplicationNotFound: if the application does not exist.
        InvalidStatusTransition: if withdrawal not allowed.
    """
    try:
        application = ScholarshipApplication.objects.get(id=application_id)
    except ScholarshipApplication.DoesNotExist:
        raise ApplicationNotFound(f"Application id={application_id} not found.")

    allowed_statuses = [ApplicationStatus.DRAFT, ApplicationStatus.PENDING, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.FORWARDED]
    if application.status not in allowed_statuses:
        raise InvalidStatusTransition(
            f"Cannot request withdrawal from current status: {application.status}."
        )

    application.status = ApplicationStatus.WITHDRAWAL_REQUESTED
    application.save()


def amend_scholarship_application(
    application_id: int, 
    student, 
    document=None,
    **kwargs
) -> ScholarshipApplication:
    """
    Allow a student to modify their application when its status is PENDING.
    """
    try:
        application = ScholarshipApplication.objects.get(id=application_id)
    except ScholarshipApplication.DoesNotExist:
        raise ApplicationNotFound(f"Application id={application_id} not found.")

    if application.student != student:
        raise InvalidStatusTransition("You are not authorized to modify this application.")

    if application.status not in [ApplicationStatus.PENDING, ApplicationStatus.DRAFT]:
        raise InvalidStatusTransition(
            f"Cannot modify application when status is '{application.status}'. Only 'PENDING' or 'DRAFT' applications can be modified."
        )

    status_update = kwargs.pop("status", None)
    if status_update in [ApplicationStatus.PENDING, ApplicationStatus.DRAFT]:
        application.status = status_update

    for field, value in kwargs.items():
        # Keep documents handling, etc. Only allowed fields should be passed from view.
        if value is not None and hasattr(application, field):
            # Convert empty strings to None for numerical fields if necessary
            if value == "" and field in ["cpi", "annual_family_income"]:
                value = None
            setattr(application, field, value)

    if document is not None:
        application.supporting_documents = document

    application.save()
    return application


def record_disbursement(application_id: int, transaction_reference: str) -> ScholarshipApplication:
    """
    Mark an approved application as DISBURSED with a transaction reference.

    Raises:
        ApplicationNotFound: if the application does not exist.
        InvalidStatusTransition: if the application is not in APPROVED state.
    """
    try:
        application = ScholarshipApplication.objects.get(id=application_id)
    except ScholarshipApplication.DoesNotExist:
        raise ApplicationNotFound(f"Application id={application_id} not found.")

    if application.status != ApplicationStatus.APPROVED:
        raise InvalidStatusTransition(
            "Only APPROVED applications can be marked as DISBURSED."
        )

    application.status = ApplicationStatus.DISBURSED
    application.disbursement_date = timezone.now()
    application.transaction_reference = transaction_reference
    application.save(update_fields=["status", "disbursement_date", "transaction_reference"])
    return application


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Award Services
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def create_award(
    name: str,
    category: str,
    description: str,
    criteria: str,
    prize_amount=None,
    certificate_provided: bool = True,
    programme_ids: list = None,
) -> Award:
    """Create a new Award definition."""
    award = Award.objects.create(
        name=name,
        category=category,
        description=description,
        criteria=criteria,
        prize_amount=prize_amount,
        certificate_provided=certificate_provided,
    )
    if programme_ids:
        award.applicable_programmes.set(programme_ids)
    return award


def nominate_award_recipient(
    award_id: int,
    student_id,
    academic_year: str,
    award_date,
    awarded_by,
    citation: str = "",
) -> AwardRecipient:
    """
    Nominate a student as a recipient for an award.

    Raises:
        AwardNotFound: if the award does not exist.
        DuplicateAwardError: if the student already received this award in the same year.
    """
    try:
        award = get_award_by_id(award_id)
    except Award.DoesNotExist:
        raise AwardNotFound(f"Award id={award_id} not found.")

    student = get_student_by_id(student_id)

    if recipient_exists(award, student, academic_year):
        raise DuplicateAwardError(
            f"Student has already received '{award.name}' in {academic_year}."
        )

    return AwardRecipient.objects.create(
        award=award,
        student=student,
        academic_year=academic_year,
        award_date=award_date,
        citation=citation,
        awarded_by=awarded_by,
    )


def mark_certificate_issued(recipient_id: int) -> AwardRecipient:
    """Mark an award recipient's certificate as issued."""
    try:
        recipient = AwardRecipient.objects.get(id=recipient_id)
    except AwardRecipient.DoesNotExist:
        raise AwardNotFound(f"AwardRecipient id={recipient_id} not found.")

    recipient.certificate_issued = True
    recipient.save(update_fields=["certificate_issued"])
    return recipient


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# MeritList Services
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def generate_merit_list(batch, academic_year: str, semester: int) -> MeritList:
    """
    Generate a ranked merit list for a batch in a given academic year and semester.
    Students are pulled from the eligible queryset and ranked by their roll number
    as a placeholder; the ranking logic should be extended to use CGPA when available.

    Raises:
        MeritListAlreadyExists: if a list for this batch/year/semester already exists.
    """
    if merit_list_exists(batch, academic_year, semester):
        raise MeritListAlreadyExists(
            f"Merit list for batch '{batch}' in {academic_year} Sem-{semester} already exists."
        )

    students = (
        get_eligible_students_for_scholarship(
            # We pass a dummy type with no restrictions to get all active-batch students.
            # Actual ranking criteria (CGPA) should be injected here.
            type("_Dummy", (), {
                "applicable_batches": batch.__class__.objects.filter(id=batch.id),
                "applicable_categories": "",
            })()
        )
        .filter(batch_id=batch)
        .order_by("id")         # Default order; extend with CGPA annotation when CMS data is ready.
    )

    merit_list = MeritList.objects.create(
        batch=batch,
        academic_year=academic_year,
        semester=semester,
    )

    entries = [
        MeritListEntry(merit_list=merit_list, student=student, rank=rank)
        for rank, student in enumerate(students, start=1)
    ]
    MeritListEntry.objects.bulk_create(entries)

    return merit_list


def delete_merit_list(merit_list_id: int) -> None:
    """Delete a previously generated merit list and its entries."""
    try:
        merit_list = MeritList.objects.get(id=merit_list_id)
    except MeritList.DoesNotExist:
        raise AwardNotFound(f"MeritList id={merit_list_id} not found.")
    merit_list.delete()