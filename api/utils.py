# utils.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from datetime import datetime, timedelta, time
from .models import Slot
import json
from django.utils import timezone
import pytz

# def generate_slots_for_mentor(mentor_profile):
#     Slot.objects.filter(mentor=mentor_profile).delete()

#     today = timezone.now().date()
#     end_date = today + timedelta(weeks=mentor_profile.future_weeks)
#     slot_duration = timedelta(minutes=mentor_profile.slot_duration)

#     day_map = {
#         'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
#         'friday': 4, 'saturday': 5, 'sunday': 6
#     }

#     for schedule in mentor_profile.schedules:
#         if not schedule.get('available'):
#             continue

#         day_str = schedule['day'].lower()
#         if day_str not in day_map:
#             continue

#         try:
#             start_time = datetime.strptime(schedule['startTime'], '%H:%M').time()
#             end_time = datetime.strptime(schedule['endTime'], '%H:%M').time()
#         except ValueError:
#             continue

#         current_date = today
#         while current_date <= end_date:
#             if current_date.weekday() == day_map[day_str]:
#                 current_datetime = datetime.combine(current_date, start_time, tzinfo=timezone.get_current_timezone())
#                 end_datetime = datetime.combine(current_date, end_time, tzinfo=timezone.get_current_timezone())
#                 while current_datetime + slot_duration <= end_datetime:
#                     #Slot.objects.create(
#                     #    mentor=mentor_profile,
#                     #    start_time=current_datetime,
#                     #    end_time=current_datetime + slot_duration
#                     #)
#                     Slot.objects.create(
#                         mentor=mentor_profile,
#                         date=current_date,  # ✅ add this line
#                         start_time=current_datetime.time(),  # store only time if your model uses TimeField
#                         end_time=(current_datetime + slot_duration).time(),
#                     )
#                     current_datetime += slot_duration
#             current_date += timedelta(days=1)
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Slot

def generate_slots_for_mentor(mentor_profile):
    # Delete existing slots
    Slot.objects.filter(mentor=mentor_profile).delete()

    today = timezone.now().date()
    end_date = today + timedelta(weeks=mentor_profile.future_weeks)
    slot_duration = timedelta(minutes=mentor_profile.slot_duration)

    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    for schedule in mentor_profile.schedules:
        if not schedule.get('available'):
            continue

        day_str = schedule['day'].lower()
        if day_str not in day_map:
            continue

        try:
            start_time = datetime.strptime(schedule['startTime'], '%H:%M').time()
            end_time = datetime.strptime(schedule['endTime'], '%H:%M').time()
        except ValueError:
            continue

        # Generate slots for each date within range
        current_date = today
        while current_date <= end_date:
            if current_date.weekday() == day_map[day_str]:
                current_start = datetime.combine(current_date, start_time)
                current_end = datetime.combine(current_date, end_time)

                while current_start + slot_duration <= current_end:
                    Slot.objects.create(
                        mentor=mentor_profile,
                        date=current_date,
                        start_time=current_start.time(),
                        end_time=(current_start + slot_duration).time(),
                        seats=1
                    )
                    current_start += slot_duration

            current_date += timedelta(days=1)

    print(f"✅ Slots generated successfully for {mentor_profile.user.email}")

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

account_activation_token = TokenGenerator()

