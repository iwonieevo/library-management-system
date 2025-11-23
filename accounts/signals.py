from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Reader

@receiver(post_save, sender=User)
def create_reader_profile(sender, instance, created, **kwargs):
    if instance.role == "reader" and not hasattr(instance, "reader"):
        Reader.objects.create(user=instance)

