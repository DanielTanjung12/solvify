from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, default='student')  # Default role is set to 'student'

    def delete(self, *args, **kwargs):
        # Delete meetings associated with the user before deleting the user profile
        Meeting.objects.filter(students=self.user).delete()
        super(UserProfile, self).delete(*args, **kwargs)

class Meeting(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_meetings')
    students = models.ManyToManyField(User, related_name='attended_meetings')
    date = models.DateField()
    time = models.TimeField()
    zoom_link = models.CharField(max_length=255, blank=True, null=True)  # New field for storing the Zoom link

    def __str__(self):
        student_names = ', '.join([f"{student.first_name} {student.last_name}" for student in self.students.all()])
        return f"Meeting with {student_names} on {self.date} at {self.time}"
    
@receiver(pre_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    try:
        user_profile = UserProfile.objects.get(user=instance)
        user_profile.delete()
    except UserProfile.DoesNotExist:
        pass