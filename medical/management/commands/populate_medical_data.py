from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import CustomUser
from medical.models import (Doctor, Specialization, Contact, Patient, 
                          Disease, MedicalHistory, DiseaseStatus)
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate the database with sample medical data for the Pediatric Oncology and Oncohematology Academy'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample medical data...')
        
        # Create user roles if they don't exist yet
        self.create_or_update_users()
        
        # Create specializations
        self.create_specializations()
        
        # Create doctors
        self.create_doctors()
        
        # Create patients
        self.create_patients()
        
        # Create contacts
        self.create_contacts()
        
        # Create diseases
        self.create_diseases()
        
        # Create medical histories
        self.create_medical_histories()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated the database with sample medical data!'))
    
    def create_or_update_users(self):
        # Admin superuser
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='doctor'
            )
            self.stdout.write(f'Created admin user: {admin}')
        
        # Doctors
        doctors_data = [
            {'username': 'doctor1', 'email': 'doctor1@example.com', 'first_name': 'Иван', 'last_name': 'Петров'},
            {'username': 'doctor2', 'email': 'doctor2@example.com', 'first_name': 'Елена', 'last_name': 'Смирнова'},
            {'username': 'doctor3', 'email': 'doctor3@example.com', 'first_name': 'Алексей', 'last_name': 'Иванов'},
            {'username': 'doctor4', 'email': 'doctor4@example.com', 'first_name': 'Мария', 'last_name': 'Козлова'},
            {'username': 'doctor5', 'email': 'doctor5@example.com', 'first_name': 'Дмитрий', 'last_name': 'Соколов'},
        ]
        
        for doctor_data in doctors_data:
            user, created = CustomUser.objects.get_or_create(
                username=doctor_data['username'],
                defaults={
                    'email': doctor_data['email'],
                    'first_name': doctor_data['first_name'],
                    'last_name': doctor_data['last_name'],
                    'role': 'doctor'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created doctor user: {user}')
        
        # Patients
        patients_data = [
            {'username': 'patient1', 'email': 'patient1@example.com', 'first_name': 'Анна', 'last_name': 'Михайлова'},
            {'username': 'patient2', 'email': 'patient2@example.com', 'first_name': 'Сергей', 'last_name': 'Кузнецов'},
            {'username': 'patient3', 'email': 'patient3@example.com', 'first_name': 'Ольга', 'last_name': 'Новикова'},
            {'username': 'patient4', 'email': 'patient4@example.com', 'first_name': 'Артём', 'last_name': 'Морозов'},
            {'username': 'patient5', 'email': 'patient5@example.com', 'first_name': 'Татьяна', 'last_name': 'Волкова'},
            {'username': 'patient6', 'email': 'patient6@example.com', 'first_name': 'Игорь', 'last_name': 'Павлов'},
            {'username': 'patient7', 'email': 'patient7@example.com', 'first_name': 'Наталья', 'last_name': 'Семенова'},
            {'username': 'patient8', 'email': 'patient8@example.com', 'first_name': 'Максим', 'last_name': 'Алексеев'},
            {'username': 'patient9', 'email': 'patient9@example.com', 'first_name': 'Екатерина', 'last_name': 'Лебедева'},
            {'username': 'patient10', 'email': 'patient10@example.com', 'first_name': 'Виктор', 'last_name': 'Козловский'},
        ]
        
        for patient_data in patients_data:
            user, created = CustomUser.objects.get_or_create(
                username=patient_data['username'],
                defaults={
                    'email': patient_data['email'],
                    'first_name': patient_data['first_name'],
                    'last_name': patient_data['last_name'],
                    'role': 'student'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created patient user: {user}')
    
    def create_specializations(self):
        specializations = [
            'Детская онкология',
            'Онкогематология',
            'Радиология',
            'Химиотерапия',
            'Хирургическая онкология',
            'Паллиативная помощь',
        ]
        
        for spec_name in specializations:
            spec, created = Specialization.objects.get_or_create(name=spec_name)
            if created:
                self.stdout.write(f'Created specialization: {spec}')
    
    def create_doctors(self):
        # Get all doctor users
        doctor_users = CustomUser.objects.filter(role='doctor')
        specializations = Specialization.objects.all()
        
        for doctor_user in doctor_users:
            # Skip if doctor profile already exists
            if hasattr(doctor_user, 'doctor_profile'):
                continue
                
            specialization = random.choice(specializations)
            experience_years = random.randint(3, 25)
            qualifications = [
                'Кандидат медицинских наук', 
                'Доктор медицинских наук', 
                'Высшая категория',
                'Первая категория',
                'Вторая категория'
            ]
            qualification = random.choice(qualifications)
            
            doctor = Doctor.objects.create(
                user=doctor_user,
                specialization=specialization,
                qualification=qualification,
                experience_years=experience_years
            )
            self.stdout.write(f'Created doctor profile: {doctor}')
    
    def create_patients(self):
        # Get all patient users
        patient_users = CustomUser.objects.filter(role='student')
        
        for patient_user in patient_users:
            # Skip if patient profile already exists
            if hasattr(patient_user, 'patient_profile'):
                continue
                
            patient = Patient.objects.create(user=patient_user)
            self.stdout.write(f'Created patient profile: {patient}')
    
    def create_contacts(self):
        # Create contacts for all users
        users = CustomUser.objects.all()
        
        contact_types = {
            'phone': ['8-900-123-4567', '8-911-234-5678', '8-922-345-6789', '8-933-456-7890', '8-944-567-8901'],
            'email': ['personal@example.com', 'work@example.com', 'private@mail.com', 'contact@mail.ru'],
            'telegram': ['@username', '@usercontact', '@doctoruser', '@patientuser']
        }
        
        for user in users:
            # Create 1-3 contacts for each user
            num_contacts = random.randint(1, 3)
            created_types = set()
            
            for _ in range(num_contacts):
                contact_type = random.choice(list(contact_types.keys()))
                
                # Make sure we don't create duplicate contact types for the same user
                if contact_type in created_types:
                    continue
                    
                created_types.add(contact_type)
                value = random.choice(contact_types[contact_type])
                
                contact = Contact.objects.create(
                    user=user,
                    code=contact_type,
                    value=value
                )
                self.stdout.write(f'Created contact: {contact}')
    
    def create_diseases(self):
        diseases = [
            {'name': 'Острый лимфобластный лейкоз', 'description': 'Наиболее распространенная форма рака у детей, затрагивающая лимфоциты в костном мозге.'},
            {'name': 'Нейробластома', 'description': 'Рак, развивающийся из незрелых нервных клеток нервной системы.'},
            {'name': 'Лимфома Ходжкина', 'description': 'Рак лимфатической системы, характеризующийся увеличением лимфатических узлов.'},
            {'name': 'Опухоль Вильмса', 'description': 'Редкий вид рака почек, встречающийся преимущественно у детей.'},
            {'name': 'Медуллобластома', 'description': 'Злокачественная опухоль мозжечка, относящаяся к эмбриональным опухолям.'},
            {'name': 'Остеосаркома', 'description': 'Злокачественная опухоль костной ткани, чаще встречающаяся в длинных костях.'},
            {'name': 'Ретинобластома', 'description': 'Редкое злокачественное заболевание сетчатки глаза.'},
            {'name': 'Рабдомиосаркома', 'description': 'Злокачественная опухоль мягких тканей, развивающаяся из эмбриональной мезенхимы.'},
        ]
        
        for disease_data in diseases:
            disease, created = Disease.objects.get_or_create(
                name=disease_data['name'],
                defaults={'description': disease_data['description']}
            )
            if created:
                self.stdout.write(f'Created disease: {disease}')
    
    def create_medical_histories(self):
        patients = Patient.objects.all()
        doctors = Doctor.objects.all()
        diseases = Disease.objects.all()
        
        # Each patient may have 1-3 medical histories
        for patient in patients:
            num_histories = random.randint(1, 3)
            
            for _ in range(num_histories):
                doctor = random.choice(doctors)
                disease = random.choice(diseases)
                
                # Randomize status (70% in treatment, 30% cured)
                status = DiseaseStatus.DURING_TREATMENT if random.random() < 0.7 else DiseaseStatus.CURED
                
                # For start date, pick a random date within the last 2 years
                days_ago = random.randint(1, 730)  # Up to 2 years ago
                start_date = timezone.now().date() - timedelta(days=days_ago)
                
                # For end date, only set if status is cured and make it after start date
                end_date = None
                if status == DiseaseStatus.CURED:
                    recovery_days = random.randint(30, 365)  # Recovery took between 1 month and 1 year
                    end_date = start_date + timedelta(days=recovery_days)
                
                notes = "Пациент проходит стандартный протокол лечения. Наблюдаются побочные эффекты средней тяжести."
                if status == DiseaseStatus.CURED:
                    notes = "Пациент успешно завершил лечение. Рекомендовано регулярное наблюдение."
                
                medical_history = MedicalHistory.objects.create(
                    patient=patient,
                    disease=disease,
                    doctor=doctor,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    notes=notes
                )
                self.stdout.write(f'Created medical history: {medical_history}') 