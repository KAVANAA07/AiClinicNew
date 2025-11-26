from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # This line points any 'api/...' request to the api app's urls.
    path('api/', include('api.urls')),
    # Twilio IVR webhook (root level)
    path('welcome/voice/', views.ivr_welcome, name='twilio-ivr-webhook'),
]

