<<<<<<< HEAD
from django.contrib import admin

# Register your models here.
from .models import (Award_and_scholarship, Director_gold, Director_silver,
                     Mcm, Notional_prize, Previous_winner, Proficiency_dm,
                     Release,Notification,Application)

admin.site.register(Mcm),
admin.site.register(Award_and_scholarship),
admin.site.register(Previous_winner),
admin.site.register(Release),
admin.site.register(Proficiency_dm),
admin.site.register(Director_silver),
admin.site.register(Director_gold),
admin.site.register(Notional_prize),
admin.site.register(Notification),
admin.site.register(Application),


from .models import (
    Award,
    AwardRecipient,
    MeritList,
    MeritListEntry,
    ScholarshipApplication,
    ScholarshipType,
)


@admin.register(ScholarshipType)
class ScholarshipTypeAdmin(admin.ModelAdmin):
    list_display  = ("name", "category", "amount", "frequency", "is_active", "created_at")
    list_filter   = ("category", "is_active", "frequency")
    search_fields = ("name", "description")
    filter_horizontal = ("applicable_programmes", "applicable_batches")
=======
﻿from django.contrib import admin
from .models import (
    Award_and_scholarship, Release, Application, Mcm,
    Director_gold, Director_silver, Proficiency_dm, Previous_winner,
    ExtendedScholarshipType, ScholarshipApplication,
    Award, AwardRecipient, MeritList, MeritListEntry, ScholarshipEligibilityLog
)


@admin.register(Award_and_scholarship)
class AwardAndScholarshipAdmin(admin.ModelAdmin):
    list_display = ('award_name', 'award_type')
    search_fields = ('award_name',)


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('award', 'batch', 'programme', 'startdate', 'enddate', 'notif_visible')
    list_filter = ('award', 'programme', 'notif_visible')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'award', 'status', 'created_at')
    list_filter = ('status', 'award')
    search_fields = ('student__id__id',)


@admin.register(ExtendedScholarshipType)
class ExtendedScholarshipTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'amount', 'frequency', 'max_backlogs', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('applicable_programmes', 'applicable_batches')
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e


@admin.register(ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display  = ("student", "scholarship_type", "academic_year", "semester", "status", "application_date")
    list_filter   = ("status", "academic_year", "semester")
    search_fields = ("student__id__id", "scholarship_type__name")
    readonly_fields = ("application_date",)


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display  = ("name", "category", "prize_amount", "certificate_provided", "is_active")
    list_filter   = ("category", "is_active")
    search_fields = ("name", "description")
    filter_horizontal = ("applicable_programmes",)
=======
    list_display = ('student', 'scholarship_type', 'academic_year', 'semester', 'status', 'application_date')
    list_filter = ('status', 'academic_year', 'scholarship_type')
    search_fields = ('student__id__id', 'scholarship_type__name')
    readonly_fields = ('application_date', 'category_at_application')


@admin.register(Award)
class GeneralAwardAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'prize_amount', 'certificate_provided', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('applicable_programmes',)
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e


@admin.register(AwardRecipient)
class AwardRecipientAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display  = ("student", "award", "academic_year", "award_date", "certificate_issued")
    list_filter   = ("academic_year", "certificate_issued")
    search_fields = ("student__id__id", "award__name")
=======
    list_display = ('student', 'award', 'academic_year', 'award_date', 'certificate_issued')
    list_filter = ('award', 'academic_year', 'certificate_issued')
    search_fields = ('student__id__id', 'award__name')
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e


@admin.register(MeritList)
class MeritListAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display  = ("batch", "academic_year", "semester", "generated_date")
    list_filter   = ("academic_year", "semester")
=======
    list_display = ('batch', 'programme', 'academic_year', 'semester', 'generated_date')
    list_filter = ('batch', 'academic_year')
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e


@admin.register(MeritListEntry)
class MeritListEntryAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display  = ("merit_list", "student", "rank")
    list_filter   = ("merit_list__academic_year",)
    search_fields = ("student__id__id",)

=======
    list_display = ('merit_list', 'student', 'rank', 'cgpa', 'eligible_for_scholarships')
    list_filter = ('merit_list', 'eligible_for_scholarships')


admin.site.register(Mcm)
admin.site.register(Director_gold)
admin.site.register(Director_silver)
admin.site.register(Proficiency_dm)
admin.site.register(Previous_winner)
admin.site.register(ScholarshipEligibilityLog)
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
