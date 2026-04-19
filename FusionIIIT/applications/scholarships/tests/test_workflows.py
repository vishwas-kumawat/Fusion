"""
test_workflows.py — Workflow tests for the SPACS Scholarship module.

2 Workflows x 2 tests each (E2E + Negative) = 4 tests.
Naming: TestWF{NN}_{Title}  .  test_e2e_...  .  test_neg_...
"""

from .conftest import WFTestBase
from applications.scholarships.models import (
    ScholarshipApplication, ApplicationStatus,
)

# ── URL constants ──────────────────────────────────────────────────────────
URL_APPS        = '/spacs/api/applications/'
URL_APP_PK      = '/spacs/api/applications/{}/'
URL_STATUS_PK   = '/spacs/api/applications/{}/update-status/'
URL_DISBURSE_PK = '/spacs/api/applications/{}/disburse/'


# ═══════════════════════════════════════════════════════════════════════════════
# WF-101 : Apply -> Verify -> Approve/Reject -> Grant
# ═══════════════════════════════════════════════════════════════════════════════

class TestWF101_FullLifecycle(WFTestBase):
    """SPACS-WF-101: Full application lifecycle from apply to disburse."""

    def test_e2e_apply_review_approve_disburse(self):
        """End-to-End: Student applies -> Assistant reviews -> Convener approves -> Disbursed."""
        self._test_id = "WF-101-E2E-01"
        self._wf_id = "SPACS-WF-101"
        self._test_category = "End-to-End"
        self._scenario = "Full happy path lifecycle"
        self._expected_result = "Status=DISBURSED; transaction recorded"

        # Step 1: Student applies
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        resp1 = self.client.post(URL_APPS, data, format='json')
        step1_pass = resp1.status_code == 201
        self._add_step(1, "Student submits application", "HTTP 201", f"HTTP {resp1.status_code}", step1_pass)

        if step1_pass:
            app_id = resp1.data['id']
        else:
            self._record_result(f"Step 1 failed: HTTP {resp1.status_code}", "Fail", str(resp1.data))
            self.fail(f"Step 1: Expected 201, got {resp1.status_code}: {resp1.data}")
            return

        # Step 2: Assistant moves to UNDER_REVIEW
        self.login_as_assistant()
        resp2 = self.client.patch(
            URL_STATUS_PK.format(app_id), {'new_status': 'UNDER_REVIEW'}, format='json')
        step2_pass = resp2.status_code == 200
        self._add_step(2, "Assistant reviews", "UNDER_REVIEW", f"HTTP {resp2.status_code}", step2_pass)

        # Step 3: Assistant forwards to convener
        resp3 = self.client.patch(
            URL_STATUS_PK.format(app_id), {'new_status': 'FORWARDED'}, format='json')
        step3_pass = resp3.status_code == 200
        self._add_step(3, "Assistant forwards", "FORWARDED", f"HTTP {resp3.status_code}", step3_pass)

        # Step 4: Convener approves
        self.login_as_convener()
        resp4 = self.client.patch(
            URL_STATUS_PK.format(app_id),
            {'new_status': 'APPROVED', 'amount_approved': '50000.00'}, format='json')
        step4_pass = resp4.status_code == 200
        self._add_step(4, "Convener approves", "APPROVED", f"HTTP {resp4.status_code}", step4_pass)

        # Step 5: Admin disburses
        self.login_as_admin()
        resp5 = self.client.post(
            URL_DISBURSE_PK.format(app_id),
            {'transaction_reference': 'TXN-WF101-001'}, format='json')
        step5_pass = resp5.status_code == 200
        self._add_step(5, "Admin disburses", "DISBURSED", f"HTTP {resp5.status_code}", step5_pass)

        # Verify final state
        app = ScholarshipApplication.objects.get(id=app_id)
        all_pass = self._all_steps_passed()

        if all_pass and app.status == ApplicationStatus.DISBURSED:
            self._record_result(
                "Full lifecycle completed",
                "Pass",
                f"status={app.status}, txn={app.transaction_reference}"
            )
        else:
            self._record_result(
                f"Incomplete lifecycle: status={app.status}",
                "Fail",
                str(self._steps)
            )
            self.fail(f"Expected DISBURSED, got {app.status}")

    def test_neg_apply_review_reject(self):
        """Negative: Student applies -> Assistant reviews -> Convener rejects."""
        self._test_id = "WF-101-NEG-01"
        self._wf_id = "SPACS-WF-101"
        self._test_category = "Negative"
        self._scenario = "Application rejected at convener level"
        self._expected_result = "Status=REJECTED; no disbursement"

        # Step 1: Student applies
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2025-26',
            'semester': 1,
        }
        resp1 = self.client.post(URL_APPS, data, format='json')
        step1_pass = resp1.status_code == 201
        self._add_step(1, "Student submits", "HTTP 201", f"HTTP {resp1.status_code}", step1_pass)

        if step1_pass:
            app_id = resp1.data['id']
        else:
            self._record_result(f"Step 1 failed: {resp1.status_code}", "Fail", str(resp1.data))
            self.fail(f"Step 1: Expected 201, got {resp1.status_code}")
            return

        # Step 2: Assistant reviews
        self.login_as_assistant()
        resp2 = self.client.patch(
            URL_STATUS_PK.format(app_id), {'new_status': 'UNDER_REVIEW'}, format='json')
        step2_pass = resp2.status_code == 200
        self._add_step(2, "Assistant reviews", "UNDER_REVIEW", f"HTTP {resp2.status_code}", step2_pass)

        # Step 3: Convener rejects
        self.login_as_convener()
        resp3 = self.client.patch(
            URL_STATUS_PK.format(app_id),
            {'new_status': 'REJECTED', 'review_remarks': 'Not meeting criteria'}, format='json')
        step3_pass = resp3.status_code == 200
        self._add_step(3, "Convener rejects", "REJECTED", f"HTTP {resp3.status_code}", step3_pass)

        # Verify
        app = ScholarshipApplication.objects.get(id=app_id)

        if app.status == ApplicationStatus.REJECTED:
            self._record_result("Correctly rejected", "Pass", f"status={app.status}")
        else:
            self._record_result(f"status={app.status}", "Fail", str(self._steps))
            self.fail(f"Expected REJECTED, got {app.status}")


