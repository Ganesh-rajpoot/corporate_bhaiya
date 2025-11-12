from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import User, MentorProfile, StudentProfile
from .utils import generate_slots_for_mentor
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_mentor:
            MentorProfile.objects.create(user=instance)
        else:
            StudentProfile.objects.create(user=instance)



@receiver(pre_save, sender=MentorProfile)
def check_mentor_profile_changes(sender, instance, **kwargs):
    if instance.pk:  # Only for updates
        old_instance = sender.objects.get(pk=instance.pk)
        instance._changed_fields = {
            'schedules': old_instance.schedules != instance.schedules,
            'slot_duration': old_instance.slot_duration != instance.slot_duration,
            'future_weeks': old_instance.future_weeks != instance.future_weeks,
        }

@receiver(post_save, sender=MentorProfile)
def regenerate_slots_on_change(sender, instance, **kwargs):
    if hasattr(instance, '_changed_fields') and any(instance._changed_fields.values()):
        generate_slots_for_mentor(instance)