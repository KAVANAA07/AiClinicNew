from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import re
import json
from .models import Patient, Consultation, PrescriptionItem
from .serializers import ConsultationSerializer

class MedicalSummaryView(APIView):
    """
    Generate structured medical summary with prescription, labs, medications, 
    diagnosis, and allergen warnings
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        phone_number = request.query_params.get('phone')
        patient_id = request.query_params.get('patient_id')
        
        if not phone_number and not patient_id:
            return Response({
                'error': 'Phone number or patient_id parameter is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find patient(s) by phone or ID
            if patient_id:
                patients = [Patient.objects.get(id=patient_id)]
            else:
                # Normalize phone number for search
                normalized_phone = self.normalize_phone_number(phone_number)
                patients = []
                for patient in Patient.objects.all():
                    if self.normalize_phone_number(patient.phone_number) == normalized_phone:
                        patients.append(patient)
                
                if not patients:
                    return Response({
                        'error': 'Patient not found with this phone number.',
                        'searched_phone': phone_number
                    }, status=status.HTTP_404_NOT_FOUND)

            # Get all consultations for matching patients
            patient_ids = [p.id for p in patients]
            consultations = Consultation.objects.filter(
                patient_id__in=patient_ids
            ).order_by('-date')

            if not consultations.exists():
                return Response({
                    'error': 'No consultation history found for this patient.'
                }, status=status.HTTP_404_NOT_FOUND)

            # Generate structured medical summary
            summary = self.generate_medical_summary(consultations, patients[0])
            
            return Response(summary, status=status.HTTP_200_OK)

        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error generating medical summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def normalize_phone_number(self, phone):
        """Normalize phone number by removing country codes and special chars"""
        if not phone:
            return phone
        digits_only = re.sub(r'\D', '', str(phone))
        if not digits_only:
            return phone
        
        # Remove country codes
        if digits_only.startswith('91') and len(digits_only) == 12:
            return digits_only[2:]
        elif digits_only.startswith('1') and len(digits_only) == 11:
            return digits_only[1:]
        
        if len(digits_only) > 10:
            return digits_only[-10:]
        return digits_only

    def generate_medical_summary(self, consultations, primary_patient):
        """Generate structured medical summary"""
        
        # Initialize summary structure
        summary = {
            'patient_info': {
                'name': primary_patient.name,
                'age': primary_patient.age,
                'phone_number': primary_patient.phone_number,
                'patient_id': primary_patient.id
            },
            'summary_generated_at': timezone.now().isoformat(),
            'total_consultations': consultations.count(),
            'recent_consultations': [],
            'medical_categories': {
                'prescriptions': [],
                'laboratory_tests': [],
                'medications': [],
                'diagnoses': [],
                'allergies': [],
                'vital_signs': [],
                'procedures': []
            },
            'risk_alerts': [],
            'consultation_links': []
        }

        # Process each consultation
        for consultation in consultations[:10]:  # Last 10 consultations
            consultation_data = {
                'id': consultation.id,
                'date': consultation.date.strftime('%Y-%m-%d'),
                'doctor_name': consultation.doctor.name,
                'doctor_specialization': consultation.doctor.specialization,
                'notes_preview': consultation.notes[:100] + '...' if len(consultation.notes) > 100 else consultation.notes,
                'link': f'/api/consultation/{consultation.id}/',
                'has_prescriptions': consultation.prescription_items.exists()
            }
            summary['recent_consultations'].append(consultation_data)
            summary['consultation_links'].append({
                'consultation_id': consultation.id,
                'date': consultation.date.strftime('%Y-%m-%d'),
                'doctor': consultation.doctor.name,
                'link': f'/api/consultation/{consultation.id}/'
            })

            # Extract medical information from notes
            self.extract_medical_info(consultation, summary['medical_categories'])
            
            # Process prescriptions
            self.process_prescriptions(consultation, summary)

        # Generate risk alerts
        summary['risk_alerts'] = self.generate_risk_alerts(summary['medical_categories'])
        
        # Sort categories by recency
        for category in summary['medical_categories']:
            if isinstance(summary['medical_categories'][category], list):
                summary['medical_categories'][category].sort(
                    key=lambda x: x.get('date', ''), reverse=True
                )

        return summary

    def extract_medical_info(self, consultation, categories):
        """Extract structured medical information from consultation notes"""
        notes = consultation.notes.lower()
        consultation_date = consultation.date.strftime('%Y-%m-%d')
        
        # Extract diagnoses
        diagnosis_keywords = ['diagnosed', 'diagnosis', 'condition', 'disease', 'disorder']
        for keyword in diagnosis_keywords:
            if keyword in notes:
                # Extract sentence containing diagnosis
                sentences = consultation.notes.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        categories['diagnoses'].append({
                            'diagnosis': sentence.strip(),
                            'date': consultation_date,
                            'doctor': consultation.doctor.name,
                            'consultation_id': consultation.id,
                            'severity': self.assess_severity(sentence)
                        })
                        break

        # Extract allergies
        allergy_keywords = ['allergy', 'allergic', 'adverse reaction', 'intolerance']
        for keyword in allergy_keywords:
            if keyword in notes:
                sentences = consultation.notes.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        categories['allergies'].append({
                            'allergen': sentence.strip(),
                            'date': consultation_date,
                            'doctor': consultation.doctor.name,
                            'consultation_id': consultation.id,
                            'risk_level': 'HIGH'  # Always mark allergies as high risk
                        })
                        break

        # Extract vital signs
        vital_patterns = [
            r'bp[:\s]*(\d+/\d+)',
            r'blood pressure[:\s]*(\d+/\d+)',
            r'temperature[:\s]*(\d+\.?\d*)',
            r'pulse[:\s]*(\d+)',
            r'weight[:\s]*(\d+\.?\d*)',
            r'height[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in vital_patterns:
            matches = re.finditer(pattern, notes)
            for match in matches:
                vital_type = pattern.split('[')[0].replace('\\', '').upper()
                categories['vital_signs'].append({
                    'vital_type': vital_type,
                    'value': match.group(1) if match.groups() else match.group(0),
                    'date': consultation_date,
                    'doctor': consultation.doctor.name,
                    'consultation_id': consultation.id
                })

        # Extract lab tests
        lab_keywords = ['test', 'lab', 'blood work', 'x-ray', 'scan', 'mri', 'ct scan', 'ultrasound']
        for keyword in lab_keywords:
            if keyword in notes:
                sentences = consultation.notes.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        categories['laboratory_tests'].append({
                            'test_name': sentence.strip(),
                            'date': consultation_date,
                            'doctor': consultation.doctor.name,
                            'consultation_id': consultation.id,
                            'status': 'ORDERED'  # Default status
                        })
                        break

        # Extract procedures
        procedure_keywords = ['procedure', 'surgery', 'operation', 'treatment', 'therapy']
        for keyword in procedure_keywords:
            if keyword in notes:
                sentences = consultation.notes.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        categories['procedures'].append({
                            'procedure_name': sentence.strip(),
                            'date': consultation_date,
                            'doctor': consultation.doctor.name,
                            'consultation_id': consultation.id
                        })
                        break

    def process_prescriptions(self, consultation, summary):
        """Process prescription items with risk assessment"""
        prescriptions = consultation.prescription_items.all()
        
        for prescription in prescriptions:
            # Check for dangerous medications
            risk_level = self.assess_medication_risk(prescription.medicine_name)
            
            prescription_data = {
                'medicine_name': prescription.medicine_name,
                'dosage': prescription.dosage,
                'duration_days': prescription.duration_days,
                'timing': {
                    'morning': prescription.timing_morning,
                    'afternoon': prescription.timing_afternoon,
                    'evening': prescription.timing_evening
                },
                'date': consultation.date.strftime('%Y-%m-%d'),
                'doctor': consultation.doctor.name,
                'consultation_id': consultation.id,
                'risk_level': risk_level,
                'is_controlled_substance': self.is_controlled_substance(prescription.medicine_name)
            }
            
            summary['medical_categories']['prescriptions'].append(prescription_data)
            summary['medical_categories']['medications'].append(prescription_data)

    def assess_medication_risk(self, medicine_name):
        """Assess risk level of medication"""
        medicine_lower = medicine_name.lower()
        
        # High-risk medications
        high_risk_meds = [
            'warfarin', 'heparin', 'insulin', 'morphine', 'fentanyl',
            'chemotherapy', 'methotrexate', 'lithium', 'digoxin'
        ]
        
        # Medium-risk medications
        medium_risk_meds = [
            'aspirin', 'ibuprofen', 'acetaminophen', 'prednisone',
            'antibiotics', 'steroids'
        ]
        
        for high_risk in high_risk_meds:
            if high_risk in medicine_lower:
                return 'HIGH'
        
        for medium_risk in medium_risk_meds:
            if medium_risk in medicine_lower:
                return 'MEDIUM'
        
        return 'LOW'

    def is_controlled_substance(self, medicine_name):
        """Check if medication is a controlled substance"""
        controlled_substances = [
            'morphine', 'oxycodone', 'fentanyl', 'codeine', 'tramadol',
            'lorazepam', 'diazepam', 'alprazolam', 'clonazepam'
        ]
        
        medicine_lower = medicine_name.lower()
        return any(substance in medicine_lower for substance in controlled_substances)

    def assess_severity(self, text):
        """Assess severity of diagnosis or condition"""
        text_lower = text.lower()
        
        high_severity_keywords = ['severe', 'critical', 'emergency', 'acute', 'cancer', 'tumor']
        medium_severity_keywords = ['moderate', 'chronic', 'persistent']
        
        for keyword in high_severity_keywords:
            if keyword in text_lower:
                return 'HIGH'
        
        for keyword in medium_severity_keywords:
            if keyword in text_lower:
                return 'MEDIUM'
        
        return 'LOW'

    def generate_risk_alerts(self, categories):
        """Generate risk alerts based on medical information"""
        alerts = []
        
        # Check for high-risk allergies
        for allergy in categories['allergies']:
            alerts.append({
                'type': 'ALLERGY_ALERT',
                'severity': 'HIGH',
                'message': f"ALLERGY ALERT: {allergy['allergen']}",
                'date': allergy['date'],
                'consultation_id': allergy['consultation_id']
            })
        
        # Check for high-risk medications
        for medication in categories['medications']:
            if medication.get('risk_level') == 'HIGH':
                alerts.append({
                    'type': 'MEDICATION_RISK',
                    'severity': 'HIGH',
                    'message': f"HIGH-RISK MEDICATION: {medication['medicine_name']}",
                    'date': medication['date'],
                    'consultation_id': medication['consultation_id']
                })
            
            if medication.get('is_controlled_substance'):
                alerts.append({
                    'type': 'CONTROLLED_SUBSTANCE',
                    'severity': 'MEDIUM',
                    'message': f"CONTROLLED SUBSTANCE: {medication['medicine_name']}",
                    'date': medication['date'],
                    'consultation_id': medication['consultation_id']
                })
        
        # Check for high-severity diagnoses
        for diagnosis in categories['diagnoses']:
            if diagnosis.get('severity') == 'HIGH':
                alerts.append({
                    'type': 'CRITICAL_DIAGNOSIS',
                    'severity': 'HIGH',
                    'message': f"CRITICAL CONDITION: {diagnosis['diagnosis']}",
                    'date': diagnosis['date'],
                    'consultation_id': diagnosis['consultation_id']
                })
        
        return alerts


class ConsultationDetailView(APIView):
    """
    Get detailed consultation information with full notes and prescriptions
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, consultation_id):
        try:
            consultation = Consultation.objects.get(id=consultation_id)
            
            # Check if user has permission to view this consultation
            if hasattr(request.user, 'doctor'):
                # Doctors can only view their own consultations
                if consultation.doctor != request.user.doctor:
                    return Response({
                        'error': 'Access denied. You can only view your own consultations.'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Serialize consultation with full details
            serializer = ConsultationSerializer(consultation)
            consultation_data = serializer.data
            
            # Add additional medical structure
            consultation_data['medical_structure'] = self.structure_consultation_notes(consultation)
            
            return Response(consultation_data, status=status.HTTP_200_OK)
            
        except Consultation.DoesNotExist:
            return Response({
                'error': 'Consultation not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error retrieving consultation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def structure_consultation_notes(self, consultation):
        """Structure consultation notes into medical categories"""
        notes = consultation.notes
        
        # Split notes into sections
        sections = {
            'chief_complaint': '',
            'history_of_present_illness': '',
            'physical_examination': '',
            'assessment': '',
            'plan': '',
            'prescriptions': [],
            'follow_up': ''
        }
        
        # Extract prescriptions
        prescriptions = consultation.prescription_items.all()
        for prescription in prescriptions:
            sections['prescriptions'].append({
                'medicine_name': prescription.medicine_name,
                'dosage': prescription.dosage,
                'duration_days': prescription.duration_days,
                'timing': {
                    'morning': prescription.timing_morning,
                    'afternoon': prescription.timing_afternoon,
                    'evening': prescription.timing_evening
                }
            })
        
        # Try to extract structured information from notes
        lines = notes.split('\n')
        current_section = 'chief_complaint'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Identify section headers
            if any(keyword in line_lower for keyword in ['chief complaint', 'cc:', 'complaint']):
                current_section = 'chief_complaint'
            elif any(keyword in line_lower for keyword in ['history', 'hpi:', 'present illness']):
                current_section = 'history_of_present_illness'
            elif any(keyword in line_lower for keyword in ['examination', 'physical', 'pe:', 'exam']):
                current_section = 'physical_examination'
            elif any(keyword in line_lower for keyword in ['assessment', 'diagnosis', 'impression']):
                current_section = 'assessment'
            elif any(keyword in line_lower for keyword in ['plan', 'treatment', 'management']):
                current_section = 'plan'
            elif any(keyword in line_lower for keyword in ['follow up', 'followup', 'next visit']):
                current_section = 'follow_up'
            else:
                # Add line to current section
                if sections[current_section]:
                    sections[current_section] += '\n' + line
                else:
                    sections[current_section] = line
        
        return sections