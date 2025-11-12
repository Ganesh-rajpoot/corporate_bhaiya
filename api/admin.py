from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from api.models import Bot
from django.db.models import Avg, Count
from .utils import generate_slots_for_mentor

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'get_mobile', 'is_mentor', 'verified_mentor', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('is_mentor', 'verified_mentor', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'name', 'mobile')
    ordering = ('email',)
    list_per_page = 20

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'mobile', 'is_mentor', 'verified_mentor')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_mentor', 'verified_mentor', 'mobile'),
        }),
    )

    actions = ['activate_users', 'deactivate_users']

    def get_mobile(self, obj):
        return obj.mobile
    get_mobile.short_description = "Mobile Number"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} users activated.")
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

admin.site.register(User, UserAdmin)

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience', 'slot_duration', 'future_weeks', 'date_joined')
    fields = ('user', 'bio', 'experience', 'skills', 'schedules', 'slot_duration', 'future_weeks', 'mobile', 'goals', 'linkedin', 'courses', 'company', 'image')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and any(field in form.changed_data for field in ['schedules', 'slot_duration', 'future_weeks']):
            generate_slots_for_mentor(obj)



@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'college')
    search_fields = ('user__email', 'college')



@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('mentor', 'is_booked')
    search_fields = ('mentor__email',)
    ordering = ('start_time',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'image','students')
    search_fields = ('title',)
    ordering = ('title',)   


@admin.register(SQLCertificate)
class SQLCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'registration_number',
        'name',
        'certificate_name',
        'issuing_organization',
        'issue_date',
        'is_verified',
        'verified_at',
    )
    search_fields = ('registration_number', 'issuing_organization')
    list_filter = ('is_verified', 'issuing_organization')
    readonly_fields = ('verified_at',)

    def save_model(self, request, obj, form, change):
        # Auto-set verified_at timestamp when verified is True and not already set
        if obj.is_verified and not obj.verified_at:
            from django.utils import timezone
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company_name',
        'job_type',
        'location',
        'posted_by',
        'posted_at',
        'deadline',
    )
    search_fields = ('title', 'company_name', 'skills_required', 'location')
    list_filter = ('job_type', 'posted_at', 'deadline')
    autocomplete_fields = ['posted_by']
    ordering = ['-posted_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'job',
        'student',
        'applied_at',
        'status',
    )
    search_fields = ('student__email', 'job__title')
    list_filter = ('status', 'applied_at')
    autocomplete_fields = ['student', 'job']
    ordering = ['-applied_at']

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'student', 'job', 'status', 'referred_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'mentor', 'rating', 'created_at')
    search_fields = ('student__email', 'mentor__email')
    list_filter = ('rating', 'created_at')
     # Optional: custom admin action to show average rating per mentor in the console/logs
    actions = ['show_average_ratings']

    def show_average_ratings(self, request, queryset):
        from django.contrib import messages
        data = (
            queryset.values('mentor__email')
            .annotate(avg_rating=Avg('rating'), review_count=Count('id'))
            .order_by('-avg_rating')
        )
        for item in data:
            messages.info(request, f"{item['mentor__email']} → {round(item['avg_rating'], 2)} stars ({item['review_count']} reviews)")
    show_average_ratings.short_description = "Show average rating per mentor (in messages)"

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'button_text','join_url')
    search_fields = ('title',)

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ("bot_page_heading", "bot_page_subheading", "is_active", "created_at", "updated_at")
    search_fields = ("bot_page_heading", "bot_page_subheading")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_name",
        "mentor_name",
        "date",
        "start_time",
        "end_time",
        "is_completed",
    )
    list_filter = ("is_completed", "slot__date")
    search_fields = (
        "student__user__name",
        "student__user__email",
        "slot__mentor__user__name",
        "slot__mentor__user__email",
    )
    ordering = ("-slot__date", "slot__start_time")

    # Custom columns
    def student_name(self, obj):
        return obj.student.user.name
    student_name.short_description = "Student"

    def mentor_name(self, obj):
        return obj.slot.mentor.user.name
    mentor_name.short_description = "Mentor"

    def date(self, obj):
        return obj.slot.date
    date.admin_order_field = "slot__date"

    def start_time(self, obj):
        return obj.slot.start_time

    def end_time(self, obj):
        return obj.slot.end_time