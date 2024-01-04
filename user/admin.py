from django.contrib import admin
from .models import UserProfile
from .models import Meeting

admin.site.register(UserProfile)
admin.site.register(Meeting)