import datetime

from django.db import models

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo


class Constants:
    STATUS_CHOICES = (
        ('Complete', 'COMPLETE'),
        ('Incomplete', 'INCOMPLETE'),
        ('Reject', 'REJECT'),
        ('Accept', 'ACCEPT')

    )
    TIME = (
        ('0', '12 Midnight'),
        ('1am', '1'),
        ('2am', '2'),
        ('3am', '3'),
        ('4am', '4'),
        ('5am', '5'),
        ('6am', '6'),
        ('7am', '7'),
        ('8am', '8'),
        ('9am', '9'),
        ('10am', '10'),
        ('11am', '11'),
        ('12 Noon', '12'),
        ('1pm', '13'),
        ('2pm', '14'),
        ('3pm', '15'),
        ('4pm', '16'),
        ('5pm', '17'),
        ('6pm', '18'),
        ('7pm', '19'),
        ('8pm', '20'),
        ('9pm', '21'),
        ('10pm', '22'),
        ('11pm', '23'),
        ('12 Midnight', '0')
    )
    BATCH = (
        ('UG1', 'UG1'),
        ('UG2', 'UG2'),
        ('UG3', 'UG3'),
        ('UG4', 'UG4'),
        ('PG1', 'PG1'),
        ('PG2', 'PG2')
    )
    FATHER_OCC_CHOICE = (
        ('government', 'Government'),
        ('private', 'Private'),
        ('public', 'Public'),
        ('business', 'Business'),
        ('medical', 'Medical'),
        ('consultant', 'Consultant'),
        ('pensioners', 'Pensioners')
    )
    MOTHER_OCC_CHOICES = (
        ('EMPLOYED', 'EMPLOYED'),
        ('HOUSE_WIFE', 'HOUSE_WIFE')
    )
    HOUSE_TYPE_CHOICES = (
        ('RENTED', 'RENTED'),
        ('OWNED', 'OWNED')
    )


class Award_and_scholarship(models.Model):
    award_name = models.CharField(max_length=100, default='')
    catalog = models.TextField(max_length=5000)

    class Meta:
        db_table = 'Award_and_scholarship'

    def __str__(self):
        return self.award_name


class Mcm(models.Model):
    brother_name = models.CharField(max_length=30, null=True)
    brother_occupation = models.TextField(max_length=100, null=True)
    sister_name = models.CharField(max_length=30, null=True)
    sister_occupation = models.TextField(max_length=100, null=True)
    income_father = models.IntegerField(default=0)
    income_mother = models.IntegerField(default=0)
    income_other = models.IntegerField(default=0)
    father_occ = models.CharField(max_length=10,
                                  choices=Constants.FATHER_OCC_CHOICE,
                                  default='')
    mother_occ = models.CharField(max_length=10,
                                  choices=Constants.MOTHER_OCC_CHOICES,
                                  default='')
    father_occ_desc = models.CharField(max_length=30, null=True)
    mother_occ_desc = models.CharField(max_length=30, null=True)
    four_wheeler = models.IntegerField(blank=True, null=True)
    four_wheeler_desc = models.CharField(max_length=30, null=True)
    two_wheeler = models.IntegerField(blank=True, null=True)
    two_wheeler_desc = models.CharField(max_length=30, null=True)
    house = models.CharField(max_length=10, null=True)
    plot_area = models.IntegerField(blank=True, null=True)
    constructed_area = models.IntegerField(blank=True, null=True)
    school_fee = models.IntegerField(blank=True, null=True)
    school_name = models.CharField(max_length=30, null=True)
    bank_name = models.CharField(max_length=100, null=True)
    loan_amount = models.IntegerField(blank=True, null=True)
    college_fee = models.IntegerField(blank=True, null=True)
    college_name = models.CharField(max_length=30, null=True)
    income_certificate = models.FileField(null=True, blank=True)
    forms = models.FileField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    student = models.ForeignKey(Student,
                                on_delete=models.CASCADE, related_name='mcm_info')
    annual_income = models.IntegerField(default=0)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)


    class Meta:
        db_table = 'Mcm'

    def __str__(self):
        return str(self.student)


class Notional_prize(models.Model):
    spi = models.FloatField()
    cpi = models.FloatField()
    year = models.CharField(max_length=10, choices=Constants.BATCH)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)


    class Meta:
        db_table = 'Notional_prize'

