from django.urls import path
from twilio_sms import views

urlpatterns = [
    path("sms/create/", views.CreateSmsView.as_view(), name="create_sms"),
    path("sms/verify/", views.VerifySmsView.as_view(), name="verify_sms"),
]
