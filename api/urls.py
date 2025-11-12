
from django.urls import path
from .views import *


urlpatterns = [
    
    path("register/", RegisterView.as_view(), name="register"),
    path('user-profile/', UserProfileView.as_view(), name='user_profile'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('reset_password/', ResetPasswordAPIView.as_view(), name="reset-password"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/<int:uid>/<str:token>/", ResetPasswordConfirmAPIView.as_view(), name="reset-password-confirm"),
    path('mentors/public/', MentorPublicListAPIView.as_view(), name='mentor-public-list'),
    path('mentor/<int:mentor_id>/', MentorPublicDetailByEmailAPIView.as_view(), name='mentor-public-detail-by-email'),
    path('mentor/full-profile/', MentorFullProfileView.as_view(), name='mentor-full-profile'),
    path('student/full-profile/', StudentFullProfileView.as_view(), name='student-full-profile'),
    path('courses/', CourseListCreateAPIView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseDetailAPIView.as_view(), name='course-detail'),
    path('jobs/', JobListCreateAPIView.as_view(), name='job-list-create'),
    path('jobs/<int:pk>/', JobDetailAPIView.as_view(), name='job-detail'),
    path('job-applications/', JobApplicationListAPIView.as_view(), name='job-applications-list'),
    path('job-applications/apply/', JobApplicationCreateAPIView.as_view(), name='job-application-create'),
    path('upload-certificate/', UploadSQLCertificateView.as_view(), name='upload-sql-certificate'),
    path('verify-certificate/', VerifySQLCertificateView.as_view(), name='verify-sql-certificate'),
    path('referrals/', ReferralCreateView.as_view(), name='refreral-create'),
    path('api/referral-request/create/', CreateReferralRequestView.as_view(), name='create-referral-request'),
    path('api/referral-request/', ReferralRequestListView.as_view(), name='list-referral-request'),
    path('api/referral-request/<int:pk>/status/', UpdateReferralRequestStatusView.as_view(), name='update-referral-status'),
    path('reviews/', ReviewListCreateAPIView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailAPIView.as_view(), name='review-detail'),
    path('mentors/ratings/', MentorAverageRatingAPIView.as_view(), name='mentor-average-ratings'),
    path('bots/', BotListCreateAPIView.as_view(), name='bot-list-create'),
    path('bots/<int:pk>/', BotDetailAPIView.as_view(), name='bot-detail'),
    path('export-users/', ExportUsersCSV.as_view(), name='export-users'),
    path('import-users/', ImportUsersView.as_view(), name='import-users'),
    path("page-contents/", PageContentListCreateView.as_view(), name="pagecontent-list-create"),
    path("page-contents/<int:pk>/", PageContentRetrieveUpdateDeleteView.as_view(), name="pagecontent-detail"),
    path('slots/<int:mentor_id>', SlotListAPI.as_view(), name='slot-list'),
    path('bookings/', BookingListAPI.as_view(), name='booking-list'),
    path('bookings/create/', BookingCreateAPI.as_view(), name='booking-create'),
    path('my-bookings/', MyBookingsAPI.as_view(), name='my-bookings'),
]
