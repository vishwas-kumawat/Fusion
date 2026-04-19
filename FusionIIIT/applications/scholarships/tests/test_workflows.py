"""
test_workflows.py — Workflow tests for the SPACS Scholarship module.

<<<<<<< HEAD
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
=======
2 Workflows × 2 tests each (E2E + Negative) = 4 tests.
Naming: TestWF{NN}_{Title}  ·  test_e2e_...  ·  test_negative_...
"""

from django.urls import reverse
from .conftest import BaseModuleTestCase
from applications.scholarships.models import McmApplication


class WFTestBase(BaseModuleTestCase):
    """Base marker class for Workflow tests."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# WF‑101 : Apply → Verify → Approve/Reject → Grant
# ═══════════════════════════════════════════════════════════════════════════════

class TestWF01_ApplyVerifyApproveGrant(WFTestBase):
    """SPACS-WF-101: Full scholarship processing workflow."""

    def test_e2e_full_approval_flow(self):
        """End-to-End: Student submits → Assistant verifies → Convener approves."""
        self._test_id = "WF-101-E2E-01"
        self._wf_id = "SPACS-WF-101"
        self._test_category = "End-to-End"
        self._scenario = "Full approval: pending → verified → approved"
        self._expected_result = "Application reaches approved status"

        # ── Step 1: Student submits MCM application ─────────────────────────
        self.login_as_student()
        url_create = reverse('api-mcm-applications')
        create_data = {
            'email': 'wf_test@test.com',
            'student_full_name': 'WF Test Student',
            'roll_no': '2021BCS001',
            'batch': '2021',
            'programme': 'B.Tech CSE',
            'mobile_no': '9876543210',
            'father_name': 'Father Name',
            'mother_name': 'Mother Name',
            'category': 'GEN',
            'current_cpi': '8.50',
            'current_spi': '8.50',
            'annual_income': '300000',
            'postal_address': '123 Test Street',
            'declaration_yes': 'Yes',
        }
        resp1 = self.client.post(url_create, create_data, format='json')
        step1_ok = resp1.status_code == 201
        app_id = resp1.data.get('id') if step1_ok else None
        self._add_step(1, "Student submits MCM application",
                       "HTTP 201, status=pending",
                       f"HTTP {resp1.status_code}",
                       step1_ok)

        if not step1_ok:
            self._record_result(f"Step 1 failed: {resp1.data}", "Fail",
                                str(resp1.data))
            self.fail(f"Step 1: Expected 201, got {resp1.status_code}: {resp1.data}")
            return

        # Verify initial status
        app = McmApplication.objects.get(pk=app_id)
        step1b_ok = app.status == 'pending'
        self._add_step(1, "Verify initial status=pending",
                       "pending", app.status, step1b_ok)

        # ── Step 2: Assistant verifies the application ──────────────────────
        self.login_as_assistant()
        url_detail = reverse('api-mcm-application-detail', args=[app_id])
        resp2 = self.client.patch(url_detail, {'status': 'verified'}, format='json')
        step2_ok = resp2.status_code == 200
        self._add_step(2, "Assistant verifies application",
                       "HTTP 200, status=verified",
                       f"HTTP {resp2.status_code}",
                       step2_ok)

        if step2_ok:
            app.refresh_from_db()
            step2b_ok = app.status == 'verified'
            self._add_step(2, "Verify status=verified in DB",
                           "verified", app.status, step2b_ok)
        else:
            self._record_result(f"Step 2 failed: {resp2.data}", "Fail",
                                str(resp2.data))
            self.fail(f"Step 2: Expected 200, got {resp2.status_code}")
            return

        # ── Step 3: Convener approves the application ───────────────────────
        self.login_as_convener()
        resp3 = self.client.patch(url_detail, {'status': 'approved'}, format='json')
        step3_ok = resp3.status_code == 200
        self._add_step(3, "Convener approves application",
                       "HTTP 200, status=approved",
                       f"HTTP {resp3.status_code}",
                       step3_ok)

        if step3_ok:
            app.refresh_from_db()
            step3b_ok = app.status == 'approved'
            self._add_step(3, "Verify status=approved in DB",
                           "approved", app.status, step3b_ok)

        # ── Final assertion ─────────────────────────────────────────────────
        if self._all_steps_passed():
            self._record_result(
                "Full flow: pending → verified → approved", "Pass",
                f"Final status={app.status}")
        else:
            failed = [s for s in self._steps if not s['passed']]
            self._record_result(
                f"Flow incomplete at step(s): {[s['step'] for s in failed]}",
                "Fail",
                str(failed))
            self.fail("Workflow did not complete successfully")

    def test_negative_convener_rejects(self):
        """Negative: Convener rejects verified application."""
        self._test_id = "WF-101-NEG-01"
        self._wf_id = "SPACS-WF-101"
        self._test_category = "Negative"
        self._scenario = "Full rejection: pending → verified → rejected"
        self._expected_result = "Application reaches rejected status; no grant"

        # ── Step 1: Create pending application ──────────────────────────────
        app = self.create_mcm_application(status='pending')
        step1_ok = app.status == 'pending'
        self._add_step(1, "MCM application exists (pending)",
                       "pending", app.status, step1_ok)

        # ── Step 2: Assistant verifies ──────────────────────────────────────
        self.login_as_assistant()
        url_detail = reverse('api-mcm-application-detail', args=[app.pk])
        resp2 = self.client.patch(url_detail, {'status': 'verified'}, format='json')
        step2_ok = resp2.status_code == 200
        self._add_step(2, "Assistant verifies",
                       "HTTP 200", f"HTTP {resp2.status_code}", step2_ok)

        if step2_ok:
            app.refresh_from_db()
            self._add_step(2, "Status=verified", "verified", app.status,
                           app.status == 'verified')

        # ── Step 3: Convener rejects ────────────────────────────────────────
        self.login_as_convener()
        resp3 = self.client.patch(url_detail, {'status': 'rejected'}, format='json')
        step3_ok = resp3.status_code == 200
        self._add_step(3, "Convener rejects",
                       "HTTP 200", f"HTTP {resp3.status_code}", step3_ok)

        if step3_ok:
            app.refresh_from_db()
            step3b_ok = app.status == 'rejected'
            self._add_step(3, "Verify status=rejected",
                           "rejected", app.status, step3b_ok)

        # ── Final assertion ─────────────────────────────────────────────────
        if self._all_steps_passed():
            self._record_result(
                "Rejection flow complete: pending → verified → rejected", "Pass",
                f"Final status={app.status}")
        else:
            failed = [s for s in self._steps if not s['passed']]
            self._record_result(
                f"Rejection flow failed: {[s['step'] for s in failed]}",
                "Fail", str(failed))
            self.fail("Rejection workflow did not complete")


# ═══════════════════════════════════════════════════════════════════════════════
# WF‑201 : Amend / Withdraw Pending
# ═══════════════════════════════════════════════════════════════════════════════

class TestWF02_AmendWithdrawPending(WFTestBase):
    """SPACS-WF-201: Amend/withdraw pending application workflow."""

    def test_e2e_revert_edit_reverify(self):
        """End-to-End: Assistant reverts → Student edits → Re-verified."""
        self._test_id = "WF-201-E2E-01"
        self._wf_id = "SPACS-WF-201"
        self._test_category = "End-to-End"
        self._scenario = "Amend cycle: pending → reverted → pending → verified"
        self._expected_result = "Application re-verified after amend cycle"

        # ── Step 1: Create pending application ──────────────────────────────
        app = self.create_mcm_application(status='pending')
        step1_ok = app.status == 'pending'
        self._add_step(1, "MCM application created (pending)",
                       "pending", app.status, step1_ok)

        url_detail = reverse('api-mcm-application-detail', args=[app.pk])

        # ── Step 2: Assistant reverts ───────────────────────────────────────
        self.login_as_assistant()
        resp2 = self.client.patch(url_detail, {
            'status': 'reverted',
            'revert_reason': 'Incorrect income details',
        }, format='json')
        step2_ok = resp2.status_code == 200
        self._add_step(2, "Assistant reverts application",
                       "HTTP 200, status=reverted",
                       f"HTTP {resp2.status_code}",
                       step2_ok)

        if step2_ok:
            app.refresh_from_db()
            self._add_step(2, "Verify status=reverted",
                           "reverted", app.status, app.status == 'reverted')

        # ── Step 3: Student edits reverted application ──────────────────────
        self.login_as_student()
        resp3 = self.client.patch(url_detail, {
            'annual_income': '250000',
        }, format='json')
        step3_ok = resp3.status_code == 200
        self._add_step(3, "Student edits reverted application",
                       "HTTP 200, status=pending",
                       f"HTTP {resp3.status_code}",
                       step3_ok)

        if step3_ok:
            app.refresh_from_db()
            step3b_ok = app.status == 'pending'
            self._add_step(3, "Verify status back to pending",
                           "pending", app.status, step3b_ok)

        # ── Step 4: Assistant re-verifies ───────────────────────────────────
        self.login_as_assistant()
        resp4 = self.client.patch(url_detail, {'status': 'verified'}, format='json')
        step4_ok = resp4.status_code == 200
        self._add_step(4, "Assistant re-verifies",
                       "HTTP 200, status=verified",
                       f"HTTP {resp4.status_code}",
                       step4_ok)

        if step4_ok:
            app.refresh_from_db()
            step4b_ok = app.status == 'verified'
            self._add_step(4, "Verify status=verified",
                           "verified", app.status, step4b_ok)

        # ── Final assertion ─────────────────────────────────────────────────
        if self._all_steps_passed():
            self._record_result(
                "Amend cycle: pending → reverted → pending → verified", "Pass",
                f"Final status={app.status}")
        else:
            failed = [s for s in self._steps if not s['passed']]
            self._record_result(
                f"Amend cycle failed: {[s['step'] for s in failed]}",
                "Fail", str(failed))
            self.fail("Amend workflow did not complete")

    def test_negative_cannot_modify_finalized(self):
        """Negative: Student cannot modify an approved (finalized) application."""
        self._test_id = "WF-201-NEG-01"
        self._wf_id = "SPACS-WF-201"
        self._test_category = "Negative"
        self._scenario = "Cannot modify finalized (approved) application"
        self._expected_result = "Update rejected; status unchanged"

        # ── Step 1: Create approved (finalized) application ─────────────────
        app = self.create_mcm_application(status='approved')
        step1_ok = app.status == 'approved'
        self._add_step(1, "Approved application exists",
                       "approved", app.status, step1_ok)

        # ── Step 2: Student attempts to modify ──────────────────────────────
        self.login_as_student()
        url_detail = reverse('api-mcm-application-detail', args=[app.pk])
        resp2 = self.client.patch(url_detail, {
            'annual_income': '999999',
        }, format='json')
        step2_ok = resp2.status_code == 400
        self._add_step(2, "Student tries to modify finalized app",
                       "HTTP 400 (blocked)",
                       f"HTTP {resp2.status_code}",
                       step2_ok)

        # ── Step 3: Verify status unchanged ─────────────────────────────────
        app.refresh_from_db()
        step3_ok = app.status == 'approved'
        self._add_step(3, "Verify status still approved",
                       "approved", app.status, step3_ok)

        # ── Final assertion ─────────────────────────────────────────────────
        if self._all_steps_passed():
            self._record_result(
                "Finalized app correctly protected", "Pass",
                f"Status unchanged={app.status}")
        else:
            failed = [s for s in self._steps if not s['passed']]
            self._record_result(
                f"Protection failed: {[s['step'] for s in failed]}",
                "Fail", str(failed))
            self.fail("Finalized application was modified")
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
