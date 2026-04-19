"""
api/views.py – Award & Scholarship Module
Thin views: handle Request/Response only.
All business logic → services.py | All DB queries → selectors.py
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import ScholarshipType
from ..selectors import (
    get_all_applications,
    get_all_scholarship_types,
    get_application_by_id,
    get_applications_for_user,
    get_eligible_students_for_scholarship,
    get_scholarship_type_by_id,
)
from ..services import (
    ApplicationNotFound,
    DuplicateApplicationError,
    EligibilityError,
    InvalidStatusTransition,
    ScholarshipNotFound,
    amend_scholarship_application,
    cancel_scholarship_application,
    create_scholarship_application,
    create_scholarship_type,
    deactivate_scholarship_type,
    record_disbursement,
    update_application_status,
    update_scholarship_type,
)
from .serializers import (
    ApplicationStatusUpdateSerializer,
    DisbursementSerializer,
    EligibleStudentSerializer,
    ScholarshipApplicationDetailSerializer,
    ScholarshipApplicationSerializer,
    ScholarshipTypeSerializer,
)


# ─────────────────────────────────────────────
# ScholarshipType Views
# ─────────────────────────────────────────────

class ScholarshipTypeListCreateView(APIView):
    """GET  /scholarships/api/types/  – list all active types
       POST /scholarships/api/types/  – create a new type"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        scholarship_types = get_all_scholarship_types()
        serializer = ScholarshipTypeSerializer(scholarship_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        return Response({"detail": "Adding new scholarships has been disabled. You can only edit the default scholarships."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ScholarshipTypeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        scholarship_type = create_scholarship_type(
            name=data["name"],
            category=data["category"],
            description=data["description"],
            amount=data["amount"],
            frequency=data["frequency"],
            eligibility_criteria=data["eligibility_criteria"],
            max_backlogs=data.get("max_backlogs", 0),
            applicable_categories=data.get("applicable_categories", ""),
            programme_ids=[p.id for p in data.get("applicable_programmes", [])],
            batch_ids=[b.id for b in data.get("applicable_batches", [])],
        )
        return Response(
            ScholarshipTypeSerializer(scholarship_type).data,
            status=status.HTTP_201_CREATED,
        )


class ScholarshipTypeDetailView(APIView):
    """GET    /scholarships/api/types/<id>/  – retrieve
       PATCH  /scholarships/api/types/<id>/  – update
       DELETE /scholarships/api/types/<id>/  – deactivate"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            scholarship_type = get_scholarship_type_by_id(pk)
        except ScholarshipType.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScholarshipTypeSerializer(scholarship_type).data)

    def patch(self, request, pk):
        from applications.globals.models import HoldsDesignation
        is_spacs_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__in=["spacs_convener", "spacsconvenor"]
        ).exists()
        if not is_spacs_staff:
            return Response({"detail": "Only spacs_convener can edit scholarship types."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ScholarshipTypeSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            scholarship_type = update_scholarship_type(
                pk,
                programme_ids=[p.id for p in data.pop("applicable_programmes", [])] or None,
                batch_ids=[b.id for b in data.pop("applicable_batches", [])] or None,
                **data,
            )
        except ScholarshipNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScholarshipTypeSerializer(scholarship_type).data)

    def delete(self, request, pk):
        try:
            deactivate_scholarship_type(pk)
        except ScholarshipNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# ScholarshipApplication Views
# ─────────────────────────────────────────────

class ScholarshipApplicationListCreateView(APIView):
    """GET  /scholarships/api/applications/  – list all applications
       POST /scholarships/api/applications/  – submit a new application"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from applications.globals.models import HoldsDesignation

        is_spacs_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__in=["spacs_assistant", "spacs_convener", "spacsassistant", "spacsconvenor"],
        ).exists()

        if is_spacs_staff:
            applications = get_all_applications()
        else:
            applications = get_applications_for_user(request.user)

        serializer = ScholarshipApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ScholarshipApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            print("SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        docs = request.FILES.getlist("supporting_documents") or request.FILES.getlist("supporting_documents[]")
        doc = docs[0] if docs else None

        data = serializer.validated_data
        try:
            status_val = request.data.get("status", "PENDING")
            application = create_scholarship_application(
                student_id=data["student"].id,
                scholarship_type_id=data["scholarship_type"].id,
                academic_year=data["academic_year"],
                semester=data["semester"],
                remarks=data.get("remarks", ""),
                document=doc,
                category=data.get("category", ""),
                cpi=data.get("cpi"),
                annual_family_income=data.get("annual_family_income"),
                status=status_val,
            )
        except ScholarshipNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except DuplicateApplicationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except EligibilityError as exc:
            return Response({"detail": str(exc), "reasons": exc.reasons}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(
            ScholarshipApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class ScholarshipApplicationDetailView(APIView):
    """GET    /scholarships/api/applications/<id>/  – retrieve single application
       DELETE /scholarships/api/applications/<id>/  – cancel a PENDING application"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            application = get_application_by_id(pk)
        except Exception:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScholarshipApplicationDetailSerializer(application).data)

    def delete(self, request, pk):
        try:
            cancel_scholarship_application(pk)
        except ApplicationNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        docs = request.FILES.getlist("supporting_documents") or request.FILES.getlist("supporting_documents[]")
        doc = docs[0] if docs else None
        
        kwargs = {}
        for field in ["academic_year", "semester", "category", "cpi", "annual_family_income", "contact_number", "remarks", "status"]:
            if field in request.data:
                kwargs[field] = request.data[field]

        try:
            student = request.user.extrainfo.student
            updated_application = amend_scholarship_application(pk, student, document=doc, **kwargs)
        except ApplicationNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except InvalidStatusTransition as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(ScholarshipApplicationDetailSerializer(updated_application).data, status=status.HTTP_200_OK)


class ApplicationStatusUpdateView(APIView):
    """PATCH /scholarships/api/applications/<id>/update-status/  – approve / reject / needs info"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            application = update_application_status(
                application_id=pk,
                new_status=data["new_status"],
                reviewer=request.user.extrainfo,
                review_remarks=data.get("review_remarks", ""),
                amount_approved=data.get("amount_approved"),
            )
        except ApplicationNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(ScholarshipApplicationSerializer(application).data)

class ApplicationDisbursementView(APIView):
    """POST /scholarships/api/applications/<id>/disburse/  – record disbursement"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = DisbursementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            application = record_disbursement(
                application_id=pk,
                transaction_reference=serializer.validated_data["transaction_reference"],
            )
        except ApplicationNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except InvalidStatusTransition as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(ScholarshipApplicationSerializer(application).data)


class EligibleStudentsView(APIView):
    """GET /scholarships/api/eligible-students/<scholarship_id>/  – students eligible for a scholarship"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            scholarship_type = get_scholarship_type_by_id(pk)
        except ScholarshipType.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        students = get_eligible_students_for_scholarship(scholarship_type)
        serializer = EligibleStudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
