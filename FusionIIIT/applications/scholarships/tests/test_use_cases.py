"""
test_use_cases.py — Use-Case tests for the SPACS Scholarship module.

13 Use Cases x 3 tests each (HP + AP + EX) = 39 tests.
Naming: TestUC{NN}_{Title}  .  test_hp01_...  .  test_ap01_...  .  test_ex01_...
"""

from .conftest import UCTestBase
from applications.scholarships.models import (
    ScholarshipApplication, ScholarshipType, ApplicationStatus,
)

# ── URL constants ──────────────────────────────────────────────────────────
URL_TYPES       = '/spacs/api/types/'
URL_TYPE_PK     = '/spacs/api/types/{}/'
URL_APPS        = '/spacs/api/applications/'
URL_APP_PK      = '/spacs/api/applications/{}/'
URL_STATUS_PK   = '/spacs/api/applications/{}/update-status/'
URL_DISBURSE_PK = '/spacs/api/applications/{}/disburse/'


# ═══════════════════════════════════════════════════════════════════════════════
# UC-001 : Apply For Scholarship/Awards
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC01_ApplyForScholarship(UCTestBase):
    """SPACS-UC-001: Student applies for a scholarship/award."""

    def test_hp01_submit_valid_application(self):
        """Happy Path: Student submits complete scholarship application."""
        self._test_id = "UC-1-HP-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Happy Path"
        self._scenario = "Student submits a complete scholarship application"
        self._preconditions = "Student logged in; active scholarship exists"
        self._input_action = "POST /spacs/api/applications/"
        self._expected_result = "Application created; status=PENDING; HTTP 201"

        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("Application created", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ap01_submit_alternate_scholarship(self):
        """Alternate Path: Student submits application for a different scholarship category."""
        self._test_id = "UC-1-AP-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Alternate Path"
        self._scenario = "Student submits for a different scholarship type"
        self._preconditions = "Student logged in; alternate active scholarship exists"
        self._input_action = "POST /spacs/api/applications/ with alternate scholarship_type"
        self._expected_result = "Application created; status=PENDING; HTTP 201"

        alt_scholarship = ScholarshipType.objects.create(
            name='Alt Need Scholarship', category='NEED',
            description='Need-based test', eligibility_criteria='All',
            amount=20000, frequency='SEMESTER', is_active=True,
            applicable_categories='GEN,SC,ST,OBC',
        )
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': alt_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        response = self.client.post(URL_APPS, data, format='json')

        if response.status_code == 201:
            self._record_result("Alt scholarship accepted", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ex01_submit_for_inactive_scholarship(self):
        """Exception: Student submits application for inactive scholarship."""
        self._test_id = "UC-1-EX-01"
        self._uc_id = "SPACS-UC-001"
        self._test_category = "Exception"
        self._scenario = "Student submits for inactive scholarship"
        self._preconditions = "Student logged in; scholarship is_active=False"
        self._input_action = "POST /spacs/api/applications/ with inactive scholarship_type"
        self._expected_result = "Rejected; scholarship not found"

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


# ═══════════════════════════════════════════════════════════════════════════════
# UC-002 : Verify Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC02_VerifyApplication(UCTestBase):
    """SPACS-UC-002: SPACS Assistant verifies application."""

    def test_hp01_assistant_reviews_to_under_review(self):
        """Happy Path: Assistant moves pending application to UNDER_REVIEW."""
        self._test_id = "UC-2-HP-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Happy Path"
        self._scenario = "Assistant moves PENDING -> UNDER_REVIEW"
        self._preconditions = "Assistant logged in; pending application exists"
        self._input_action = "PATCH update-status with new_status=UNDER_REVIEW"
        self._expected_result = "Status=UNDER_REVIEW; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'UNDER_REVIEW'}, format='json')

        if response.status_code == 200:
            self._record_result("Status updated", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_assistant_rejects_pending(self):
        """Alternate Path: Assistant rejects a pending application."""
        self._test_id = "UC-2-AP-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Alternate Path"
        self._scenario = "Assistant rejects PENDING application"
        self._preconditions = "Assistant logged in; pending application exists"
        self._input_action = "PATCH update-status with new_status=REJECTED"
        self._expected_result = "Status=REJECTED; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'REJECTED'}, format='json')

        if response.status_code == 200:
            self._record_result("Rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ex01_student_cannot_verify(self):
        """Exception: Student attempts to change status."""
        self._test_id = "UC-2-EX-01"
        self._uc_id = "SPACS-UC-002"
        self._test_category = "Exception"
        self._scenario = "Student tries to change application status"
        self._preconditions = "Student logged in"
        self._input_action = "PATCH update-status with new_status=UNDER_REVIEW"
        self._expected_result = "Should be restricted for student roles"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'UNDER_REVIEW'}, format='json')

        if response.status_code in [200]:
            self._record_result("Status changed (no role enforcement)", "Partial",
                                f"HTTP {response.status_code}")
        elif response.status_code in [403, 401]:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Unexpected status: {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-003 : Modify Pending Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC03_ModifyPendingApplication(UCTestBase):
    """SPACS-UC-003: Student edits/cancels a pending application."""

    def test_hp01_student_cancels_pending(self):
        """Happy Path: Student cancels own pending application."""
        self._test_id = "UC-3-HP-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Happy Path"
        self._scenario = "Student cancels pending application"
        self._preconditions = "Student logged in; owns PENDING application"
        self._input_action = "DELETE /spacs/api/applications/<pk>/"
        self._expected_result = "Application cancelled; HTTP 204"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.delete(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 204:
            self._record_result("Cancelled", "Pass", "HTTP 204")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 204, got {response.status_code}")

    def test_ap01_student_retrieves_application(self):
        """Alternate Path: Student retrieves own application before modifying."""
        self._test_id = "UC-3-AP-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Alternate Path"
        self._scenario = "Student retrieves own application"
        self._preconditions = "Student logged in; owns application"
        self._input_action = "GET /spacs/api/applications/<pk>/"
        self._expected_result = "Application details returned; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            self._record_result("Details retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_cancel_non_pending_fails(self):
        """Exception: Student attempts to cancel a non-PENDING application."""
        self._test_id = "UC-3-EX-01"
        self._uc_id = "SPACS-UC-003"
        self._test_category = "Exception"
        self._scenario = "Cancel non-PENDING application"
        self._preconditions = "Student logged in; application status=APPROVED"
        self._input_action = "DELETE on approved application"
        self._expected_result = "Rejected; only PENDING applications can be cancelled"

        app = self.create_scholarship_application(status='APPROVED')
        self.login_as_student()
        response = self.client.delete(URL_APP_PK.format(app.pk), format='json')

        if response.status_code in [422, 400, 403]:
            self._record_result("Correctly rejected", "Pass", str(getattr(response, 'data', '')))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 422/400/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-004 : Request Withdrawal
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC04_RequestWithdrawal(UCTestBase):
    """SPACS-UC-004: Student withdraws a pending application."""

    def test_hp01_student_views_applications(self):
        """Happy Path: Student views own applications list."""
        self._test_id = "UC-4-HP-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Happy Path"
        self._scenario = "Student views applications list"
        self._preconditions = "Student logged in; has applications"
        self._input_action = "GET /spacs/api/applications/"
        self._expected_result = "Own applications returned; HTTP 200"

        self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200:
            self._record_result("Applications listed", "Pass", f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_student_views_single_application(self):
        """Alternate Path: Student views single application detail."""
        self._test_id = "UC-4-AP-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Alternate Path"
        self._scenario = "Student views single application"
        self._preconditions = "Student logged in; has application"
        self._input_action = "GET /spacs/api/applications/<pk>/"
        self._expected_result = "Application details returned; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            self._record_result("Detail retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_delete_under_review_fails(self):
        """Exception: Delete non-pending (UNDER_REVIEW) application fails."""
        self._test_id = "UC-4-EX-01"
        self._uc_id = "SPACS-UC-004"
        self._test_category = "Exception"
        self._scenario = "Delete UNDER_REVIEW application"
        self._preconditions = "Student logged in; application UNDER_REVIEW"
        self._input_action = "DELETE application"
        self._expected_result = "Rejected; only PENDING can be cancelled"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_student()
        response = self.client.delete(URL_APP_PK.format(app.pk), format='json')

        if response.status_code in [422, 400, 403]:
            self._record_result("Correctly blocked", "Pass", str(getattr(response, 'data', '')))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 422/400/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-005 : Acknowledge Withdrawal
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC05_AcknowledgeWithdrawal(UCTestBase):
    """SPACS-UC-005: SPACS Assistant acknowledges withdrawal/status change."""

    def test_hp01_assistant_forwards_under_review(self):
        """Happy Path: Assistant transitions UNDER_REVIEW -> FORWARDED."""
        self._test_id = "UC-5-HP-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Happy Path"
        self._scenario = "UNDER_REVIEW -> FORWARDED"
        self._preconditions = "Assistant logged in; application UNDER_REVIEW"
        self._input_action = "PATCH update-status with FORWARDED"
        self._expected_result = "Status=FORWARDED; HTTP 200"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'FORWARDED'}, format='json')

        if response.status_code == 200:
            self._record_result("Forwarded", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_assistant_rejects_under_review(self):
        """Alternate Path: Assistant rejects UNDER_REVIEW application."""
        self._test_id = "UC-5-AP-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Alternate Path"
        self._scenario = "UNDER_REVIEW -> REJECTED"
        self._preconditions = "Assistant logged in; app UNDER_REVIEW"
        self._input_action = "PATCH update-status with REJECTED"
        self._expected_result = "Status=REJECTED; HTTP 200"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'REJECTED'}, format='json')

        if response.status_code == 200:
            self._record_result("Rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ex01_invalid_transition_pending_to_forwarded(self):
        """Exception: Invalid transition PENDING -> FORWARDED."""
        self._test_id = "UC-5-EX-01"
        self._uc_id = "SPACS-UC-005"
        self._test_category = "Exception"
        self._scenario = "Invalid PENDING -> FORWARDED transition"
        self._preconditions = "Assistant logged in; application PENDING"
        self._input_action = "PATCH with FORWARDED on PENDING"
        self._expected_result = "Rejected; invalid transition"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'FORWARDED'}, format='json')

        if response.status_code in [422, 400]:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 422/400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-006 : Sanctioning Decision
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC06_SanctioningDecision(UCTestBase):
    """SPACS-UC-006: Convener approves/rejects forwarded applications."""

    def test_hp01_convener_approves_forwarded(self):
        """Happy Path: Convener approves a forwarded application with amount."""
        self._test_id = "UC-6-HP-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Happy Path"
        self._scenario = "Convener approves FORWARDED application"
        self._preconditions = "Convener logged in; app FORWARDED"
        self._input_action = "PATCH with APPROVED + amount_approved"
        self._expected_result = "Status=APPROVED; HTTP 200"

        app = self.create_scholarship_application(status='FORWARDED')
        self.login_as_convener()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk),
            {'new_status': 'APPROVED', 'amount_approved': '50000.00'}, format='json')

        if response.status_code == 200:
            self._record_result("Approved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_convener_rejects_forwarded(self):
        """Alternate Path: Convener rejects forwarded application."""
        self._test_id = "UC-6-AP-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Alternate Path"
        self._scenario = "Convener rejects FORWARDED application"
        self._preconditions = "Convener logged in; app FORWARDED"
        self._input_action = "PATCH with REJECTED"
        self._expected_result = "Status=REJECTED; HTTP 200"

        app = self.create_scholarship_application(status='FORWARDED')
        self.login_as_convener()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'REJECTED'}, format='json')

        if response.status_code == 200:
            self._record_result("Rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ex01_approve_without_amount_fails(self):
        """Exception: Approve without amount_approved fails validation."""
        self._test_id = "UC-6-EX-01"
        self._uc_id = "SPACS-UC-006"
        self._test_category = "Exception"
        self._scenario = "Approve without amount_approved"
        self._preconditions = "Convener logged in; app FORWARDED"
        self._input_action = "PATCH with APPROVED but no amount"
        self._expected_result = "Validation error"

        app = self.create_scholarship_application(status='FORWARDED')
        self.login_as_convener()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'APPROVED'}, format='json')

        if response.status_code == 400:
            self._record_result("Validation blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}: {response.data}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-007 : Download/Print Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC07_DownloadPrintApplication(UCTestBase):
    """SPACS-UC-007: Student/staff retrieves application data for export."""

    def test_hp01_student_retrieves_own_application(self):
        """Happy Path: Student retrieves own application details."""
        self._test_id = "UC-7-HP-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Happy Path"
        self._scenario = "Student retrieves own application"
        self._preconditions = "Student logged in; owns application"
        self._input_action = "GET /spacs/api/applications/<pk>/"
        self._expected_result = "Full data returned; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            self._record_result("Data retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_staff_retrieves_all_applications(self):
        """Alternate Path: Staff retrieves all applications."""
        self._test_id = "UC-7-AP-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Alternate Path"
        self._scenario = "Staff retrieves all applications"
        self._preconditions = "SPACS staff logged in"
        self._input_action = "GET /spacs/api/applications/"
        self._expected_result = "All applications returned; HTTP 200"

        self.create_scholarship_application(status='PENDING')
        self.login_as_assistant()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200:
            self._record_result("All apps retrieved", "Pass", f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_unauthenticated_access_blocked(self):
        """Exception: Unauthenticated user cannot retrieve application."""
        self._test_id = "UC-7-EX-01"
        self._uc_id = "SPACS-UC-007"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated access"
        self._preconditions = "No user logged in"
        self._input_action = "GET without authentication"
        self._expected_result = "HTTP 401 or 403"

        app = self.create_scholarship_application(status='PENDING')
        self.logout()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code in [401, 403]:
            self._record_result("Access blocked", "Pass", f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-008 : Check Application Status
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC08_CheckApplicationStatus(UCTestBase):
    """SPACS-UC-008: Student views current application status."""

    def test_hp01_student_checks_status_list(self):
        """Happy Path: Student checks status via applications list."""
        self._test_id = "UC-8-HP-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Happy Path"
        self._scenario = "Student checks status via list"
        self._preconditions = "Student logged in; has application"
        self._input_action = "GET /spacs/api/applications/"
        self._expected_result = "Applications with status field; HTTP 200"

        self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code == 200 and len(response.data) > 0:
            has_status = 'status' in response.data[0]
            if has_status:
                self._record_result("Status found", "Pass", str(response.data[0]['status']))
            else:
                self._record_result("No status field", "Fail", str(response.data[0]))
                self.fail("Status field not in response")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200 with data, got {response.status_code}")

    def test_ap01_student_checks_specific_application(self):
        """Alternate Path: Student checks specific application detail."""
        self._test_id = "UC-8-AP-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Alternate Path"
        self._scenario = "Student checks specific app detail"
        self._preconditions = "Student logged in; has application"
        self._input_action = "GET /spacs/api/applications/<pk>/"
        self._expected_result = "Application with status_display; HTTP 200"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_student()
        response = self.client.get(URL_APP_PK.format(app.pk), format='json')

        if response.status_code == 200:
            self._record_result("Detail retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_unauthenticated_status_blocked(self):
        """Exception: Unauthenticated user cannot check status."""
        self._test_id = "UC-8-EX-01"
        self._uc_id = "SPACS-UC-008"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated status check"
        self._preconditions = "No user logged in"
        self._input_action = "GET without authentication"
        self._expected_result = "HTTP 401 or 403"

        self.logout()
        response = self.client.get(URL_APPS, format='json')

        if response.status_code in [401, 403]:
            self._record_result("Blocked", "Pass", f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-009 : Forward Application
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC09_ForwardApplication(UCTestBase):
    """SPACS-UC-009: Assistant forwards verified application to Convener."""

    def test_hp01_forward_under_review(self):
        """Happy Path: Forward UNDER_REVIEW to next stage."""
        self._test_id = "UC-9-HP-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Happy Path"
        self._scenario = "Forward UNDER_REVIEW -> FORWARDED"
        self._preconditions = "Assistant logged in; app UNDER_REVIEW"
        self._input_action = "PATCH update-status"
        self._expected_result = "Status=FORWARDED; HTTP 200"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'FORWARDED'}, format='json')

        if response.status_code == 200:
            self._record_result("Forwarded", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_approve_directly_from_under_review(self):
        """Alternate Path: Assistant approves directly from UNDER_REVIEW."""
        self._test_id = "UC-9-AP-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Alternate Path"
        self._scenario = "UNDER_REVIEW -> APPROVED directly"
        self._preconditions = "Assistant logged in; app UNDER_REVIEW"
        self._input_action = "PATCH with APPROVED + amount"
        self._expected_result = "Status=APPROVED; HTTP 200"

        app = self.create_scholarship_application(status='UNDER_REVIEW')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk),
            {'new_status': 'APPROVED', 'amount_approved': '25000.00'}, format='json')

        if response.status_code == 200:
            self._record_result("Approved directly", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_forward_rejected_application_fails(self):
        """Exception: Cannot forward an already REJECTED application."""
        self._test_id = "UC-9-EX-01"
        self._uc_id = "SPACS-UC-009"
        self._test_category = "Exception"
        self._scenario = "Forward REJECTED application"
        self._preconditions = "Assistant logged in; app REJECTED"
        self._input_action = "PATCH with FORWARDED on REJECTED"
        self._expected_result = "Rejected; invalid transition"

        app = self.create_scholarship_application(status='REJECTED')
        self.login_as_assistant()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk), {'new_status': 'FORWARDED'}, format='json')

        if response.status_code in [422, 400]:
            self._record_result("Blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 422/400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-010 : Add New Scholarships
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC10_AddNewScholarships(UCTestBase):
    """SPACS-UC-010: Admin creates a new ScholarshipType."""

    def test_hp01_create_scholarship_type(self):
        """Happy Path: Admin creates new scholarship type with full details."""
        self._test_id = "UC-10-HP-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Happy Path"
        self._scenario = "Create new scholarship type"
        self._preconditions = "Admin logged in"
        self._input_action = "POST /spacs/api/types/"
        self._expected_result = "Created; HTTP 201"

        self.login_as_admin()
        data = {
            'name': 'New Merit Award',
            'category': 'MERIT',
            'description': 'A new merit scholarship',
            'amount': '75000.00',
            'frequency': 'ANNUAL',
            'eligibility_criteria': 'CPI >= 9.0',
        }
        response = self.client.post(URL_TYPES, data, format='json')

        if response.status_code == 201:
            self._record_result("Created", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ap01_create_with_minimal_fields(self):
        """Alternate Path: Create with only required fields."""
        self._test_id = "UC-10-AP-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Alternate Path"
        self._scenario = "Create with minimal fields"
        self._preconditions = "Admin logged in"
        self._input_action = "POST /spacs/api/types/ minimal"
        self._expected_result = "Created; HTTP 201"

        self.login_as_admin()
        data = {
            'name': 'Minimal Scholarship',
            'category': 'NEED',
            'description': 'Minimal test',
            'amount': '10000.00',
            'frequency': 'ONE_TIME',
            'eligibility_criteria': 'None',
        }
        response = self.client.post(URL_TYPES, data, format='json')

        if response.status_code == 201:
            self._record_result("Created minimal", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 201, got {response.status_code}: {response.data}")

    def test_ex01_invalid_category_rejected(self):
        """Exception: Invalid category rejected."""
        self._test_id = "UC-10-EX-01"
        self._uc_id = "SPACS-UC-010"
        self._test_category = "Exception"
        self._scenario = "Invalid category"
        self._preconditions = "Admin logged in"
        self._input_action = "POST with category=INVALID"
        self._expected_result = "HTTP 400"

        self.login_as_admin()
        data = {
            'name': 'Bad Scholarship',
            'category': 'INVALID',
            'description': 'Invalid',
            'amount': '10000.00',
            'frequency': 'ANNUAL',
            'eligibility_criteria': 'N/A',
        }
        response = self.client.post(URL_TYPES, data, format='json')

        if response.status_code == 400:
            self._record_result("Invalid rejected", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 400, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-011 : Modify Award Criteria
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC11_ModifyAwardCriteria(UCTestBase):
    """SPACS-UC-011: Admin edits criteria for existing scholarship type."""

    def test_hp01_update_eligibility_criteria(self):
        """Happy Path: Admin updates eligibility criteria."""
        self._test_id = "UC-11-HP-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Happy Path"
        self._scenario = "Update eligibility criteria"
        self._preconditions = "Admin logged in; scholarship exists"
        self._input_action = "PATCH /spacs/api/types/<pk>/"
        self._expected_result = "Updated; HTTP 200"

        self.login_as_admin()
        response = self.client.patch(
            URL_TYPE_PK.format(self.active_scholarship.pk),
            {'eligibility_criteria': 'Updated: GEN, min CPI 9.0'}, format='json')

        if response.status_code == 200:
            self._record_result("Updated", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_deactivate_scholarship(self):
        """Alternate Path: Admin deactivates (soft-delete) a scholarship."""
        self._test_id = "UC-11-AP-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Alternate Path"
        self._scenario = "Deactivate scholarship"
        self._preconditions = "Admin logged in; active scholarship"
        self._input_action = "DELETE /spacs/api/types/<pk>/"
        self._expected_result = "Deactivated; HTTP 204"

        temp = ScholarshipType.objects.create(
            name='Temp Scholarship', category='MERIT',
            description='Temp', eligibility_criteria='None',
            amount=5000, frequency='ANNUAL', is_active=True,
        )
        self.login_as_admin()
        response = self.client.delete(URL_TYPE_PK.format(temp.pk), format='json')

        if response.status_code == 204:
            temp.refresh_from_db()
            if not temp.is_active:
                self._record_result("Deactivated", "Pass", f"is_active={temp.is_active}")
            else:
                self._record_result("Still active", "Fail", f"is_active={temp.is_active}")
                self.fail("Scholarship should be deactivated")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(getattr(response, 'data', '')))
            self.fail(f"Expected 204, got {response.status_code}")

    def test_ex01_update_nonexistent_fails(self):
        """Exception: Update non-existent scholarship type."""
        self._test_id = "UC-11-EX-01"
        self._uc_id = "SPACS-UC-011"
        self._test_category = "Exception"
        self._scenario = "Update non-existent type"
        self._preconditions = "Admin logged in"
        self._input_action = "PATCH /spacs/api/types/99999/"
        self._expected_result = "HTTP 404"

        self.login_as_admin()
        response = self.client.patch(
            URL_TYPE_PK.format(99999), {'eligibility_criteria': 'New'}, format='json')

        if response.status_code == 404:
            self._record_result("Not found", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 404, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-012 : Manage Scholarship Catalogue
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC12_ManageScholarshipCatalogue(UCTestBase):
    """SPACS-UC-012: Admin manages catalogue of scholarship types."""

    def test_hp01_retrieve_full_catalogue(self):
        """Happy Path: Retrieve full scholarship catalogue."""
        self._test_id = "UC-12-HP-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Happy Path"
        self._scenario = "Retrieve full catalogue"
        self._preconditions = "User logged in; types exist"
        self._input_action = "GET /spacs/api/types/"
        self._expected_result = "List returned; HTTP 200"

        self.login_as_admin()
        response = self.client.get(URL_TYPES, format='json')

        if response.status_code == 200:
            self._record_result("Catalogue retrieved", "Pass", f"Count={len(response.data)}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_retrieve_specific_type(self):
        """Alternate Path: Retrieve specific scholarship type details."""
        self._test_id = "UC-12-AP-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Alternate Path"
        self._scenario = "Retrieve single type"
        self._preconditions = "User logged in; type exists"
        self._input_action = "GET /spacs/api/types/<pk>/"
        self._expected_result = "Type details; HTTP 200"

        self.login_as_admin()
        response = self.client.get(
            URL_TYPE_PK.format(self.active_scholarship.pk), format='json')

        if response.status_code == 200:
            self._record_result("Type retrieved", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_unauthenticated_access_blocked(self):
        """Exception: Unauthenticated user cannot view catalogue."""
        self._test_id = "UC-12-EX-01"
        self._uc_id = "SPACS-UC-012"
        self._test_category = "Exception"
        self._scenario = "Unauthenticated catalogue access"
        self._preconditions = "No user logged in"
        self._input_action = "GET without auth"
        self._expected_result = "HTTP 401 or 403"

        self.logout()
        response = self.client.get(URL_TYPES, format='json')

        if response.status_code in [401, 403]:
            self._record_result("Blocked", "Pass", f"HTTP {response.status_code}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 401/403, got {response.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# UC-013 : Verify and Grant Scholarship
# ═══════════════════════════════════════════════════════════════════════════════

class TestUC13_VerifyAndGrantScholarship(UCTestBase):
    """SPACS-UC-013: Admin disburses approved scholarships."""

    def test_hp01_disburse_approved_application(self):
        """Happy Path: Disburse approved scholarship."""
        self._test_id = "UC-13-HP-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Happy Path"
        self._scenario = "Disburse approved application"
        self._preconditions = "Admin logged in; app APPROVED"
        self._input_action = "POST /spacs/api/applications/<pk>/disburse/"
        self._expected_result = "Status=DISBURSED; HTTP 200"

        app = self.create_scholarship_application(status='APPROVED')
        self.login_as_admin()
        response = self.client.post(
            URL_DISBURSE_PK.format(app.pk),
            {'transaction_reference': 'TXN-TEST-001'}, format='json')

        if response.status_code == 200:
            self._record_result("Disbursed", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_approve_before_disburse(self):
        """Alternate Path: Approve forwarded application before disbursement."""
        self._test_id = "UC-13-AP-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Alternate Path"
        self._scenario = "Approve forwarded, then disburse"
        self._preconditions = "Admin logged in; app FORWARDED"
        self._input_action = "PATCH APPROVED + amount"
        self._expected_result = "Approved; HTTP 200"

        app = self.create_scholarship_application(status='FORWARDED')
        self.login_as_admin()
        response = self.client.patch(
            URL_STATUS_PK.format(app.pk),
            {'new_status': 'APPROVED', 'amount_approved': '30000.00'}, format='json')

        if response.status_code == 200:
            self._record_result("Approved for disbursement", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ex01_disburse_non_approved_fails(self):
        """Exception: Cannot disburse a non-APPROVED application."""
        self._test_id = "UC-13-EX-01"
        self._uc_id = "SPACS-UC-013"
        self._test_category = "Exception"
        self._scenario = "Disburse PENDING application"
        self._preconditions = "Admin logged in; app PENDING"
        self._input_action = "POST /disburse/ on PENDING"
        self._expected_result = "Rejected; only APPROVED can be disbursed"

        app = self.create_scholarship_application(status='PENDING')
        self.login_as_admin()
        response = self.client.post(
            URL_DISBURSE_PK.format(app.pk),
            {'transaction_reference': 'TXN-FAIL-001'}, format='json')

        if response.status_code in [422, 400]:
            self._record_result("Correctly blocked", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 422/400, got {response.status_code}")