#Addition: a column programme added
class Previous_winner(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    programme = models.CharField(max_length=10,default='B.Tech')
    year = models.IntegerField(default=datetime.datetime.now().year)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Previous_winner'


class Release(models.Model):
    date_time = models.DateTimeField(default=datetime.datetime.now, blank=True)
    programme = models.CharField(max_length=10,default='B.Tech')
    startdate = models.DateField(default=datetime.date.today)
    enddate = models.DateField()
    award = models.CharField(default='',max_length=50)
    remarks = models.TextField(max_length=500,default='')
    batch = models.TextField(default='all')
    notif_visible = models.IntegerField(default=1)

    class Meta:
        db_table = 'Release'

# new class added for keeping track of notifications and applied application by students
class Notification(models.Model):
    release_id = models.ForeignKey(Release,default=None, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
    notification_mcm_flag = models.BooleanField(default=False)
    notification_convocation_flag = models.BooleanField(default=False)
    invite_mcm_accept_flag = models.BooleanField(default=False)
    invite_convocation_accept_flag = models.BooleanField(default=False)
    def __str__(self):
        return str(self.student_id)

    class Meta:
        db_table = 'Notification'

class Application(models.Model):
    application_id = models.CharField(max_length = 100, primary_key=True)
    student_id = models.ForeignKey(ExtraInfo, on_delete = models.CASCADE)
    applied_flag = models.BooleanField(default=False)
    award = models.CharField(max_length = 30)

    def __str__(self):
        return str(self.application_id)

    class Meta:
        db_table = 'Application'

class Director_silver(models.Model):
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    award_type = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES,default='INCOMPLETE')
    relevant_document = models.FileField(null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    inside_achievements = models.TextField(max_length=1000, null=True)
    justification = models.TextField(max_length=1000, null=True)
    outside_achievements = models.TextField(max_length=1000, null=True)


    class Meta:
        db_table = 'Director_silver'


class Proficiency_dm(models.Model):
    relevant_document = models.FileField(null=True, blank=True)
    title_name = models.CharField(max_length=30, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    award_type = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES,default='INCOMPLETE')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    no_of_students = models.IntegerField(default=1)
    date = models.DateField(default=datetime.date.today)
    roll_no1 = models.IntegerField(default=0)
    roll_no2 = models.IntegerField(default=0)
    roll_no3 = models.IntegerField(default=0)
    roll_no4 = models.IntegerField(default=0)
    roll_no5 = models.IntegerField(default=0)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    brief_description = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    ece_topic = models.CharField(max_length=25,null=True)
    cse_topic = models.CharField(max_length=25,null=True)
    mech_topic = models.CharField(max_length=25,null=True)
    design_topic = models.CharField(max_length=25,null=True)
    ece_percentage = models.IntegerField(null=True)
    cse_percentage = models.IntegerField(null=True)
    mech_percentage = models.IntegerField(null=True)
    design_percentage = models.IntegerField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)


    class Meta:
        db_table = 'Proficiency_dm'


class Director_gold(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=10,choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    correspondence_address = models.TextField(max_length=40, default='address')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    relevant_document = models.FileField(null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    academic_achievements = models.TextField(max_length=1000 ,null=True)
    science_inside = models.TextField(max_length=1000 ,null=True)
    science_outside = models.TextField(max_length=1000 ,null=True)
    games_inside = models.TextField(max_length=1000 ,null=True)
    games_outside = models.TextField(max_length=1000 ,null=True)
    cultural_inside = models.TextField(max_length=1000 ,null=True)
    cultural_outside = models.TextField(max_length=1000 ,null=True)
    social = models.TextField(max_length=1000 ,null=True)
    corporate = models.TextField(max_length=1000 ,null=True)
    hall_activities = models.TextField(max_length=1000 ,null=True)
    gymkhana_activities = models.TextField(max_length=1000 ,null=True)
    institute_activities = models.TextField(max_length=1000 ,null=True)
    counselling_activities = models.TextField(max_length=1000 ,null=True)
    other_activities = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = 'Director_gold'



from applications.programme_curriculum.models import Batch, Discipline, Programme



# ─────────────────────────────────────────────
# Choices (TextChoices / IntegerChoices)
# ─────────────────────────────────────────────

class ScholarshipCategory(models.TextChoices):
    MERIT    = "MERIT",    "Merit-based"
    NEED     = "NEED",     "Need-based"
    CATEGORY = "CATEGORY", "Category-based"
    SPORTS   = "SPORTS",   "Sports"
    CULTURAL = "CULTURAL", "Cultural"
    RESEARCH = "RESEARCH", "Research"
    EXTERNAL = "EXTERNAL", "External / Government"


class ApplicationStatus(models.TextChoices):
    DRAFT        = "DRAFT",        "Draft"
    PENDING      = "PENDING",      "Pending"
    WITHDRAWAL_REQUESTED = "WITHDRAWAL_REQUESTED", "Withdrawal Requested"
    WITHDRAWN    = "WITHDRAWN",    "Withdrawn"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    FORWARDED    = "FORWARDED",    "Forwarded"
    APPROVED     = "APPROVED",     "Approved"
    REJECTED     = "REJECTED",     "Rejected"
    DISBURSED    = "DISBURSED",    "Disbursed"


class AwardCategory(models.TextChoices):
    ACADEMIC   = "ACADEMIC",   "Academic Excellence"
    RESEARCH   = "RESEARCH",   "Research"
    SPORTS     = "SPORTS",     "Sports"
    CULTURAL   = "CULTURAL",   "Cultural"
    INNOVATION = "INNOVATION", "Innovation"
    LEADERSHIP = "LEADERSHIP", "Leadership"
    COMMUNITY  = "COMMUNITY",  "Community Service"


class FrequencyChoice(models.TextChoices):
    MONTHLY   = "MONTHLY",   "Monthly"
    SEMESTER  = "SEMESTER",  "Semester"
    ANNUAL    = "ANNUAL",    "Annual"
    ONE_TIME  = "ONE_TIME",  "One-time"


# ─────────────────────────────────────────────
# Core Models
# ─────────────────────────────────────────────

class ScholarshipType(models.Model):
    """
    Defines the types / schemes of scholarships offered by the institute
    or forwarded from external / government bodies.
    """
    name                  = models.CharField(max_length=200)
    category              = models.CharField(max_length=20, choices=ScholarshipCategory.choices)
    description           = models.TextField()
    amount                = models.DecimalField(max_digits=10, decimal_places=2)
    frequency             = models.CharField(max_length=20, choices=FrequencyChoice.choices)
    eligibility_criteria  = models.TextField()
    cpi_cutoff            = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    annual_family_income_limit = models.IntegerField(default=0)
    max_backlogs          = models.IntegerField(default=0)
    # Comma-separated category codes: e.g., "GEN,SC,ST,OBC"
    applicable_categories = models.CharField(max_length=50, blank=True)
    applicable_programmes = models.ManyToManyField(Programme, blank=True, related_name="scholarship_types")
    applicable_batches    = models.ManyToManyField(Batch, blank=True, related_name="scholarship_types")
    deadline              = models.DateField(null=True, blank=True)
    is_active             = models.BooleanField(default=True)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scholarships_scholarshiptype"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ScholarshipApplication(models.Model):
    """
    Tracks a student's application for a particular scholarship scheme
    within an academic year and semester.
    """
    student               = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="scholarship_applications")
    scholarship_type      = models.ForeignKey(ScholarshipType, on_delete=models.CASCADE, related_name="applications")
    academic_year         = models.CharField(max_length=9)          # e.g., "2024-25"
    semester              = models.IntegerField()

    # Snapshot of category at the time of application
    category_at_application = models.CharField(max_length=10)

    # Applicant submission
    contact_number         = models.CharField(max_length=15, null=True, blank=True)
    application_date       = models.DateTimeField(auto_now_add=True)
    cpi                    = models.FloatField(null=True, blank=True)
    annual_family_income   = models.IntegerField(null=True, blank=True)
    supporting_documents   = models.FileField(upload_to="scholarships/documents/", null=True, blank=True)
    remarks                = models.TextField(blank=True)

    # Workflow
    status                 = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    reviewed_by            = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_scholarship_applications")
    review_date            = models.DateTimeField(null=True, blank=True)
    review_remarks         = models.TextField(blank=True)

    # Disbursement
    amount_approved        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disbursement_date      = models.DateTimeField(null=True, blank=True)
    transaction_reference  = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table        = "scholarships_scholarshipapplication"
        unique_together = ["student", "scholarship_type", "academic_year", "semester"]
        ordering        = ["-application_date"]

    def __str__(self):
        return f"{self.student.id} – {self.scholarship_type.name} ({self.academic_year})"


class Award(models.Model):
    """
    Institute-level award definitions (academic, sports, cultural, etc.).
    """
    name                  = models.CharField(max_length=200)
    category              = models.CharField(max_length=20, choices=AwardCategory.choices)
    description           = models.TextField()
    criteria              = models.TextField()
    prize_amount          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certificate_provided  = models.BooleanField(default=True)
    applicable_programmes = models.ManyToManyField(Programme, blank=True, related_name="awards")
    is_active             = models.BooleanField(default=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scholarships_award"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class AwardRecipient(models.Model):
    """
    Records which student received which award in which academic year.
    """
    award             = models.ForeignKey(Award, on_delete=models.CASCADE, related_name="recipients")
    student           = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="awards_received")
    academic_year     = models.CharField(max_length=9)
    award_date        = models.DateField()
    citation          = models.TextField(blank=True)
    certificate_issued = models.BooleanField(default=False)
    awarded_by        = models.ForeignKey(ExtraInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="awards_given")

    class Meta:
        db_table        = "scholarships_awardrecipient"
        unique_together = ["award", "student", "academic_year"]
        ordering        = ["-award_date"]

    def __str__(self):
        return f"{self.student_id} – {self.award.name} ({self.academic_year})"


class MeritList(models.Model):
    """
    Header record for a batch-semester merit list generation.
    """
    batch          = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="merit_lists")
    academic_year  = models.CharField(max_length=9)
    semester       = models.IntegerField()
    generated_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "scholarships_meritlist"
        unique_together = ["batch", "academic_year", "semester"]
        ordering        = ["-generated_date"]

    def __str__(self):
        return f"Merit List – {self.batch} | {self.academic_year} Sem-{self.semester}"


class MeritListEntry(models.Model):
    """
    Individual student rank entry within a MeritList.
    """
    merit_list = models.ForeignKey(MeritList, on_delete=models.CASCADE, related_name="entries")
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="merit_entries")
    rank       = models.IntegerField()

    class Meta:
        db_table        = "scholarships_meritlistentry"
        unique_together = ["merit_list", "student"]
        ordering        = ["rank"]

    def __str__(self):
        return f"Rank {self.rank} – {self.student_id} in {self.merit_list}"

