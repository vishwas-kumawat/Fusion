"""
conftest.py — Base test setup for SPACS (Scholarships & Awards) module.

Creates all test actors (Student, Assistant, Convener, Admin) and provides
shared helper methods used by all test files.
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from applications.globals.models import (
    ExtraInfo, DepartmentInfo, Designation, HoldsDesignation,
)
from applications.academic_information.models import Student
from applications.scholarships.models import (
    Award_and_scholarship, Mcm, Release,
    ScholarshipType, ScholarshipApplication,
    Award, AwardRecipient,
    ApplicationStatus,
)


class BaseModuleTestCase(TestCase):
    """
    Base class for every SPACS test.  Call super().setUpTestData() in
    subclasses that override it.
    """

    # ── Class-level fixtures (created ONCE for the entire TestCase) ──────────

    @classmethod
    def setUpTestData(cls):
        # ── Department ──────────────────────────────────────────────────────
        cls.dept = DepartmentInfo.objects.create(name='CSE')

        # ── Student 1 (primary test student — eligible) ─────────────────────
        cls.student_user = User.objects.create_user(
            username='2021BCS001', password='test123',
            first_name='Test', last_name='Student',
        )
        cls.student_extra = ExtraInfo.objects.create(
            user=cls.student_user, id='2021BCS001',
            user_type='student', department=cls.dept,
            phone_no=9999999999,
        )
        cls.student = Student.objects.create(
            id=cls.student_extra,
            programme='B.Tech', batch=2021,
            cpi=8.5, category='GEN',
        )

        # ── Student 2 (second student — for ownership / access tests) ──────
        cls.student_user_2 = User.objects.create_user(
            username='2021BCS002', password='test123',
            first_name='Other', last_name='Student',
        )
        cls.student_extra_2 = ExtraInfo.objects.create(
            user=cls.student_user_2, id='2021BCS002',
            user_type='student', department=cls.dept,
        )
        cls.student_2 = Student.objects.create(
            id=cls.student_extra_2,
            programme='B.Tech', batch=2021,
            cpi=7.5, category='GEN',
        )

        # ── SPACS Assistant ─────────────────────────────────────────────────
        cls.assistant_user = User.objects.create_user(
            username='spacsassistant1', password='test123',
        )
        cls.assistant_extra = ExtraInfo.objects.create(
            user=cls.assistant_user, id='spacsassistant1',
            user_type='staff', department=cls.dept,
        )

        # ── SPACS Convener ──────────────────────────────────────────────────
        cls.convener_user = User.objects.create_user(
            username='spacsconvenor1', password='test123',
        )
        cls.convener_extra = ExtraInfo.objects.create(
            user=cls.convener_user, id='spacsconvenor1',
            user_type='staff', department=cls.dept,
        )

        # ── Admin / Superuser ───────────────────────────────────────────────
        cls.admin_user = User.objects.create_superuser(
            username='admin1', password='test123', email='admin@test.com',
        )
        cls.admin_extra = ExtraInfo.objects.create(
            user=cls.admin_user, id='admin1',
            user_type='staff', department=cls.dept,
        )

        # ── Designations & HoldsDesignation ─────────────────────────────────
        cls.assistant_desig = Designation.objects.create(
            name='spacs_assistant', full_name='SPACS Assistant',
        )
        cls.convener_desig = Designation.objects.create(
            name='spacs_convener', full_name='SPACS Convenor',
        )
        HoldsDesignation.objects.create(
            user=cls.assistant_user,
            working=cls.assistant_user,
            designation=cls.assistant_desig,
        )
        HoldsDesignation.objects.create(
            user=cls.convener_user,
            working=cls.convener_user,
            designation=cls.convener_desig,
        )

        # ── Legacy award + open release window ──────────────────────────────
        cls.test_award = Award_and_scholarship.objects.create(
            award_name='Test MCM Award',
            catalog='Test scholarship for MCM',
        )
        cls.test_release = Release.objects.create(
            award='Merit-cum-Means Scholarship',
            startdate=timezone.now().date() - timedelta(days=1),
            enddate=timezone.now().date() + timedelta(days=30),
            batch='2021', programme='B.Tech',
        )

        # ── ScholarshipType (active) ────────────────────────────────────────
        cls.active_scholarship = ScholarshipType.objects.create(
            name='Test Merit Scholarship',
            category='MERIT',
            description='Test merit-based scholarship',
            eligibility_criteria='GEN category, no backlogs',
            max_backlogs=0,
            applicable_categories='GEN,SC,ST,OBC',
            is_active=True,
            amount=Decimal('50000.00'),
            frequency='ANNUAL',
        )

        # ── ScholarshipType (inactive) ──────────────────────────────────────
        cls.inactive_scholarship = ScholarshipType.objects.create(
            name='Inactive Scholarship',
            category='MERIT',
            description='Deactivated scholarship',
            eligibility_criteria='Not available',
            max_backlogs=0,
            is_active=False,
            amount=Decimal('10000.00'),
            frequency='ANNUAL',
        )

    # ── Per-test setup ──────────────────────────────────────────────────────

    def setUp(self):
        self.client = APIClient()

        # Result tracking for reporter
        self._test_id = ''
        self._uc_id = ''
        self._br_id = ''
        self._wf_id = ''
        self._test_category = ''
        self._scenario = ''
        self._preconditions = ''
        self._input_action = ''
        self._expected_result = ''
        self._results = []
        self._steps = []

    # ── Login helpers ───────────────────────────────────────────────────────

    def login_as_student(self, user=None):
        self.client.force_authenticate(user=user or self.student_user)

    def login_as_student2(self):
        self.client.force_authenticate(user=self.student_user_2)

    def login_as_assistant(self):
        self.client.force_authenticate(user=self.assistant_user)

    def login_as_convener(self):
        self.client.force_authenticate(user=self.convener_user)

    def login_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)

    def logout(self):
        self.client.force_authenticate(user=None)

    # ── API helpers ─────────────────────────────────────────────────────────

    def api_get(self, path, expected_status=200):
        response = self.client.get(path, format='json')
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"GET {path} -> {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_post(self, path, data=None, expected_status=201, fmt='json'):
        response = self.client.post(path, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"POST {path} -> {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_patch(self, path, data=None, expected_status=200, fmt='json'):
        response = self.client.patch(path, data or {}, format=fmt)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"PATCH {path} -> {response.status_code}: {getattr(response, 'data', '')}")
        return response

    def api_delete(self, path, expected_status=204):
        response = self.client.delete(path, format='json')
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"DELETE {path} -> {response.status_code}: {getattr(response, 'data', '')}")
        return response

    # ── Date helpers ────────────────────────────────────────────────────────

    @staticmethod
    def future_date(days=5):
        return (date.today() + timedelta(days=days)).isoformat()

    @staticmethod
    def past_date(days=3):
        return (date.today() - timedelta(days=days)).isoformat()

    @staticmethod
    def today():
        return date.today().isoformat()

    # ── DB assertion helpers ────────────────────────────────────────────────

    def assert_object_exists(self, model, **kwargs):
        self.assertTrue(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} does not exist",
        )

    def assert_object_not_exists(self, model, **kwargs):
        self.assertFalse(
            model.objects.filter(**kwargs).exists(),
            f"{model.__name__} with {kwargs} should not exist",
        )

    # ── ScholarshipApplication factory ───────────────────────────────────────

    def create_scholarship_application(self, student=None, scholarship=None,
                                       status='PENDING', **overrides):
        """Create a ScholarshipApplication for testing."""
        s = student or self.student
        sch = scholarship or self.active_scholarship
        defaults = {
            'student': s,
            'scholarship_type': sch,
            'academic_year': '2024-25',
            'semester': 1,
            'category_at_application': s.category,
            'status': status,
        }
        defaults.update(overrides)
        return ScholarshipApplication.objects.create(**defaults)

    # ── Award factory ────────────────────────────────────────────────────────

    def create_test_award(self, **overrides):
        """Create an Award (new model) for testing."""
        defaults = {
            'name': 'Test Academic Award',
            'category': 'ACADEMIC',
            'description': 'Test award description',
            'criteria': 'Top CPI',
            'prize_amount': Decimal('10000.00'),
            'is_active': True,
        }
        defaults.update(overrides)
        return Award.objects.create(**defaults)

    # ── Result recording (used by runner.py) ────────────────────────────────

    def _record_result(self, actual, status, evidence=''):
        self._results.append({
            'test_id': self._test_id,
            'actual': actual,
            'status': status,
            'evidence': evidence,
        })

    def _add_step(self, step_num, action, expected, actual, passed):
        self._steps.append({
            'step': step_num,
            'action': action,
            'expected': expected,
            'actual': actual,
            'passed': passed,
        })

    def _all_steps_passed(self):
        return all(s['passed'] for s in self._steps)


class UCTestBase(BaseModuleTestCase):
    """Marker base class for Use Case tests."""
    pass


class BRTestBase(BaseModuleTestCase):
    """Marker base class for Business Rule tests."""
    pass


class WFTestBase(BaseModuleTestCase):
    """Marker base class for Workflow tests."""
    pass
