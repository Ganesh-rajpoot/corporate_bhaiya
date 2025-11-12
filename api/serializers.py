from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from django.db.models import Avg, Count
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_role = serializers.ChoiceField(choices=[("student", "Student"), ("mentor", "Mentor")])

    # Role-specific 
    bio = serializers.CharField(required=False, allow_blank=True)
    experience = serializers.IntegerField(required=False)
    skills = serializers.CharField(required=False, allow_blank=True)
    available_days = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    college = serializers.CharField(required=False, allow_blank=True)
    interests = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "name", "password", "user_role", "bio"]

    def create(self, validated_data):
        role = validated_data.pop("user_role")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=password,
            is_mentor=(role == "mentor")
        )
        user.user_role = role
        user.save()

        # Create role-specific profile
        if role == "mentor":
            MentorProfile.objects.create(
                user=user,
                bio=validated_data.get("bio", ""),
                experience=validated_data.get("experience", 0),
                skills=validated_data.get("skills", ""),
                available_days=validated_data.get("available_days"),
                company=validated_data.get("company", "")
            )
        elif role == "student":
            StudentProfile.objects.create(
                user=user,
                college=validated_data.get("college", ""),
                interests=validated_data.get("interests", "")
            )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data.get("email"), password=data.get("password"))
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['name', 'email', 'mobile', 'linkedin','password','user_role']
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'mobile': {'required': False},
            'linkedin': {'required': False},
        }
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class MentorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        #fields = '__all__'
        exclude = ['user']

    def validate_schedules(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Schedules must be a list.")
        for schedule in value:
            if not isinstance(schedule, dict):
                raise serializers.ValidationError(f"Invalid schedule format for {schedule}.")
            if schedule.get('available'):
                try:
                    start_time = datetime.strptime(schedule['startTime'], '%H:%M').time()
                    end_time = datetime.strptime(schedule['endTime'], '%H:%M').time()
                    if start_time >= end_time:
                        raise serializers.ValidationError(
                            f"endTime must be after startTime for {schedule['day']}"
                        )
                except ValueError:
                    raise serializers.ValidationError(
                        f"Invalid time format for {schedule['day']}. Use HH:MM."
                    )
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            'college',
            'interests'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'mobile', 'user_role', 'bio', 'linkedin','date_joined']
        read_only_fields = ['email', 'user_role']  # email & role change nahi honi chahiye



class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'



class MentorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = ['available_days', 'start_time', 'end_time', 'slot_duration', 'future_weeks']


class SlotSerializer(serializers.ModelSerializer):
    mentor_email = serializers.EmailField(source='mentor.email', read_only=True)

    class Meta:
        model = Slot
        # fields = ['id', 'mentor', 'mentor_email', 'start_time', 'end_time', 'is_booked']
        fields = ['id', 'mentor', 'date', 'start_time', 'end_time', 'seats', 'is_booked','mentor_email']

        read_only_fields = ['is_booked']

class BookingSerializer(serializers.ModelSerializer):
    slot = SlotSerializer(read_only=True)
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'student', 'student_email', 'slot', 'booked_at']
        read_only_fields = ['booked_at']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    posted_by = serializers.ReadOnlyField(source='posted_by.email')

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['posted_by', 'posted_at']


class JobApplicationSerializer(serializers.ModelSerializer):
    student = serializers.ReadOnlyField(source='student.email')

    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ['student', 'applied_at']

class SQLCertificateAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SQLCertificate
        fields = '__all__'


class SQLCertificateVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = SQLCertificate
        fields = [
            'registration_number',
            'name',
            'certificate_name',
            'issuing_organization',
            'issue_date',
            'certificate_url',
            'is_verified',
            'verified_at',
            'remarks'
        ]
        read_only_fields = fields

