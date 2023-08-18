from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models




class CustomUser(AbstractUser):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user')

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profile_email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    friends = models.ManyToManyField("self", blank=True, related_name='user_friends')



class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='received_messages')
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    media = models.FileField(upload_to='chat_media/', null=True, blank=True)

class Friend(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendships_created',
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='friendships_received',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user} -> {self.to_user}'