# ═══════════════════════════════════════════════════════════════════════════════
# WF-201 : Amend / Withdraw Pending
# ═══════════════════════════════════════════════════════════════════════════════

class TestWF201_AmendWithdrawPending(WFTestBase):
    """SPACS-WF-201: Student withdraws a pending application."""

    def test_e2e_apply_then_cancel(self):
        """End-to-End: Student applies then cancels PENDING application."""
        self._test_id = "WF-201-E2E-01"
        self._wf_id = "SPACS-WF-201"
        self._test_category = "End-to-End"
        self._scenario = "Apply & cancel pending"
        self._expected_result = "Application deleted"

        # Step 1: Student applies
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        resp1 = self.client.post(URL_APPS, data, format='json')
        step1_pass = resp1.status_code == 201
        self._add_step(1, "Student applies", "HTTP 201", f"HTTP {resp1.status_code}", step1_pass)

        if step1_pass:
            app_id = resp1.data['id']
        else:
            self._record_result(f"Step 1 failed: {resp1.status_code}", "Fail", str(resp1.data))
            self.fail(f"Expected 201, got {resp1.status_code}")
            return

        # Step 2: Cancel
        resp2 = self.client.delete(URL_APP_PK.format(app_id), format='json')
        step2_pass = resp2.status_code == 204
        self._add_step(2, "Student cancels", "HTTP 204", f"HTTP {resp2.status_code}", step2_pass)

        # Verify deleted
        exists = ScholarshipApplication.objects.filter(id=app_id).exists()
        if not exists:
            self._record_result("Deleted", "Pass", "Application no longer exists")
        else:
            self._record_result("Still exists", "Fail", "Application not deleted")
            self.fail("Application should be deleted")

    def test_neg_cancel_under_review_blocked(self):
        """Negative: Cannot cancel UNDER_REVIEW application."""
        self._test_id = "WF-201-NEG-01"
        self._wf_id = "SPACS-WF-201"
        self._test_category = "Negative"
        self._scenario = "Cancel UNDER_REVIEW is blocked"
        self._expected_result = "Cancellation blocked; app remains"

        # Step 1: Student applies
        self.login_as_student()
        data = {
            'student': self.student.pk,
            'scholarship_type': self.active_scholarship.pk,
            'academic_year': '2024-25',
            'semester': 1,
        }
        resp1 = self.client.post(URL_APPS, data, format='json')
        step1_pass = resp1.status_code == 201
        self._add_step(1, "Student applies", "HTTP 201", f"HTTP {resp1.status_code}", step1_pass)

        if step1_pass:
            app_id = resp1.data['id']
        else:
            self._record_result(f"Step 1 failed: {resp1.status_code}", "Fail", str(resp1.data))
            self.fail(f"Expected 201, got {resp1.status_code}")
            return

        # Step 2: Move to UNDER_REVIEW
        self.login_as_assistant()
        resp2 = self.client.patch(
            URL_STATUS_PK.format(app_id), {'new_status': 'UNDER_REVIEW'}, format='json')
        step2_pass = resp2.status_code == 200
        self._add_step(2, "Assistant reviews", "UNDER_REVIEW", f"HTTP {resp2.status_code}", step2_pass)

        # Step 3: Student tries to cancel
        self.login_as_student()
        resp3 = self.client.delete(URL_APP_PK.format(app_id), format='json')
        step3_pass = resp3.status_code in [422, 400, 403]
        self._add_step(3, "Student tries cancel", "Blocked", f"HTTP {resp3.status_code}", step3_pass)

        # Verify still exists
        exists = ScholarshipApplication.objects.filter(id=app_id).exists()
        if exists and step3_pass:
            self._record_result("Cancel blocked correctly", "Pass", f"HTTP {resp3.status_code}")
        else:
            self._record_result("Failed", "Fail", str(self._steps))
            self.fail(f"Cancel should have been blocked. Status: {resp3.status_code}")