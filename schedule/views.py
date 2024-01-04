from django.shortcuts import render, redirect
from user.models import UserProfile, Meeting
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def schedule(request):
    # Always retrieve student_first_names, regardless of the request method
    student_first_names = UserProfile.objects.filter(role='student').values_list('user__first_name', flat=True)
    if request.method == 'POST':
        teacher = request.user
        students_selected = request.POST.getlist('studentSelect')
        date = request.POST.get('date')
        time = request.POST.get('time')
        zoom_link = request.POST.get('link')

        # Creating a new Meeting instance and storing the submitted information
        meeting = Meeting.objects.create(teacher=teacher, date=date, time=time, zoom_link=zoom_link)
        meeting.students.set(User.objects.filter(first_name__in=students_selected))

        # Retrieving upcoming meetings for the same teacher
        upcoming_meetings = Meeting.objects.filter(teacher=teacher)

        # Render the 'schedule.html' template with the necessary context
        return render(request, 'schedule.html', {'student_first_names': student_first_names, 'upcoming_meetings': upcoming_meetings})
    upcoming_meetings = Meeting.objects.filter(teacher=request.user)
    return render(request, 'schedule.html', {'student_first_names': student_first_names, 'upcoming_meetings': upcoming_meetings})