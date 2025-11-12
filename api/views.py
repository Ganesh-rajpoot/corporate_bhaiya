from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from .serializers import *
from rest_framework.permissions import IsAuthenticated,AllowAny
import csv
import io
from rest_framework import status, permissions
from django.utils import timezone
from .models import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Avg, Count
import csv
from django.http import HttpResponse
from .utils import account_activation_token,generate_slots_for_mentor
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction




class RegisterView(APIView):

    @transaction.atomic
    def post(self, request):
        data = request.data
        role = data.get("user_role")

        if role not in ["student", "mentor"]:
            return Response({"error": "user_role must be 'student' or 'mentor'"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create User
        try:
            user = User.objects.create_user(
                email=data.get("email"),
                name=data.get("name"),
                password=data.get("password"),
                is_mentor=(role == "mentor"),
                mobile=data.get("mobile")
            )
            user.user_role = role
            user.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create Role-specific profile
        if role == "mentor":
            MentorProfile.objects.create(
                user=user,
                bio=data.get("bio", ""),
                experience=data.get("experience", 0),
                skills=data.get("skills", ""),
                #available_days=data.get("available_days", ""),
                company=data.get("company", ""),
                linkedin=data.get("linkedin", ""),
                goals=data.get("goals", "")
            )
        else:  # student
            StudentProfile.objects.create(
                user=user,
                college=data.get("college", ""),
                interests=data.get("interests", "")
            )

        return Response({
            "message": f"{role.capitalize()} registered successfully",
            "user_id": user.id,
            "email": user.email,
            "role": role
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Login successful",
                    
                    # "user": {
                    #     "id": user.id,
                    #     "email": user.email,
                    #     "name": user.name,
                        
                    #     "is_mentor": user.is_mentor
                    # },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


class MentorFullProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_serializer = UserUpdateSerializer(request.user)
        mentor_profile, _ = MentorProfile.objects.get_or_create(user=request.user)
        profile_serializer = MentorProfileSerializer(mentor_profile)
        return Response({
            "user": user_serializer.data,
            "profile": profile_serializer.data
        })

    def put(self, request):
        user_serializer = UserUpdateSerializer(request.user, data=request.data.get('user'), partial=True)
        mentor_profile, _ = MentorProfile.objects.get_or_create(user=request.user)
        profile_serializer = MentorProfileSerializer(mentor_profile, data=request.data.get('profile'), partial=True)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "user": user_serializer.data,
                "profile": profile_serializer.data
            })

        return Response({
            "user_errors": user_serializer.errors,
            "profile_errors": profile_serializer.errors
        }, status=400)



class StudentFullProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        return Response({
            "user": UserUpdateSerializer(request.user).data,
            "profile": StudentProfileSerializer(student_profile).data,
        })

    def put(self, request):
        user_serializer = UserUpdateSerializer(request.user, data=request.data.get('user'), partial=True)
        profile_serializer = StudentProfileSerializer(request.user.studentprofile, data=request.data.get('profile'), partial=True)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "user": user_serializer.data,
                "profile": profile_serializer.data
            })

        return Response({
            "user_errors": user_serializer.errors,
            "profile_errors": profile_serializer.errors
        }, status=400)


# class UserProfileView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         data = UserSerializer(user).data

#         if hasattr(user, 'mentorprofile'):
#             data['mentor_profile'] = MentorProfileSerializer(user.mentorprofile).data
#         if hasattr(user, 'studentprofile'):
#             data['student_profile'] = StudentProfileSerializer(user.studentprofile).data

#         return Response(data)

#     def put(self, request):
#         user = request.user

#         # User update
#         user_serializer = UserUpdateSerializer(user, data=request.data)
#         if user_serializer.is_valid():
#             user_serializer.save()
#         else:
#             return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Mentor profile update if mentor
#         if hasattr(user, 'mentorprofile'):
#             mentor_serializer = MentorProfileSerializer(user.mentorprofile, data=request.data, partial=True)
#             if mentor_serializer.is_valid():
#                 mentor_profile = mentor_serializer.save()
#                 # ✅ Agar availability fields update hue hain to slots regenerate
#                 if any(field in request.data for field in ["schedules", "slot_duration", "future_weeks"]):
#                     generate_slots_for_mentor(mentor_profile)
#             else:
#                 return Response(mentor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Student profile update if student
#         if hasattr(user, 'studentprofile'):
#             student_serializer = StudentProfileSerializer(user.studentprofile, data=request.data, partial=True)
#             if student_serializer.is_valid():
#                 student_serializer.save()

                
#             else:
#                 return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response({"detail": "Profile updated successfully."})

