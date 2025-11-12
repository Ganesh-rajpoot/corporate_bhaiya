from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from corporate_bhaiya import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.conf import settings
from datetime import timedelta, date, time, datetime
import datetime as dt

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, is_mentor=False,mobile=None):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, is_mentor=is_mentor, is_active=True,mobile=mobile)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password, is_mentor=False)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    verified_mentor = models.BooleanField(default=False)
    user_role = models.CharField(max_length=20, default='student')  # 'student' or 'mentor'
    is_mentor = models.BooleanField(default=False)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    confirmPassword = models.CharField(max_length=128, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email
    
class MentorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    experience = models.IntegerField(default=0)
    skills = models.CharField(max_length=255, blank=True)
    
    schedules = models.JSONField(default=list)  # Stores array of {day, available, startTime, endTime}
    slot_duration = models.IntegerField(default=30)  # minutes
    future_weeks = models.IntegerField(default=2)   # how many weeks ahead
    
    mobile = models.CharField(max_length=15, blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    courses = models.ManyToManyField('Course', blank=True)
    company = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='mentor_images/', blank=True, null=True)

    def __str__(self):
        return self.user.email

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    college = models.CharField(max_length=255, blank=True)
    interests = models.TextField(blank=True)
    course = models.ManyToManyField('Course', blank=True)

    def __str__(self):
        return self.user.email



class Slot(models.Model):
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    seats = models.PositiveIntegerField(default=1)
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('mentor', 'date', 'start_time', 'end_time')  # ✅ Prevent duplicates

    def __str__(self):
        return f"{self.mentor.user.email} - {self.date} ({self.start_time} - {self.end_time})"

class Booking(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booked by {self.student.email} for {self.slot}"


class Course(models.Model):
    image = models.ImageField(upload_to='course_images/')
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    duration = models.CharField(max_length=100)  # e.g., "3 months"
    students = models.PositiveIntegerField()
    join_url = models.URLField()

    def __str__(self):
        return self.title

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('internship', 'Internship'),
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('freelance', 'Freelance'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    stipend_or_salary = models.CharField(max_length=100, blank=True, null=True)
    skills_required = models.CharField(max_length=255, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    posted_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(blank=True, null=True)
    apply_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"


class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    resume_url = models.URLField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')  # e.g., pending, reviewed, selected, rejected

    def __str__(self):
        return f"{self.student.email} applied for {self.job.title}"

class SQLCertificate(models.Model):
    registration_number = models.CharField(max_length=50, unique=True)
    certificate_name = models.CharField(max_length=255, default="SQL Certification")
    issuing_organization = models.CharField(max_length=255)
    issue_date = models.DateField()
    name = models.CharField(max_length=50,null=True)
    certificate_url = models.URLField(blank=True, null=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.registration_number}"


class Referral(models.Model):
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_referrals')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_referrals')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='referrals')
    message = models.TextField(blank=True, null=True)
    resume_url = models.URLField(blank=True, null=True)  # if mentor wants to upload/attach resume
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending')
    referred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mentor.email} referred {self.student.email} for {self.job.title}"


class ReferralRequest(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_requests')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incoming_requests')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        limit_choices_to={'user_role': 'student'}
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        limit_choices_to={'user_role': 'mentor'}
    )
    rating = models.PositiveSmallIntegerField()  # 1 to 5 typically
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'mentor')  # Optional: one review per student per mentor
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email} rated {self.mentor.email} - {self.rating}⭐"

class Bot(models.Model):
    image = models.ImageField(upload_to='bot_images/')
    title = models.CharField(max_length=255)
    button_text = models.CharField(max_length=100, default="Practice with Bot")
    join_url = models.CharField(max_length=100, default="sql.corporatebhaiya.in")

    def __str__(self):
        return self.title

class PageContent(models.Model):
    bot_page_heading = models.CharField(max_length=255, help_text="Heading for Bot page")
    bot_page_subheading = models.CharField(max_length=255, help_text="Subheading for Bot page")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this content was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this content was last updated")
    is_active = models.BooleanField(default=True, help_text="Set inactive if this content should not be visible")

    class Meta:
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.bot_page_heading
