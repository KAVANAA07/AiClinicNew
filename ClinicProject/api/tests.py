
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Patient, Clinic, Doctor, Receptionist, Token as ClinicToken
from django.utils import timezone
import json
from unittest.mock import patch

User = get_user_model()

class AuthTests(APITestCase):
	def setUp(self):
		self.patient_data = {
			"username": "testpatient",
			"password": "testpass123",
			"name": "Test Patient",
			"age": 30,
			"phone_number": "+1234567890"
		}
		self.staff_data = {
			"username": "staffuser",
			"password": "staffpass123",
			"is_staff": True
		}
		self.patient_user = User.objects.create_user(
			username=self.patient_data["username"],
			password=self.patient_data["password"]
		)
		self.patient = Patient.objects.create(
			user=self.patient_user,
			name=self.patient_data["name"],
			age=self.patient_data["age"],
			phone_number=self.patient_data["phone_number"]
		)
		self.staff_user = User.objects.create_user(
			username=self.staff_data["username"],
			password=self.staff_data["password"],
			is_staff=True
		)
		# Create a clinic and receptionist profile for staff access tests
		self.clinic = Clinic.objects.create(name="Test Clinic", address="123 Test St", city="TestCity")
		self.receptionist = Receptionist.objects.create(user=self.staff_user, clinic=self.clinic)

		# Create a doctor and one token for clinic
		self.doctor_user = User.objects.create_user(username="docuser", password="docpass")
		self.doctor = Doctor.objects.create(user=self.doctor_user, name="Dr. Who", specialization="General", clinic=self.clinic)
		# create a token in the clinic
		self.sample_token = ClinicToken.objects.create(patient=self.patient, doctor=self.doctor, clinic=self.clinic, date=timezone.now().date(), status='waiting')

	def test_patient_login(self):
		url = "/api/login/"
		response = self.client.post(url, {
			"username": self.patient_data["username"],
			"password": self.patient_data["password"]
		}, format="json")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("token", response.data)
		self.assertEqual(response.data["user"]["role"], "patient")

	def test_registration_duplicate_username(self):
		url = "/api/register/patient/"
		payload = {
			"username": self.patient_data["username"],
			"password": "xpass123",
			"password2": "xpass123",
			"name": "Dup User",
			"age": 40,
			"phone_number": "+19999999999"
		}
		resp = self.client.post(url, payload, format="json")
		self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

	def test_registration_duplicate_phone(self):
		url = "/api/register/patient/"
		payload = {
			"username": "uniqueuser",
			"password": "xpass123",
			"password2": "xpass123",
			"name": "Dup Phone",
			"age": 40,
			"phone_number": self.patient_data["phone_number"]
		}
		resp = self.client.post(url, payload, format="json")
		self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

	def test_login_inactive_user(self):
		# create an inactive user with patient profile
		inactive = User.objects.create_user(username="inactive", password="pass123", is_active=False)
		Patient.objects.create(user=inactive, name="Inactive", age=20, phone_number="+15550001111")
		resp = self.client.post("/api/login/", {"username": "inactive", "password": "pass123"}, format="json")
		# LoginView returns 401 for inactive patient
		self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST])

	def test_patient_cannot_see_clinic_tokens(self):
		# login patient and try to access /api/tokens/ which is staff/receptionist view
		login_resp = self.client.post("/api/login/", {"username": self.patient_data["username"], "password": self.patient_data["password"]}, format="json")
		self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
		token = login_resp.data.get('token')
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
		resp = self.client.get("/api/tokens/", format="json")
		# Patient is authenticated but should get empty list (no access to clinic tokens)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertEqual(resp.data, [])

	def test_staff_can_view_clinic_tokens(self):
		# login staff and access tokens
		login_resp = self.client.post("/api/login/staff/", {"username": self.staff_data["username"], "password": self.staff_data["password"]}, format="json")
		self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
		token = login_resp.data.get('token')
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
		resp = self.client.get("/api/tokens/", format="json")
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		# receptionist should see at least the sample token we created
		self.assertTrue(isinstance(resp.data, list))
		self.assertGreaterEqual(len(resp.data), 1)

	def test_ivr_confirm_links_existing_web_user(self):
		# If a web user with username==phone exists, IVR booking should link patient to that user
		phone = "+19990001122"
		existing_user = User.objects.create_user(username=phone, password="pw12345")
		# Ensure no patient exists yet for that number
		ClinicToken.objects.filter(patient__phone_number=phone).delete()
		from urllib.parse import urlencode
		query = urlencode({
			'doctor_id': str(self.doctor.id),
			'date': timezone.now().date().strftime('%Y-%m-%d'),
			'time': '09:15',
			'phone': phone
		})
		url = f"/api/ivr/confirm-booking/?{query}"
		# Send form-encoded body as Twilio would: Digits=1
		resp = self.client.post(url, "Digits=1", content_type='application/x-www-form-urlencoded')
		# The view returns TwiML text/XML; we check DB outcome
		patient_qs = Patient.objects.filter(phone_number=phone)
		self.assertTrue(patient_qs.exists())
		patient = patient_qs.first()
		# patient should be linked to existing_user
		self.assertIsNotNone(patient.user)
		self.assertEqual(patient.user.id, existing_user.id)
		# Token should be created for that patient
		self.assertTrue(ClinicToken.objects.filter(patient=patient).exists())

	def test_ivr_confirm_creates_new_user_when_missing(self):
		phone = "+19990002233"
		# Ensure no user or patient exists
		User.objects.filter(username=phone).delete()
		Patient.objects.filter(phone_number=phone).delete()
		from urllib.parse import urlencode
		query = urlencode({
			'doctor_id': str(self.doctor.id),
			'date': timezone.now().date().strftime('%Y-%m-%d'),
			'time': '09:30',
			'phone': phone
		})
		url = f"/api/ivr/confirm-booking/?{query}"
		# Send form-encoded body as Twilio would: Digits=1
		resp = self.client.post(url, "Digits=1", content_type='application/x-www-form-urlencoded')
		patient_qs = Patient.objects.filter(phone_number=phone)
		self.assertTrue(patient_qs.exists())
		patient = patient_qs.first()
		# new patient should have a linked user with username == phone
		self.assertIsNotNone(patient.user)
		self.assertEqual(patient.user.username, phone)
		self.assertTrue(ClinicToken.objects.filter(patient=patient).exists())

	def test_staff_login(self):
		url = "/api/login/staff/"
		response = self.client.post(url, {
			"username": self.staff_data["username"],
			"password": self.staff_data["password"]
		}, format="json")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("token", response.data)
		self.assertIn("role", response.data["user"])

	def test_patient_registration(self):
		url = "/api/register/patient/"
		new_patient_data = {
			"username": "newpatient",
			"password": "newpass123",
			"password2": "newpass123",
			"name": "New Patient",
			"age": 25,
			"phone_number": "+19876543210"
		}
		response = self.client.post(url, new_patient_data, format="json")
		self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
		self.assertIn("token", response.data)
		self.assertEqual(response.data["user"]["role"], "patient")


class StructuredSummaryTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='summuser', password='pw123')
		self.patient = Patient.objects.create(user=self.user, name='Sum Test', age=40, phone_number='+15552223333')
		# create a doctor just for relation
		clinic = Clinic.objects.create(name='Sum Clinic', address='Addr', city='City')
		doc_user = User.objects.create_user(username='docsum', password='pw')
		self.doctor = Doctor.objects.create(user=doc_user, name='Dr Sum', specialization='General', clinic=clinic)
		# create 2 consultations
		from .models import Consultation
		Consultation.objects.create(patient=self.patient, doctor=self.doctor, notes='Patient complains of fever and cough for 3 days. No known allergies. Takes paracetamol occasionally.')
		Consultation.objects.create(patient=self.patient, doctor=self.doctor, notes='Follow up: fever decreased, persistent cough. Suspect viral URI. Prescribed cough syrup.')

	def test_structured_summary_with_mock(self):
		# Mock the ai_summarizer to return a JSON string
		structured_json = {
			'chief_complaint': 'Fever and cough',
			'history_of_present_illness': '3 days of fever and cough',
			'past_medical_history': '',
			'medications': 'Paracetamol',
			'allergies': '',
			'examination_findings': 'Low-grade fever',
			'assessment': 'Viral URI',
			'plan': 'Supportive care, cough syrup'
		}

		mock_response_text = json.dumps(structured_json)

		with patch('api.ai_client.summarize_text') as mock_summarizer:
			mock_summarizer.return_value = [{'summary_text': mock_response_text}]
			# authenticate
			self.client.force_authenticate(user=self.user)
			url = f"/api/patient-summary/{self.patient.id}/"
			resp = self.client.get(url, format='json')
			self.assertEqual(resp.status_code, 200)
			for key in structured_json.keys():
				self.assertIn(key, resp.data)
			self.assertEqual(resp.data['chief_complaint'], structured_json['chief_complaint'])

	def test_fallback_to_text_when_no_json(self):
		# Model returns plain text without JSON
		with patch('api.ai_client.summarize_text') as mock_summarizer:
			mock_summarizer.return_value = [{'summary_text': 'This is a plain English summary without JSON.'}]
			self.client.force_authenticate(user=self.user)
			url = f"/api/patient-summary/{self.patient.id}/"
			resp = self.client.get(url, format='json')
			self.assertEqual(resp.status_code, 200)
			self.assertIn('summary_text', resp.data)
