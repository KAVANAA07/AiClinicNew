from django.urls import path
from . import views


urlpatterns = [
    # Public & Analytics
    path('public/clinics/', views.PublicClinicListView.as_view(), name='public-clinic-list'),
    path('analytics/', views.ClinicAnalyticsView.as_view(), name='clinic-analytics'),

    # Patient Self-Service
    path('register/patient/', views.PatientRegisterView.as_view(), name='patient-register'),
    
    # ✅ FIX: Explicitly matches App.js call
    path('tokens/get_my_token/', views.GetPatientTokenView.as_view(), name='get-patient-token'),
    
    path('tokens/confirm_arrival/', views.ConfirmArrivalView.as_view(), name='confirm-arrival'),
    path('clinics_with_doctors/', views.ClinicWithDoctorsListView.as_view(), name='clinics-with-doctors'),
    path('tokens/patient_create/', views.PatientCreateTokenView.as_view(), name='patient-create-token'),
    path('tokens/patient_cancel/', views.PatientCancelTokenView.as_view(), name='patient-cancel-token'),

    # Queues & Slots
    path('patient/queue/<int:doctor_id>/<str:date>/', views.PatientLiveQueueView.as_view(), name='patient-live-queue'),
    path('doctors/<int:doctor_id>/available-slots/<str:date>/', views.AvailableSlotsView.as_view(), name='available-slots'),

    # Auth
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/staff/', views.StaffLoginView.as_view(), name='staff-login'),

    # Staff Dashboard
    path('tokens/', views.TokenListCreate.as_view(), name='token-list-create'),
    path('doctors/', views.DoctorList.as_view(), name='doctor-list'),
    path('tokens/<int:id>/update_status/', views.TokenUpdateStatusView.as_view(), name='token-update-status'),

    # History & Consultations
    path('history/my_history/', views.MyHistoryView.as_view(), name='my-history'),
    path('history/<int:patient_id>/', views.PatientHistoryView.as_view(), name='patient-history'),
    
    # ✅ NEW: Emergency History Search
    path('history-search/', views.PatientHistorySearchView.as_view(), name='history-search'),
    
    path('consultations/create/', views.ConsultationCreateView.as_view(), name='consultation-create'),

    # AI
    path('ai-summary/', views.SimpleAISummaryView.as_view(), name='ai-history-summary'),
    path('patient-summary/<int:patient_id>/', views.PatientHistorySummaryView.as_view(), name='patient-ai-summary'),
    path('patient-summary/status/', views.AIModelStatusView.as_view(), name='patient-ai-summary-status'),
    path('patient-summary/load/', views.AIModelLoadView.as_view(), name='patient-ai-summary-load'),
    path('me/', views.MeView.as_view(), name='me'),

    # Schedule Management
    path('schedules/', views.DoctorScheduleListView.as_view(), name='doctor-schedules'),
    path('schedules/<int:doctor_id>/', views.DoctorScheduleUpdateView.as_view(), name='doctor-schedule-update'),

    # IVR & SMS
    path('ivr/welcome/', views.ivr_welcome, name='ivr-welcome'),
    path('ivr/handle-state/', views.ivr_handle_state, name='ivr-handle-state'),
    path('ivr/handle-district/<int:state_id>/', views.ivr_handle_district, name='ivr-handle-district'),
    path('ivr/handle-clinic/<int:district_id>/', views.ivr_handle_clinic, name='ivr-handle-clinic'),
    path('ivr/handle-booking-type/<int:clinic_id>/', views.ivr_handle_booking_type, name='ivr-handle-booking-type'),
    path('ivr/handle-specialization/<int:clinic_id>/', views.ivr_handle_specialization, name='ivr-handle-specialization'),
    path('ivr/handle-doctor/<int:clinic_id>/<str:spec>/', views.ivr_handle_doctor, name='ivr-handle-doctor'),
    path('ivr/confirm-booking/', views.ivr_confirm_booking, name='ivr-confirm-booking'),
    path('sms/incoming/', views.handle_incoming_sms, name='incoming-sms'),


]