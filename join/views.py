from django.shortcuts import render, redirect
from user.models import UserProfile, Meeting
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def join(request):
    # Try to get the user profile, or redirect to sign-in if it doesn't exist
    user_profile = UserProfile.objects.filter(user=request.user).first()

    # Access the role directly from the user_profile
    role = user_profile.role

    # Retrieve upcoming meetings for the user (teacher or student)
    if role == 'teacher':
        upcoming_meetings = Meeting.objects.filter(teacher=request.user)
    else:
        upcoming_meetings = Meeting.objects.filter(students=request.user)

    context = {'role': role, 'upcoming_meetings': upcoming_meetings}
    return render(request, 'joinMeeting.html', context)