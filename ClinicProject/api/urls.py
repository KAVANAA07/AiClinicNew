from django.urls import path
from . import views
from .views import *
from .waiting_time_views import PredictWaitingTimeView, TrainModelView, WaitingTimeStatusView, PublicPredictWaitingTimeView
from .enhanced_views import RealTimeDashboardView, SmartQueueView, CommunicationHubView, AdvancedReportsView, ClinicInsightsView

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('staff-login/', StaffLoginView.as_view(), name='staff-login'),
    path('register/', PatientRegisterView.as_view(), name='register'),
    path('register/patient/', PatientRegisterView.as_view(), name='register-patient'),
    path('link-ivr/', LinkIVRAccountView.as_view(), name='link-ivr'),
    path('me/', MeView.as_view(), name='me'),
    
    # Patient endpoints
    path('patient/token/', GetPatientTokenView.as_view(), name='get-patient-token'),
    path('patient/create-token/', PatientCreateTokenView.as_view(), name='create-patient-token'),
    path('patient/cancel-token/', PatientCancelTokenView.as_view(), name='cancel-patient-token'),
    path('patient/confirm-arrival/', ConfirmArrivalView.as_view(), name='confirm-arrival'),
    path('patient/history/', MyHistoryView.as_view(), name='my-history'),
    
    # Missing patient endpoints (frontend compatibility) - with and without trailing slash
    path('tokens/get_my_token/', GetPatientTokenView.as_view(), name='get-my-token'),
    path('tokens/get_my_token', GetPatientTokenView.as_view(), name='get-my-token-no-slash'),
    path('history/my_history/', MyHistoryView.as_view(), name='my-history-alt'),
    path('history/my_history', MyHistoryView.as_view(), name='my-history-alt-no-slash'),
    path('tokens/confirm_arrival/', ConfirmArrivalView.as_view(), name='confirm-arrival-alt'),
    path('tokens/confirm_arrival', ConfirmArrivalView.as_view(), name='confirm-arrival-alt-no-slash'),
    path('tokens/patient_cancel/', PatientCancelTokenView.as_view(), name='patient-cancel-alt'),
    path('tokens/patient_cancel', PatientCancelTokenView.as_view(), name='patient-cancel-alt-no-slash'),
    path('tokens/patient_create/', PatientCreateTokenView.as_view(), name='patient-create-alt'),
    path('tokens/patient_create', PatientCreateTokenView.as_view(), name='patient-create-alt-no-slash'),
    path('patient/queue/<int:doctor_id>/<str:date>/', PatientLiveQueueView.as_view(), name='patient-queue'),
    path('doctors/<int:doctor_id>/available-slots/<str:date>/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('public/doctors/<int:doctor_id>/available-slots/<str:date>/', PublicAvailableSlotsView.as_view(), name='public-doctor-available-slots'),
    path('history/<int:patient_id>/', PatientHistoryView.as_view(), name='patient-history-by-id'),
    path('ai-summary/', SimpleAISummaryView.as_view(), name='ai-summary'),
    
    # Staff endpoints
    path('tokens/', TokenListCreate.as_view(), name='token-list-create'),
    path('tokens/<int:id>/', TokenUpdateStatusView.as_view(), name='token-update'),
    path('tokens/<int:id>/update_status/', TokenUpdateStatusView.as_view(), name='token-update-status'),
    path('tokens/<int:token_id>/receptionist-confirm/', ReceptionistConfirmArrivalView.as_view(), name='receptionist-confirm'),
    path('tokens/<int:token_id>/confirm_arrival/', ReceptionistConfirmArrivalView.as_view(), name='receptionist-confirm-alt'),
    path('doctors/', DoctorList.as_view(), name='doctor-list'),
    path('consultations/', ConsultationCreateView.as_view(), name='consultation-create'),
    path('consultations/create/', ConsultationCreateView.as_view(), name='consultation-create-alt'),
    
    # Public endpoints
    path('clinics/', PublicClinicListView.as_view(), name='public-clinics'),
    path('public/clinics/', PublicClinicListView.as_view(), name='public-clinics-alt'),
    path('clinics-with-doctors/', ClinicWithDoctorsListView.as_view(), name='clinics-with-doctors'),
    path('clinics_with_doctors/', ClinicWithDoctorsListView.as_view(), name='clinics-with-doctors-alt'),
    path('available-slots/<int:doctor_id>/<str:date>/', AvailableSlotsView.as_view(), name='available-slots'),
    path('public/available-slots/<int:doctor_id>/<str:date>/', AvailableSlotsView.as_view(), name='public-available-slots'),
    path('live-queue/<int:doctor_id>/<str:date>/', PatientLiveQueueView.as_view(), name='live-queue'),
    
    # Analytics
    path('analytics/', ClinicAnalyticsView.as_view(), name='clinic-analytics'),
    
    # Patient history search
    path('history-search/', PatientHistorySearchView.as_view(), name='patient-history-search'),
    path('patient-history/<int:patient_id>/', PatientHistoryView.as_view(), name='patient-history'),
    path('patient-history-summary/<int:patient_id>/', PatientHistorySummaryView.as_view(), name='patient-history-summary'),
    path('patient-summary/<int:patient_id>/', PatientHistorySummaryView.as_view(), name='patient-summary'),
    
    # AI endpoints
    path('ai/model-status/', AIModelStatusView.as_view(), name='ai-model-status'),
    path('ai/model-load/', AIModelLoadView.as_view(), name='ai-model-load'),
    path('ai/history-summary/', AIHistorySummaryView.as_view(), name='ai-history-summary'),
    path('ai/simple-summary/', SimpleAISummaryView.as_view(), name='simple-ai-summary'),
    
    # Waiting time prediction endpoints
    path('waiting-time/predict/<int:doctor_id>/', PredictWaitingTimeView.as_view(), name='predict-waiting-time'),
    path('public/waiting-time/predict/<int:doctor_id>/', PublicPredictWaitingTimeView.as_view(), name='public-predict-waiting-time'),
    path('waiting-time/train/', TrainModelView.as_view(), name='train-model'),
    path('waiting-time/status/', WaitingTimeStatusView.as_view(), name='waiting-time-status'),
    
    # Enhanced dashboard endpoints
    path('dashboard/realtime/', RealTimeDashboardView.as_view(), name='realtime-dashboard'),
    path('queue/smart/', SmartQueueView.as_view(), name='smart-queue'),
    path('communication/', CommunicationHubView.as_view(), name='communication-hub'),
    path('reports/advanced/', AdvancedReportsView.as_view(), name='advanced-reports'),
    path('insights/', ClinicInsightsView.as_view(), name='clinic-insights'),
    
    # Schedule management
    path('schedules/', DoctorScheduleListView.as_view(), name='doctor-schedules'),
    path('schedules/<int:doctor_id>/', DoctorScheduleUpdateView.as_view(), name='doctor-schedule-update'),
    
    # IVR endpoints
    path('ivr/welcome/', views.ivr_welcome, name='ivr-welcome'),
    path('welcome/voice/', views.ivr_welcome, name='ivr-welcome-alt'),  # Twilio default URL
    path('ivr/handle-state/', views.ivr_handle_state, name='ivr-handle-state'),
    path('ivr/handle-district/<int:state_id>/', views.ivr_handle_district, name='ivr-handle-district'),
    path('ivr/handle-clinic/<int:district_id>/', views.ivr_handle_clinic, name='ivr-handle-clinic'),
    path('ivr/handle-booking-type/<int:clinic_id>/', views.ivr_handle_booking_type, name='ivr-handle-booking-type'),
    path('ivr/handle-specialization/<int:clinic_id>/', views.ivr_handle_specialization, name='ivr-handle-specialization'),
    path('ivr/handle-doctor/<int:clinic_id>/<str:spec>/', views.ivr_handle_doctor, name='ivr-handle-doctor'),
    path('ivr/handle-next-available-spec/<int:clinic_id>/', views.ivr_handle_next_available_spec, name='ivr-handle-next-available-spec'),
    path('ivr/handle-date-specialization/<int:clinic_id>/', views.ivr_handle_date_specialization, name='ivr-handle-date-specialization'),
    path('ivr/handle-date-doctor-choice/<int:clinic_id>/<str:spec>/', views.ivr_handle_date_doctor_choice, name='ivr-handle-date-doctor-choice'),
    path('ivr/handle-date-input/<int:clinic_id>/<str:spec>/', views.ivr_handle_date_input, name='ivr-handle-date-input'),
    path('ivr/handle-specific-doctor-date/<int:clinic_id>/<str:spec>/<str:date_str>/', views.ivr_handle_specific_doctor_date, name='ivr-handle-specific-doctor-date'),
    path('ivr/handle-specific-doctor/<int:clinic_id>/<str:spec>/', views.ivr_handle_specific_doctor, name='ivr-handle-specific-doctor'),
    path('ivr/confirm-booking/', views.ivr_confirm_booking, name='ivr-confirm-booking'),
    path('ivr/sms/', views.handle_incoming_sms, name='handle-incoming-sms'),
    
    # Coordinate picker
    path('coordinate-picker/', CoordinatePickerView.as_view(), name='coordinate-picker'),
    
    # Token wait time endpoint for LiveQueueWidget
    path('token-wait-time/<int:token_id>/', TokenWaitTimeView.as_view(), name='token-wait-time'),
    
    # Doctor dashboard
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor-dashboard'),
]