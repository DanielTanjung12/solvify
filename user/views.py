import re
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token
from django.contrib.auth.decorators import login_required
from solvify import settings
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
from .models import UserProfile, Meeting
from django.db.models.signals import pre_delete
from django.dispatch import receiver

@login_required(login_url='signin')
def home(request):
    # Try to get the user profile, or redirect to sign-in if it doesn't exist
    user_profile = UserProfile.objects.filter(user=request.user).first()

    if not user_profile:
        # Redirect to sign-in page if UserProfile doesn't exist (user is not registered)
        return redirect('signin')

    # Access the role directly from the user_profile
    role = user_profile.role
    fname = request.user.first_name if request.user.is_authenticated else None

    # Retrieve upcoming meetings for the user (teacher or student)
    if role == 'teacher':
        upcoming_meetings = Meeting.objects.filter(teacher=request.user)
    else:
        upcoming_meetings = Meeting.objects.filter(students=request.user)

    context = {'fname': fname, 'role': role, 'upcoming_meetings': upcoming_meetings}
    return render(request, 'index.html', context)

def signup(request):
    # if the button submit button for registration is clicked
    if request.method == "POST":
        # storin the inputted values by the user to a variable
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # validate username
        if User.objects.filter(username=username):
            messages.error(request, "Username already exist!")
            return redirect('/signup')
        
        # validate email
        if User.objects.filter(email=email):
            messages.error(request, "Email already registered!")
            return redirect('/signup')

        # validate length of username
        if len(username)>10:
            messages.error(request, "Username must be under 10 characters")
            return redirect('/signup')

        # validate password math
        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('/signup')
        
        # if username is not alphanumeric
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!")
            return redirect('/signup')

        # Validate password
        if len(pass1) < 8:
            messages.error(request, "Password must contain at least 8 characters.")
            return redirect('/signup')

        if not re.search(r'[a-zA-Z]', pass1):
            messages.error(request, "Password must contain at least one alphabet character.")
            return redirect('/signup')

        if not re.search(r'[A-Z]', pass1):
            messages.error(request, "Password must contain at least one uppercase character.")
            return redirect('/signup')

        if not re.search(r'[0-9]', pass1):
            messages.error(request, "Password must contain at least one numeric character.")
            return redirect('/signup')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pass1):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('/signup')

        # create the table or user object by using User
        myuser = User.objects.create_user(username, email, pass1)

        # Create UserProfile for the registered user
        UserProfile.objects.create(user=myuser, role='student')  # Set the default role as 'student'
        
        # alternatively, you can create the fname and lname columns by doing the two lines below
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()
        
        # # send welcome email
        subject = "Welcome to Solvify login!"
        message = "Hello " + myuser.first_name + "! \n" + "Welcome to Solvify! \nThank you for visiting our website. \nWe have also sent you a confirmation email, please confirm your email address. \n\nThanking You,\nSolvify Team"        
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)

        # send email confirmation link
        current_site = get_current_site(request)
        email_subject = "Confirm your email address"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
        email_subject,
        message2,
        settings.EMAIL_HOST_USER,
        [myuser.email],
        )
        send_mail(email_subject, message2, from_email, to_list, fail_silently=False)
        messages.success(request, "Your account has been created successfully! Please check your email to confirm your email address and activate your account.")
        return redirect('/signin')
    
    return render(request, "user/signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            # Retrieve user profile
            try:
                user_profile = UserProfile.objects.get(user=user)
                role = user_profile.role if user_profile else 'student'  # Default to 'student' if the profile is not found
            except UserProfile.DoesNotExist:
                role = 'student'
            
            login(request, user)
            messages.success(request, "Logged In Sucessfully!")
            # Redirect to the home view, which handles upcoming meetings, don't use render because you won't see the meetings in the upcoming meetings section
            return redirect('home')
            # The previou render code:
            # return render(request, "index.html", {"fname": user.first_name, "role": role})
        else:
            messages.error(request, "Username or password is incorrect")
            return redirect('home')
    
    return render(request, "user/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('/signin')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        messages.success(request, "Your Account has been activated!")
        return redirect('home')
    else:
        return render(request, 'activation_failed.html')
    

@login_required(login_url='signin')
def delete_meeting(request, meeting_id):
    # Retrieve the meeting object
    meeting = get_object_or_404(Meeting, pk=meeting_id)

    # Check if the user has the right to delete this meeting (assuming teacher can only delete their own meetings)
    if request.user == meeting.teacher:
        # Delete the meeting
        meeting.delete()
        messages.success(request, "Meeting deleted successfully!")
    else:
        messages.error(request, "You do not have permission to delete this meeting.")

    # Redirect back to the schedule page or any other appropriate page
    return redirect('schedule')