from django.urls import path
from . import views
from .waiting_time_views import PredictWaitingTimeView, TrainModelView, WaitingTimeStatusView
from .waiting_time_dashboard import ClinicWaitingTimeDashboardView, MyTokenWaitingTimeView
from .model_accuracy_dashboard import ModelAccuracyDashboardView, ModelTrainingLogView
from .training_management_views import TrainingManagementView, DataQualityView
from .enhanced_views import (
    RealTimeDashboardView, SmartQueueView, CommunicationHubView, 
    AdvancedReportsView, ClinicInsightsView
)
from .smart_queue_views import (
    RealTimeQueueView, EarlyArrivalView, ClinicOverviewView,
    SmartQueueActionsView, PatientQueueStatusView, WalkInAvailabilityView
)
from . import live_dashboard_views
from .medical_summary_views import MedicalSummaryView, ConsultationDetailView


urlpatterns = [
    # Public & Analytics
    path('public/clinics/', views.PublicClinicListView.as_view(), name='public-clinic-list'),
    path('analytics/', views.ClinicAnalyticsView.as_view(), name='clinic-analytics'),

    # Patient Self-Service
    path('register/patient/', views.PatientRegisterView.as_view(), name='patient-register'),
    path('link-ivr-account/', views.LinkIVRAccountView.as_view(), name='link-ivr-account'),
    
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

    # Waiting Time Prediction
    path('waiting-time/predict/<int:doctor_id>/', PredictWaitingTimeView.as_view(), name='predict-waiting-time'),
    path('waiting-time/train/', TrainModelView.as_view(), name='train-waiting-time-model'),
    path('waiting-time/status/', WaitingTimeStatusView.as_view(), name='waiting-time-status'),
    
    # Waiting Time Dashboard
    path('waiting-time/dashboard/', ClinicWaitingTimeDashboardView.as_view(), name='waiting-time-dashboard'),
    path('waiting-time/dashboard/<int:clinic_id>/', ClinicWaitingTimeDashboardView.as_view(), name='clinic-waiting-time-dashboard'),
    path('waiting-time/my-token/', MyTokenWaitingTimeView.as_view(), name='my-token-waiting-time'),
    
    # Model Accuracy Dashboard for Judges
    path('model/accuracy/', ModelAccuracyDashboardView.as_view(), name='model-accuracy-dashboard'),
    path('model/training-log/', ModelTrainingLogView.as_view(), name='model-training-log'),
    
    # Training Management
    path('training/manage/', TrainingManagementView.as_view(), name='training-management'),
    path('training/data-quality/', DataQualityView.as_view(), name='training-data-quality'),

    # IVR & SMS
    path('ivr/welcome/', views.ivr_welcome, name='ivr-welcome'),
    path('ivr/handle-state/', views.ivr_handle_state, name='ivr-handle-state'),
    path('ivr/handle-district/<int:state_id>/', views.ivr_handle_district, name='ivr-handle-district'),
    path('ivr/handle-clinic/<int:district_id>/', views.ivr_handle_clinic, name='ivr-handle-clinic'),
    path('ivr/handle-booking-type/<int:clinic_id>/', views.ivr_handle_booking_type, name='ivr-handle-booking-type'),
    path('ivr/handle-next-available-spec/<int:clinic_id>/', views.ivr_handle_next_available_spec, name='ivr-handle-next-available-spec'),
    path('ivr/handle-specialization/<int:clinic_id>/', views.ivr_handle_specialization, name='ivr-handle-specialization'),
    path('ivr/handle-doctor/<int:clinic_id>/<str:spec>/', views.ivr_handle_doctor, name='ivr-handle-doctor'),
    path('ivr/handle-date-specialization/<int:clinic_id>/', views.ivr_handle_date_specialization, name='ivr-handle-date-specialization'),
    path('ivr/handle-date-doctor-choice/<int:clinic_id>/<str:spec>/', views.ivr_handle_date_doctor_choice, name='ivr-handle-date-doctor-choice'),
    path('ivr/handle-date-input/<int:clinic_id>/<str:spec>/', views.ivr_handle_date_input, name='ivr-handle-date-input'),
    path('ivr/handle-specific-doctor-date/<int:clinic_id>/<str:spec>/<str:date_str>/', views.ivr_handle_specific_doctor_date, name='ivr-handle-specific-doctor-date'),
    path('ivr/handle-specific-doctor/<int:clinic_id>/<str:spec>/', views.ivr_handle_specific_doctor, name='ivr-handle-specific-doctor'),
    path('ivr/confirm-booking/', views.ivr_confirm_booking, name='ivr-confirm-booking'),
    path('sms/incoming/', views.handle_incoming_sms, name='incoming-sms'),

    # Enhanced Features
    path('dashboard/realtime/', RealTimeDashboardView.as_view(), name='realtime-dashboard'),
    path('queue/smart/', SmartQueueView.as_view(), name='smart-queue'),
    path('communication/', CommunicationHubView.as_view(), name='communication-hub'),
    path('reports/advanced/', AdvancedReportsView.as_view(), name='advanced-reports'),
    path('insights/', ClinicInsightsView.as_view(), name='clinic-insights'),
    
    # Smart Queue Management
    path('queue/realtime/', RealTimeQueueView.as_view(), name='realtime-queue'),
    path('queue/realtime/<int:doctor_id>/', RealTimeQueueView.as_view(), name='realtime-queue-doctor'),
    path('queue/early-arrival/', EarlyArrivalView.as_view(), name='early-arrival'),
    path('queue/clinic-overview/', ClinicOverviewView.as_view(), name='clinic-overview'),
    path('queue/actions/', SmartQueueActionsView.as_view(), name='smart-queue-actions'),
    path('queue/patient-status/', PatientQueueStatusView.as_view(), name='patient-queue-status'),
    path('queue/walkin-availability/', WalkInAvailabilityView.as_view(), name='walkin-availability'),
    
    # Live Wait Times APIs
    path('live-wait-times/', live_dashboard_views.LiveWaitTimesView.as_view(), name='live_wait_times'),
    path('token-wait-time/<int:token_id>/', live_dashboard_views.TokenWaitTimeView.as_view(), name='token_wait_time'),
    path('doctor-flow/<int:doctor_id>/', live_dashboard_views.DoctorFlowAnalysisView.as_view(), name='doctor_flow'),
    path('live-dashboard-overview/', live_dashboard_views.LiveDashboardOverviewView.as_view(), name='live_dashboard_overview'),
    path('update-token-status/<int:token_id>/', live_dashboard_views.UpdateTokenStatusView.as_view(), name='update_token_status'),
    
    # Medical Summary System
    path('medical-summary/', MedicalSummaryView.as_view(), name='medical-summary'),
    path('consultation/<int:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),

]