#     def patch(self, request):
#         user = request.user

#         # User update (partial)
#         user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
#         if user_serializer.is_valid():
#             user_serializer.save()
#         else:
#             return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Mentor profile update if mentor
#         if hasattr(user, 'mentorprofile'):
#             mentor_serializer = MentorProfileSerializer(user.mentorprofile, data=request.data, partial=True)

#             if mentor_serializer.is_valid():
#                 print(mentor_serializer.validated_data)
#                 mentor_profile = mentor_serializer.save()
#                 # ✅ Agar availability fields update hue hain to slots regenerate
#                 if any(field in request.data for field in ["schedules", "slot_duration", "future_weeks"]):
#                     generate_slots_for_mentor(mentor_profile)
#             else:
#                 return Response(mentor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Student profile update if student
#         if hasattr(user, 'studentprofile'):
#             student_serializer = StudentProfileSerializer(user.studentprofile, data=request.data, partial=True)
#             if student_serializer.is_valid():
#                 student_serializer.save()
#             else:
#                 return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response({"detail": "Profile updated successfully."})

#     def delete(self, request):
#         user = request.user
#         user.delete()
#         return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserUpdateSerializer(user).data  # Use UserUpdateSerializer for consistency

        if hasattr(user, 'mentorprofile'):
            data['mentor_profile'] = MentorProfileSerializer(user.mentorprofile).data
        if hasattr(user, 'studentprofile'):
            data['student_profile'] = StudentProfileSerializer(user.studentprofile).data

        return Response(data)

    def put(self, request):
        user = request.user

        # User update
        user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Mentor profile update if mentor
        if hasattr(user, 'mentorprofile'):
            mentor_data = request.data.get('mentorprofile', {})  # Extract nested mentorprofile data
            # Include top-level mobile and linkedin in mentor_data if present
            #if 'mobile' in request.data:
            #    mentor_data['mobile'] = request.data['mobile']
            #if 'linkedin' in request.data:
            #    mentor_data['linkedin'] = request.data['linkedin']
            for field in ["bio", "experience", "skills", "company", "linkedin", "mobile","goals", "schedules", "slot_duration", "future_weeks"]:
                if field in request.data:
                    mentor_data[field] = request.data[field]

            mentor_serializer = MentorProfileSerializer(user.mentorprofile, data=mentor_data, partial=True)
            if mentor_serializer.is_valid():
                mentor_profile = mentor_serializer.save()
                # Regenerate slots if availability fields are updated
                if any(field in mentor_data for field in ["schedules", "slot_duration", "future_weeks"]):
                    generate_slots_for_mentor(mentor_profile)
            else:
                return Response(mentor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Student profile update if student
        if hasattr(user, 'studentprofile'):
            student_data = request.data.get('studentprofile', {})  # Extract nested studentprofile data
            student_serializer = StudentProfileSerializer(user.studentprofile, data=student_data, partial=True)
            if student_serializer.is_valid():
                student_serializer.save()
            else:
                return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Profile updated successfully."})

    def patch(self, request):
        user = request.user

        # User update (partial)
        user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Mentor profile update if mentor
        if hasattr(user, 'mentorprofile'):
            mentor_data = request.data.get('mentorprofile', {})  # Extract nested mentorprofile data
            # Include top-level mobile and linkedin in mentor_data if present
            #if 'mobile' in request.data:
            #    mentor_data['mobile'] = request.data['mobile']
            #if 'linkedin' in request.data:
            #    mentor_data['linkedin'] = request.data['linkedin']
            for field in ["bio", "experience", "skills", "company", "linkedin", "mobile","goals", "schedules", "slot_duration", "future_weeks"]:
                if field in request.data:
                    mentor_data[field] = request.data[field]
            mentor_serializer = MentorProfileSerializer(user.mentorprofile, data=mentor_data, partial=True)
            if mentor_serializer.is_valid():
                mentor_profile = mentor_serializer.save()
                # Regenerate slots if availability fields are updated
                if any(field in mentor_data for field in ["schedules", "slot_duration", "future_weeks"]):
                    generate_slots_for_mentor(mentor_profile)
            else:
                return Response(mentor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Student profile update if student
        if hasattr(user, 'studentprofile'):
            student_data = request.data.get('studentprofile', {})  # Extract nested studentprofile data
            student_serializer = StudentProfileSerializer(user.studentprofile, data=student_data, partial=True)
            if student_serializer.is_valid():
                student_serializer.save()
            else:
                return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Profile updated successfully."})

def generate_slots_for_mentor(mentor_profile):
    """
    Generate time slots for a mentor based on their schedules, slot_duration, and future_weeks.
    Deletes existing slots for the mentor and creates new ones.
    """
    # Delete existing slots to avoid duplicates
    mentor_profile.slots.all().delete()

    # Get current date and time in the server's timezone
    now = timezone.now()
    current_date = now.date()

    # Map day names to weekday numbers (Monday=0, Sunday=6)
    day_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
        'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }

    # Get mentor's schedules, slot_duration, and future_weeks
    schedules = mentor_profile.schedules
    slot_duration = mentor_profile.slot_duration  # in minutes
    future_weeks = mentor_profile.future_weeks

    # Calculate the end date for slot generation
    end_date = current_date + timedelta(weeks=future_weeks)

    for schedule in schedules:
        if not schedule.get('available', False):
            continue  # Skip unavailable days

        day_name = schedule.get('day')
        start_time_str = schedule.get('startTime')
        end_time_str = schedule.get('endTime')

        if not (day_name and start_time_str and end_time_str):
            continue  # Skip invalid schedule entries

        # Parse start and end times
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            continue  # Skip invalid time formats

        # Find the next occurrence of the day
        target_weekday = day_map[day_name]
        days_ahead = (target_weekday - current_date.weekday()) % 7
        if days_ahead == 0 and now.time() > end_time:
            days_ahead = 7  # If today's time is past end_time, move to next week

        current_target_date = current_date + timedelta(days=days_ahead)

        # Generate slots for each week until end_date
        while current_target_date <= end_date:
            # Combine date and time to create datetime objects
            start_datetime = timezone.make_aware(
                datetime.combine(current_target_date, start_time)
            )
            end_datetime = timezone.make_aware(
                datetime.combine(current_target_date, end_time)
            )

            # Generate slots within the day's time range
            current_slot_start = start_datetime
            while current_slot_start < end_datetime:
                slot_end = current_slot_start + timedelta(minutes=slot_duration)
                if slot_end <= end_datetime:
                    # Create a new slot
                    Slot.objects.create(
                        mentor=mentor_profile,
                        start_time=current_slot_start,
                        end_time=slot_end,
                        is_booked=False
                    )
                current_slot_start += timedelta(minutes=slot_duration)

            # Move to the same day in the next week
            current_target_date += timedelta(weeks=1)
class CourseListCreateAPIView(APIView):
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseDetailAPIView(APIView):
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def put(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




# 🔐 Custom permission for admin users only
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ✅ Job List & Create (Only admin can post)
class JobListCreateAPIView(APIView):
    def get(self, request):
        jobs = Job.objects.all().order_by('-posted_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "Only admins can post jobs."}, status=status.HTTP_403_FORBIDDEN)
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(posted_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Job Detail View (Only admin can update/delete)
class JobDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Job, pk=pk)

    def get(self, request, pk):
        job = self.get_object(pk)
        serializer = JobSerializer(job)
        return Response(serializer.data)

    def put(self, request, pk):
        job = self.get_object(pk)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "Only admins can update jobs."}, status=status.HTTP_403_FORBIDDEN)
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(posted_by=job.posted_by)  # don't change the original poster
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        job = self.get_object(pk)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "Only admins can delete jobs."}, status=status.HTTP_403_FORBIDDEN)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Student applies to a job
class JobApplicationCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# List applications (own for student, all for mentor/staff)
class JobApplicationListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.user_role == 'mentor' or request.user.is_staff:
            applications = JobApplication.objects.all()
        else:
            applications = JobApplication.objects.filter(student=request.user)
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data)

class UploadSQLCertificateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = SQLCertificateAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Certificate uploaded successfully.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifySQLCertificateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        reg_no = request.query_params.get('registration_number')
        if not reg_no:
            return Response({'error': 'registration_number parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cert = SQLCertificate.objects.get(registration_number=reg_no, is_verified=True)
            serializer = SQLCertificateVerifySerializer(cert)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SQLCertificate.DoesNotExist:
            return Response({'error': 'No verified certificate found for this registration number.'}, status=status.HTTP_404_NOT_FOUND)

class ReferralCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['mentor'] = request.user.id
        serializer = ReferralSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Referral submitted successfully'}, status=201)
        return Response(serializer.errors, status=400)

# 1. Create Referral Request (by Student)
class CreateReferralRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['student'] = request.user.id  # student is the requester
        serializer = ReferralRequestSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Referral request sent.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. View Requests for Mentor or Student
class ReferralRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_role == 'mentor':
            requests = ReferralRequest.objects.filter(mentor=user)
        else:
            requests = ReferralRequest.objects.filter(student=user)
        
        serializer = ReferralRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 3. Mentor Updates Status of Request (approve/reject)
class UpdateReferralRequestStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ref_request = ReferralRequest.objects.get(id=pk, mentor=request.user)
        except ReferralRequest.DoesNotExist:
            return Response({'error': 'Referral request not found or not allowed.'}, status=status.HTTP_404_NOT_FOUND)
        
        status_value = request.data.get('status')
        if status_value not in ['approved', 'rejected']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        ref_request.status = status_value
        ref_request.save()

        # ✅ Create Referral Automatically
        if status_value == 'approved':
            Referral.objects.create(
                mentor=ref_request.mentor,
                student=ref_request.student,
                job=ref_request.job,
                message=ref_request.message,  # optional
            )

        return Response({'message': f'Referral request {status_value}.'}, status=status.HTTP_200_OK)

class ReviewListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mentor_id = request.query_params.get('mentor')
        if mentor_id:
            reviews = Review.objects.filter(mentor__id=mentor_id)
        else:
            reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.user_role != 'student':
            return Response({'detail': 'Only students can post reviews.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, student):
        return get_object_or_404(Review, pk=pk, student=student)

    def get(self, request, pk):
        review = self.get_object(pk, request.user)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, pk):
        review = self.get_object(pk, request.user)
        serializer = ReviewSerializer(review, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        review = self.get_object(pk, request.user)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MentorAverageRatingAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        mentors_with_reviews = (
            Review.objects
            .values('mentor')
            .annotate(
                average_rating=Avg('rating'),
                total_reviews=Count('id')
            )
            .order_by('-average_rating')
        )

        data = []
        for item in mentors_with_reviews:
            try:
                mentor = User.objects.get(id=item['mentor'], user_role='mentor')
                data.append({
                    'mentor_id': mentor.id,
                    'mentor_name': mentor.name,
                    'mentor_email': mentor.email,
                    'average_rating': round(item['average_rating'], 2),
                    'total_reviews': item['total_reviews']
                })
            except User.DoesNotExist:
                continue

        serializer = MentorAverageRatingSerializer(data, many=True)
        return Response(serializer.data)

class MentorPublicListAPIView(APIView):
    def get(self, request):
        mentors = MentorProfile.objects.select_related('user').filter(user__verified_mentor=True).prefetch_related('courses')
        serializer = MentorPublicSerializer(mentors, many=True, context={'request': request})
        return Response(serializer.data)

class MentorPublicDetailByEmailAPIView(APIView):
    def get(self, request, mentor_id):
        mentor = get_object_or_404(
            MentorProfile.objects.select_related('user').prefetch_related('courses'),            
            user__id=mentor_id
        )
        serializer = MentorPublicSerializer(mentor, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class BotListCreateAPIView(APIView):
    def get(self, request):
        bots = Bot.objects.all()
        serializer = BotSerializer(bots, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BotDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Bot, pk=pk)

    def get(self, request, pk):
        bot = self.get_object(pk)
        serializer = BotSerializer(bot)
        return Response(serializer.data)

    def put(self, request, pk):
        bot = self.get_object(pk)
        serializer = BotSerializer(bot, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        bot = self.get_object(pk)
        bot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ExportUsersCSV(APIView):
    #permission_classes = [IsAuthenticated]  # 🔒 optional, remove if public

    def get(self, request, format=None):
        # Create HttpResponse with CSV headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'

        writer = csv.writer(response)

        # Header row
        writer.writerow([
            'Email',
            'Name',
            'Mobile',
            'Role',
            'Is Mentor',
            'Is Active',
            'Date Joined',
        ])

        # User data rows
        for user in User.objects.all():
            writer.writerow([
                user.email,
                user.name,
                user.mobile,
                user.user_role,
                user.is_mentor,
                user.is_active,
                user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        return response


class ForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        token = account_activation_token.make_token(user)
        uid = user.pk

        #reset_url = request.build_absolute_uri(
        #    reverse("reset-password-confirm", kwargs={"uid": uid, "token": token})
        #)
        reset_url = f"https://corporatebhaiya.in/reset-password/{uid}/{token}/"

        # send email
        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.name},\n\nUse the link below to reset your password:\n{reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

        return Response({"message": "Password reset link sent to email"}, status=status.HTTP_200_OK)
class ResetPasswordAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password reset successful"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordConfirmAPIView(APIView):
    def post(self, request, uid, token):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=uid)
            except User.DoesNotExist:
                return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

            if not account_activation_token.check_token(user, token):
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImportUsersView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)
        if serializer.is_valid():
            csv_file = serializer.validated_data['file']

            # Check file type
            if not csv_file.name.endswith('.csv'):
                return Response({"error": "File must be a CSV."}, status=status.HTTP_400_BAD_REQUEST)

            data_set = csv_file.read().decode('utf-8')
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)

            created_users = []
            skipped_users = []

            for row in reader:
                name = row.get("Name", "").strip()
                email = row.get("Email ID", "").strip()
                mobile = row.get("Mobile", "").strip()
                password = row.get("Password", "").strip()

                if User.objects.filter(email=email).exists():
                    skipped_users.append(email)
                    continue

                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password=password,
                    is_mentor=False
                )
                user.mobile = mobile
                user.save()
                created_users.append(email)

            return Response({
                "created": created_users,
                "skipped_existing": skipped_users
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PageContentListCreateView(generics.ListCreateAPIView):
    """GET all PageContent, POST new PageContent"""
    queryset = PageContent.objects.all()
    serializer_class = PageContentSerializer


class PageContentRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """GET by ID, PUT/PATCH update, DELETE PageContent"""
    queryset = PageContent.objects.all()
    serializer_class = PageContentSerializer


class SlotListAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, mentor_id):
        # Sirf is mentor ke unbooked slots dikhao
        slots = Slot.objects.filter(
            mentor_id=mentor_id,
            is_booked=False
        ).order_by("start_time")

        serializer = SlotSerializer(slots, many=True)
        return Response(serializer.data)


class BookingListAPI(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all bookings for the authenticated student."""
        bookings = Booking.objects.filter(student=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
class BookingCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new booking for a slot."""
        slot_id = request.data.get('slot')
        try:
            # Use start_time__date instead of date__gte
            slot = Slot.objects.get(
                id=slot_id,
                is_booked=False,
                start_time__date__gte=timezone.now().date()
            )
            # Check for existing booking on the same date
            if Booking.objects.filter(
                student=request.user,
                slot__start_time__date=slot.start_time.date()
            ).first():
                return Response(
                    {"error": "You already have a booking on this date."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            slot.is_booked = True
            slot.save()
            booking = Booking.objects.create(student=request.user, slot=slot)
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Slot.DoesNotExist:
            return Response(
                {"error": "Slot not available or already booked."},
                status=status.HTTP_400_BAD_REQUEST
            )
