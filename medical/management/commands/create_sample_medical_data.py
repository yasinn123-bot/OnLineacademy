from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from medical.models import Doctor, Patient, Specialization, Disease, MedicalHistory, Contact
from core.models import CustomUser
import random

class Command(BaseCommand):
    help = 'Creates sample medical data for testing the doctor dashboard'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample medical data...')
        
        # Create doctor users if they don't exist
        User = get_user_model()
        
        # First check if we have a doctor user
        try:
            doctor_user = User.objects.get(username='doctor1')
            self.stdout.write(self.style.SUCCESS(f'Found existing doctor user: {doctor_user.username}'))
        except User.DoesNotExist:
            doctor_user = User.objects.create_user(
                username='doctor1',
                email='doctor1@example.com',
                password='doctorpass123',
                first_name='Иван',
                last_name='Петров',
                role='doctor'
            )
            self.stdout.write(self.style.SUCCESS(f'Created new doctor user: {doctor_user.username}'))
        
        # Create specializations
        specializations = [
            'Онкология',
            'Гематология',
            'Педиатрия',
            'Хирургия',
            'Радиология'
        ]
        
        created_specializations = []
        for spec_name in specializations:
            spec, created = Specialization.objects.get_or_create(name=spec_name)
            created_specializations.append(spec)
            status = 'Created' if created else 'Found existing'
            self.stdout.write(self.style.SUCCESS(f'{status} specialization: {spec.name}'))
        
        # Create doctor profile if it doesn't exist
        try:
            doctor = Doctor.objects.get(user=doctor_user)
            self.stdout.write(self.style.SUCCESS(f'Found existing doctor profile for: {doctor_user.username}'))
        except Doctor.DoesNotExist:
            doctor = Doctor.objects.create(
                user=doctor_user,
                specialization=created_specializations[0],  # Онкология
                qualification='Высшая категория',
                experience_years=10
            )
            self.stdout.write(self.style.SUCCESS(f'Created doctor profile for: {doctor_user.username}'))
        
        # Create patient users
        patient_data = [
            {
                'username': 'patient1', 
                'email': 'patient1@example.com',
                'first_name': 'Алексей',
                'last_name': 'Иванов',
                'contact': '+996 555 123 456'
            },
            {
                'username': 'patient2', 
                'email': 'patient2@example.com',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'contact': '+996 555 234 567'
            },
            {
                'username': 'patient3', 
                'email': 'patient3@example.com',
                'first_name': 'Дмитрий',
                'last_name': 'Кузнецов',
                'contact': '+996 555 345 678'
            },
        ]
        
        created_patients = []
        for p_data in patient_data:
            try:
                patient_user = User.objects.get(username=p_data['username'])
                self.stdout.write(self.style.SUCCESS(f"Found existing patient user: {patient_user.username}"))
            except User.DoesNotExist:
                patient_user = User.objects.create_user(
                    username=p_data['username'],
                    email=p_data['email'],
                    password='patientpass123',
                    first_name=p_data['first_name'],
                    last_name=p_data['last_name'],
                    role='patient'
                )
                self.stdout.write(self.style.SUCCESS(f"Created patient user: {patient_user.username}"))
            
            # Create patient profile
            try:
                patient = Patient.objects.get(user=patient_user)
                self.stdout.write(self.style.SUCCESS(f"Found existing patient profile for: {patient_user.username}"))
            except Patient.DoesNotExist:
                patient = Patient.objects.create(user=patient_user)
                self.stdout.write(self.style.SUCCESS(f"Created patient profile for: {patient_user.username}"))
            
            created_patients.append(patient)
            
            # Create contact for patient
            contact, created = Contact.objects.get_or_create(
                user=patient_user,
                code='phone',
                defaults={'value': p_data['contact']}
            )
            status = 'Created' if created else 'Found existing'
            self.stdout.write(self.style.SUCCESS(f"{status} contact for {patient_user.username}: {contact.value}"))
        
        # Create diseases
        diseases = [
            {'name': 'Лейкемия', 'description': 'Рак клеток крови'},
            {'name': 'Лимфома', 'description': 'Рак лимфатической системы'},
            {'name': 'Анемия', 'description': 'Снижение уровня гемоглобина в крови'},
            {'name': 'Тромбоцитопения', 'description': 'Снижение количества тромбоцитов'},
            {'name': 'Нейробластома', 'description': 'Злокачественная опухоль симпатической нервной системы'},
        ]
        
        created_diseases = []
        for disease_data in diseases:
            disease, created = Disease.objects.get_or_create(
                name=disease_data['name'],
                defaults={'description': disease_data['description']}
            )
            created_diseases.append(disease)
            status = 'Created' if created else 'Found existing'
            self.stdout.write(self.style.SUCCESS(f"{status} disease: {disease.name}"))
        
        # Create medical histories
        histories_data = [
            {'patient': created_patients[0], 'disease': created_diseases[0], 'status': MedicalHistory.DiseaseStatus.DURING_TREATMENT},
            {'patient': created_patients[1], 'disease': created_diseases[2], 'status': MedicalHistory.DiseaseStatus.CURED},
            {'patient': created_patients[2], 'disease': created_diseases[1], 'status': MedicalHistory.DiseaseStatus.DURING_TREATMENT},
            {'patient': created_patients[0], 'disease': created_diseases[3], 'status': MedicalHistory.DiseaseStatus.CURED},
        ]
        
        for history_data in histories_data:
            # Check if a similar history already exists
            existing_history = MedicalHistory.objects.filter(
                patient=history_data['patient'],
                disease=history_data['disease'],
                doctor=doctor
            ).first()
            
            if existing_history:
                self.stdout.write(self.style.SUCCESS(
                    f"Found existing medical history: {history_data['patient']} - {history_data['disease']}"
                ))
            else:
                history = MedicalHistory.objects.create(
                    patient=history_data['patient'],
                    disease=history_data['disease'],
                    doctor=doctor,
                    status=history_data['status']
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Created medical history: {history.patient} - {history.disease} ({history.get_status_display()})"
                ))
        
        self.stdout.write(self.style.SUCCESS('Sample medical data creation completed!'))
        self.stdout.write(self.style.SUCCESS(
            'You can now log in as doctor1 (password: doctorpass123) to view the doctor dashboard.'
        )) 