class ReferralSerializer(serializers.ModelSerializer):
    mentor_email = serializers.EmailField(source='mentor.email', read_only=True)
    student_email = serializers.EmailField(source='student.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Referral
        fields = '__all__'

class ReferralRequestSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    mentor_email = serializers.EmailField(source='mentor.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = ReferralRequest
        fields = '__all__'
        read_only_fields = ['status', 'requested_at', 'student']

class ReviewSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    mentor_email = serializers.EmailField(source='mentor.email', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'student', 'mentor', 'student_email', 'mentor_email', 'rating', 'review_text', 'created_at']
        read_only_fields = ['student', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        request = self.context['request']
        if request.user.user_role != 'student':
            raise serializers.ValidationError("Only students can post reviews.")
        return data

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)

class MentorAverageRatingSerializer(serializers.Serializer):
    mentor_id = serializers.IntegerField()
    mentor_name = serializers.CharField()
    mentor_email = serializers.EmailField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()

# class MentorPublicSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(source='user.id') 
#     name = serializers.CharField(source='user.name')
#     image = serializers.SerializerMethodField()
#     role = serializers.SerializerMethodField()
#     company = serializers.SerializerMethodField()
#     linkedin = serializers.URLField()
#     experience = serializers.SerializerMethodField()
#     route = serializers.SerializerMethodField()
#     buttonText = serializers.SerializerMethodField()
#     skills = serializers.SerializerMethodField()
#     courses = serializers.SerializerMethodField()
#     average_rating = serializers.SerializerMethodField()

#     class Meta:
#         model = MentorProfile
#         fields = [
#            'id','name', 'image', 'role', 'experience', 'company',
#             'linkedin', 'route', 'buttonText', 'bio',
#             'skills', 'courses', 'average_rating'
#         ]

#     def get_image(self, obj):
#         request = self.context.get('request')
#         if obj.image and request:
#             return request.build_absolute_uri(obj.image.url)
#         return None

#     def get_role(self, obj):
#         return "Mentor"
    
#     def get_company(self,obj):
#        return obj.company

#     def get_experience(self, obj):
#         return f"{obj.experience}+ years"

#     def get_route(self, obj):
#         slug = obj.user.id
#         return f"/mentor/{slug}"

#     def get_buttonText(self, obj):
#         return "Know More"

#     def get_skills(self, obj):
#         return [skill.strip() for skill in obj.skills.split(",")] if obj.skills else []

#     def get_courses(self, obj):
#         return list(obj.courses.values_list('title', flat=True))

#     def get_average_rating(self, obj):
#         avg = Review.objects.filter(mentor=obj.user).aggregate(avg_rating=Avg('rating'))
#         return round(avg['avg_rating'], 2) if avg['avg_rating'] else None

class MentorPublicSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id') 
    name = serializers.CharField(source='user.name')
    image = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    linkedin = serializers.URLField()
    experience = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    buttonText = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    verified_mentor = serializers.BooleanField(source='user.verified_mentor')  # new field

    class Meta:
        model = MentorProfile
        fields = [
           'id','name', 'image', 'role', 'experience', 'company',
            'linkedin', 'route', 'buttonText', 'bio',
            'skills', 'courses', 'average_rating', 'verified_mentor'  # added here
        ]
    
    def to_representation(self, instance):
        # Only serialize if mentor is verified
        if not instance.user.verified_mentor:
            return None  # or raise serializers.ValidationError("Mentor not verified")
        return super().to_representation(instance)

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_role(self, obj):
        return "Mentor"
    
    def get_company(self,obj):
       return obj.company

    def get_experience(self, obj):
        return f"{obj.experience}+ years"

    def get_route(self, obj):
        slug = obj.user.id
        return f"/mentor/{slug}"

    def get_buttonText(self, obj):
        return "Know More"

    def get_skills(self, obj):
        return [skill.strip() for skill in obj.skills.split(",")] if obj.skills else []

    def get_courses(self, obj):
        return list(obj.courses.values_list('title', flat=True))

    def get_average_rating(self, obj):
        avg = Review.objects.filter(mentor=obj.user).aggregate(avg_rating=Avg('rating'))
        return round(avg['avg_rating'], 2) if avg['avg_rating'] else None


class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot
        fields = ['id', 'image', 'title', 'button_text','join_url']

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def save(self):
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")

        user.set_password(new_password)
        user.save()
        return user

class ResetPasswordConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class PageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageContent
        fields = "__all__" 
