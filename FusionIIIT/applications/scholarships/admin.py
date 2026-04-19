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


@admin.register(ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
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


@admin.register(AwardRecipient)
class AwardRecipientAdmin(admin.ModelAdmin):
    list_display  = ("student", "award", "academic_year", "award_date", "certificate_issued")
    list_filter   = ("academic_year", "certificate_issued")
    search_fields = ("student__id__id", "award__name")


@admin.register(MeritList)
class MeritListAdmin(admin.ModelAdmin):
    list_display  = ("batch", "academic_year", "semester", "generated_date")
    list_filter   = ("academic_year", "semester")


@admin.register(MeritListEntry)
class MeritListEntryAdmin(admin.ModelAdmin):
    list_display  = ("merit_list", "student", "rank")
    list_filter   = ("merit_list__academic_year",)
    search_fields = ("student__id__id",)

