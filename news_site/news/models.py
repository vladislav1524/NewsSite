from django.db import models
from datetime import datetime
import pytz
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be filled in")
        
        email = self.normalize_email(email)
        
        existing_user = self.model.objects.filter(email=email).first()
        if existing_user:
            for key, value in extra_fields.items():
                setattr(existing_user, key, value)
            existing_user.save(using=self._db)
            return existing_user
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return self.email
    

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    url = models.URLField()
    published_date = models.DateTimeField()

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ["-published_date"]

    def save(self, *args, **kwargs):
        if isinstance(self.published_date, str):
            try:
                naive_datetime = datetime.strptime(self.published_date, '%a, %d %b %Y %H:%M:%S %z')
                aware_datetime = naive_datetime.astimezone(pytz.utc)
                self.published_date = aware_datetime
            except ValueError:
                raise ValueError("Incorrect date format. Expected: 'Wed, 22 Jan 2025 15:23:09 +0300'")
        super().save(*args, **kwargs)
    
class ReadLater(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')