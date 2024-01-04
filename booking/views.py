from django.shortcuts import render
from user.models import UserProfile

def booking(request):
    teacher_first_names = UserProfile.objects.filter(role='teacher').values_list('user__first_name', flat=True)
    return render(request, "booking.html", {'student_first_names': teacher_first_names})