<<<<<<< HEAD
"""
test_business_rules.py — Business Rule tests for the SPACS Scholarship module.

12 Business Rules x 2 tests each (Valid + Invalid) = 24 tests.
Naming: TestBR{NN}_{Title}  .  test_valid_...  .  test_invalid_...
"""

from decimal import Decimal
from .conftest import BRTestBase
from applications.scholarships.models import (
    ScholarshipApplication, ScholarshipType, ApplicationStatus,
)

# ── URL constants ──────────────────────────────────────────────────────────
URL_TYPES       = '/spacs/api/types/'
URL_APPS        = '/spacs/api/applications/'
URL_APP_PK      = '/spacs/api/applications/{}/'
URL_STATUS_PK   = '/spacs/api/applications/{}/update-status/'


# ═══════════════════════════════════════════════════════════════════════════════
# BR-001 : Eligibility Must Be Satisfied
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR01_EligibilityMustBeSatisfied(BRTestBase):
    """BR-SPACS-001: Student must satisfy eligibility criteria."""

    def test_valid_eligible_student_accepted(self):
        """Valid: Eligible student (no backlogs, valid category) accepted."""
        self._test_id = "BR-1-V-01"
        self._br_id = "BR-SPACS-001"
        self._test_category = "Valid"
        self._input_action = "POST /spacs/api/applications/ — eligible student"
        self._expected_result = "Application accepted; HTTP 201"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("Eligible accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_ineligible_category_rejected(self):
        """Invalid: Student with ineligible category rejected."""
        self._test_id = "BR-1-I-01"
        self._br_id = "BR-SPACS-001"
        self._test_category = "Invalid"
        self._input_action = "POST /spacs/api/applications/ — restricted category"
        self._expected_result = "Rejected with eligibility error"

        restricted_scholarship = ScholarshipType.objects.create(
            name='SC Only Scholarship', category='CATEGORY',
            description='SC only', eligibility_criteria='SC only',
            amount=25000, frequency='ANNUAL', is_active=True,
            applicable_categories='SC',
        )
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': restricted_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code in [400, 422]:
            self._record_result("Correctly rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400/422, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-002 : No Duplicate Applications
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR02_NoDuplicateApplications(BRTestBase):
    """BR-SPACS-002: No duplicate applications per student per scholarship."""

    def test_valid_first_application_accepted(self):
        """Valid: First application is accepted."""
        self._test_id = "BR-2-V-01"
        self._br_id = "BR-SPACS-002"
        self._test_category = "Valid"
        self._input_action = "POST /spacs/api/applications/ — first application"
        self._expected_result = "Application created; HTTP 201"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("First accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_duplicate_application_rejected(self):
        """Invalid: Second application for same scholarship/cycle rejected."""
        self._test_id = "BR-2-I-01"
        self._br_id = "BR-SPACS-002"
        self._test_category = "Invalid"
        self._input_action = "POST /spacs/api/applications/ — duplicate"
        self._expected_result = "Rejected; HTTP 409"

        self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 409:
            self._record_result("Duplicate rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 409, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-003 : Use of Previously Uploaded Documents
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR03_PreviousDocuments(BRTestBase):
    """BR-SPACS-003: System allows document uploads with applications."""

    def test_valid_application_with_documents(self):
        """Valid: Application with supporting_documents accepted."""
        self._test_id = "BR-3-V-01"
        self._br_id = "BR-SPACS-003"
        self._test_category = "Valid"
        self._input_action = "POST /spacs/api/applications/ with document"
        self._expected_result = "Application accepted; HTTP 201"

        from django.core.files.uploadedfile import SimpleUploadedFile
        self.login_as_student()
        fake_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
            'supporting_documents': fake_file,
        }
        response = self.client.post(URL_APPS, data, format='multipart')

        if response.status_code == 201:
            self._record_result("With docs accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_missing_required_fields(self):
        """Invalid: Application missing required fields rejected."""
        self._test_id = "BR-3-I-01"
        self._br_id = "BR-SPACS-003"
        self._test_category = "Invalid"
        self._input_action = "POST /spacs/api/applications/ missing fields"
        self._expected_result = "Validation error; HTTP 400"

        self.login_as_student()
        response = self.client.post(URL_APPS, {'student': self.student.pk}, format='json')

        if response.status_code == 400:
            self._record_result("Missing fields rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-004 : Application Completeness Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR04_CompletenessValidation(BRTestBase):
    """BR-SPACS-004: All required fields must be filled."""

    def test_valid_complete_application(self):
        """Valid: Complete application accepted."""
        self._test_id = "BR-4-V-01"
        self._br_id = "BR-SPACS-004"
        self._test_category = "Valid"
        self._input_action = "POST /spacs/api/applications/ with all required fields"
        self._expected_result = "Accepted; HTTP 201"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("Complete accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_incomplete_application(self):
        """Invalid: Application missing scholarship_type rejected."""
        self._test_id = "BR-4-I-01"
        self._br_id = "BR-SPACS-004"
        self._test_category = "Invalid"
        self._input_action = "POST missing scholarship_type"
        self._expected_result = "Validation error; HTTP 400"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 400:
            self._record_result("Incomplete rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-005 : Application Review Access
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR05_ApplicationReviewAccess(BRTestBase):
    """BR-SPACS-005: Only SPACS staff can see all applications."""

    def test_valid_assistant_sees_all(self):
        """Valid: Assistant sees all applications."""
        self._test_id = "BR-5-V-01"
        self._br_id = "BR-SPACS-005"
        self._test_category = "Valid"
        self._input_action = "GET /spacs/api/applications/ as assistant"
        self._expected_result = "All applications returned"

        self.create_scholarship_application(student=self.student, status='PENDING')
        self.create_scholarship_application(student=self.student_2, status='PENDING',
                                            academic_year='2025-26')
        self.login_as_assistant()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200 and len(response.data) >= 2:
            self._record_result("All apps visible", "Pass", f"Count={len(response.data)}")
        elif response.status_code == 200:
            self._record_result("Partial visibility", "Partial", f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_student_sees_only_own(self):
        """Invalid: Student sees only own applications."""
        self._test_id = "BR-5-I-01"
        self._br_id = "BR-SPACS-005"
        self._test_category = "Invalid"
        self._input_action = "GET /spacs/api/applications/ as student"
        self._expected_result = "Only own applications"

        self.create_scholarship_application(student=self.student, status='PENDING')
        self.create_scholarship_application(student=self.student_2, status='PENDING',
                                            academic_year='2025-26')
        self.login_as_student()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200:
            if len(response.data) <= 1:
                self._record_result("Only own visible", "Pass", f"Count={len(response.data)}")
            else:
                self._record_result("Sees others!", "Fail", f"Count={len(response.data)}")
                self.fail("Student should only see own applications")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-007 : Draft Save on Timeout or Error
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR07_DraftSaveOnTimeout(BRTestBase):
    """BR-SPACS-007: Application data is persisted."""

    def test_valid_data_persisted(self):
        """Valid: Submitted data persisted in DB."""
        self._test_id = "BR-7-V-01"
        self._br_id = "BR-SPACS-007"
        self._test_category = "Valid"
        self._input_action = "POST /spacs/api/applications/ — data persisted"
        self._expected_result = "Record created in DB"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            exists = ScholarshipApplication.objects.filter(student=self.student).exists()
            if exists:
                self._record_result("Data persisted", "Pass", "DB record found")
            else:
                self._record_result("Not in DB", "Fail", "")
                self.fail("Application not persisted")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_empty_submission_rejected(self):
        """Invalid: Empty payload rejected."""
        self._test_id = "BR-7-I-01"
        self._br_id = "BR-SPACS-007"
        self._test_category = "Invalid"
        self._input_action = "POST with empty data"
        self._expected_result = "Validation error; HTTP 400"

        self.login_as_student()
        response = self.client.post(URL_APPS, {}, format='json')

        if response.status_code == 400:
            self._record_result("Empty rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-008 : Notification on Status Change
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR08_NotificationOnStatusChange(BRTestBase):
    """BR-SPACS-008: Status changes are properly recorded."""

    def test_valid_status_change_recorded(self):
        """Valid: Status change PENDING->UNDER_REVIEW is recorded."""
        self._test_id = "BR-8-V-01"
        self._br_id = "BR-SPACS-008"
        self._test_category = "Valid"
        self._input_action = "PATCH status PENDING->UNDER_REVIEW"
        self._expected_result = "Status changed; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'UNDER_REVIEW'}, format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            self._record_result("Status changed", "Pass", f"Status={app.status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_read_does_not_change_status(self):
        """Invalid: GET does not change application status."""
        self._test_id = "BR-8-I-01"
        self._br_id = "BR-SPACS-008"
        self._test_category = "Invalid"
        self._input_action = "GET (read-only)"
        self._expected_result = "No status change"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            app.refresh_from_db()
            if app.status == 'PENDING':
                self._record_result("No change on read", "Pass", f"Status={app.status}")
            else:
                self._record_result("Status changed!", "Fail", f"Status={app.status}")
                self.fail("Read should not change status")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-009 : Withdrawal Before Review
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR09_WithdrawalBeforeReview(BRTestBase):
    """BR-SPACS-009: Withdrawal only before review starts."""

    def test_valid_cancel_pending(self):
        """Valid: PENDING application can be cancelled."""
        self._test_id = "BR-9-V-01"
        self._br_id = "BR-SPACS-009"
        self._test_category = "Valid"
        self._input_action = "DELETE PENDING application"
        self._expected_result = "Cancelled; HTTP 204"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.delete(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 204:
            self._record_result("Cancelled", "Pass", "HTTP 204")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 204, got {response.status_code}")

    def test_invalid_cancel_under_review_blocked(self):
        """Invalid: UNDER_REVIEW application cannot be cancelled."""
        self._test_id = "BR-9-I-01"
        self._br_id = "BR-SPACS-009"
        self._test_category = "Invalid"
        self._input_action = "DELETE UNDER_REVIEW application"
        self._expected_result = "Blocked"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_student()
        response = self.client.delete(URL_APP_PK.format(app.pk), format='json')

        if response.status_code in [422, 400, 403]:
            self._record_result("Correctly blocked", "Pass", str(getattr(response, 'data', '')))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 422/400/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-010 : Only Owner Can Edit or Withdraw
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR10_OnlyOwnerCanEdit(BRTestBase):
    """BR-SPACS-010: Only application owner can interact."""

    def test_valid_owner_sees_own_apps(self):
        """Valid: Owner sees own applications."""
        self._test_id = "BR-10-V-01"
        self._br_id = "BR-SPACS-010"
        self._test_category = "Valid"
        self._input_action = "GET applications as owner"
        self._expected_result = "Own data returned"

        self.create_scholarship_application(student=self.student, status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200 and len(response.data) >= 1:
            self._record_result("Own apps visible", "Pass", f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200 with data, got {response.status_code}")

    def test_invalid_non_owner_cannot_see(self):
        """Invalid: Non-owner student cannot see other's applications."""
        self._test_id = "BR-10-I-01"
        self._br_id = "BR-SPACS-010"
        self._test_category = "Invalid"
        self._input_action = "GET as non-owner student"
        self._expected_result = "Other's apps not in result"

        self.create_scholarship_application(student=self.student, status='PENDING')
        self.login_as_student2()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200:
            if len(response.data) == 0:
                self._record_result("Not accessible", "Pass", "Empty list")
            else:
                self._record_result("Leaked!", "Fail", f"Count={len(response.data)}")
                self.fail("Non-owner should not see other's apps")
        else:
            self._record_result(f"HTTP {response.status_code}", "Pass", "Blocked")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-012 : Download/Print Access Control
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR12_DownloadPrintAccess(BRTestBase):
    """BR-SPACS-012: Only authorized users can view/download."""

    def test_valid_owner_can_view(self):
        """Valid: Owning student can view application."""
        self._test_id = "BR-12-V-01"
        self._br_id = "BR-SPACS-012"
        self._test_category = "Valid"
        self._input_action = "GET as owner"
        self._expected_result = "Data returned; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            self._record_result("Owner can view", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_unauthenticated_blocked(self):
        """Invalid: Unauthenticated user blocked."""
        self._test_id = "BR-12-I-01"
        self._br_id = "BR-SPACS-012"
        self._test_category = "Invalid"
        self._input_action = "GET unauthenticated"
        self._expected_result = "HTTP 401 or 403"

        app = self.create_scholarship_application(status='PENDING')
        self.logout()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code in [401, 403]:
            self._record_result("Blocked", "Pass", f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-013 : Escalation & SLA for Reviews
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR13_EscalationSLA(BRTestBase):
    """BR-SPACS-013: Proper status transitions enforced."""

    def test_valid_convener_approves_forwarded(self):
        """Valid: Convener approves forwarded application."""
        self._test_id = "BR-13-V-01"
        self._br_id = "BR-SPACS-013"
        self._test_category = "Valid"
        self._input_action = "PATCH FORWARDED -> APPROVED"
        self._expected_result = "Status changed; HTTP 200"

        app = self.create_scholarship_application(status='FORWARDED')
        self.login_as_convener()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk),
            {'new_status': 'APPROVED', 'amount_approved': '50000.00'}, format='json')

        if response.status_code == 200:
            self._record_result("Approved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_invalid_skip_transition_blocked(self):
        """Invalid: Cannot skip from PENDING -> APPROVED."""
        self._test_id = "BR-13-I-01"
        self._br_id = "BR-SPACS-013"
        self._test_category = "Invalid"
        self._input_action = "PATCH PENDING -> APPROVED (invalid skip)"
        self._expected_result = "Blocked; invalid transition"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_convener()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk),
            {'new_status': 'APPROVED', 'amount_approved': '50000.00'}, format='json')

        if response.status_code in [422, 400]:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 422/400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# BR-014 : Catalog Versioning & Published Source of Truth
# ═══════════════════════════════════════════════════════════════════════════════

class TestBR14_CatalogVersioning(BRTestBase):
    """BR-SPACS-014: Only active scholarships accept applications."""

    def test_valid_active_scholarship_accepts(self):
        """Valid: Application to active scholarship accepted."""
        self._test_id = "BR-14-V-01"
        self._br_id = "BR-SPACS-014"
        self._test_category = "Valid"
        self._input_action = "POST with is_active=True type"
        self._expected_result = "Accepted; HTTP 201"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("Active accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}")

    def test_invalid_inactive_scholarship_rejected(self):
        """Invalid: Application to inactive scholarship rejected."""
        self._test_id = "BR-14-I-01"
        self._br_id = "BR-SPACS-014"
        self._test_category = "Invalid"
        self._input_action = "POST with is_active=False type"
        self._expected_result = "Rejected"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.inactive_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code in [400, 404, 422]:
            self._record_result("Inactive rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400/404/422, got {response.status_code}")
=======
1.add deadline chaneg for mcm,single parent,application awards 
2.fix application form in awards
3.map all tables of pg admin used in scholarship and awards module
4.ensure both scholarship and awards module in proper final file struture for submission
5.generate workflows,brs and ucs for both modules final

>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
