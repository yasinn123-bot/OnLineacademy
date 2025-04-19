import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from core.models import (
    Course, Material, MaterialType, Test, Question, Answer, 
    UserProgress, Certificate
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample courses, materials, tests, and questions'

    def add_arguments(self, parser):
        parser.add_argument('--doctors', type=int, default=2, help='Number of doctor users to create')
        parser.add_argument('--students', type=int, default=5, help='Number of student users to create')
        parser.add_argument('--courses', type=int, default=4, help='Number of courses to create')
        parser.add_argument('--materials', type=int, default=20, help='Number of materials to create')
        parser.add_argument('--tests', type=int, default=8, help='Number of tests to create')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Get or create options
        num_doctors = options['doctors']
        num_students = options['students']
        num_courses = options['courses']
        num_materials = options['materials']
        num_tests = options['tests']
        
        # Create users if they don't exist
        doctors = self._create_doctors(num_doctors)
        students = self._create_students(num_students)
        
        # Create courses
        courses = self._create_courses(num_courses, doctors)
        
        # Create materials
        materials = self._create_materials(num_materials, courses, doctors)
        
        # Create tests
        tests = self._create_tests(num_tests, courses)
        
        # Create questions and answers for each test
        self._create_questions_and_answers(tests)
        
        # Enroll some students in courses
        self._enroll_students(students, courses)
        
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))
    
    def _create_doctors(self, num_doctors):
        self.stdout.write('Creating doctor users...')
        doctors = []
        
        # Check if we already have an admin user
        admin_exists = User.objects.filter(username='admin').exists()
        if not admin_exists:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword',
                first_name='Admin',
                last_name='User',
                role='doctor'
            )
            doctors.append(admin)
            self.stdout.write(f'  Created admin user: {admin.username}')
        
        # Create doctor users
        doctor_first_names = ['Иван', 'Елена', 'Михаил', 'Анна', 'Сергей', 'Ольга']
        doctor_last_names = ['Петров', 'Смирнова', 'Иванов', 'Козлова', 'Соколов', 'Морозова']
        
        existing_count = User.objects.filter(role='doctor').count()
        for i in range(num_doctors):
            first_name = random.choice(doctor_first_names)
            last_name = random.choice(doctor_last_names)
            username = f'doctor{existing_count + i + 1}'
            email = f'{username}@example.com'
            
            if not User.objects.filter(username=username).exists():
                doctor = User.objects.create_user(
                    username=username,
                    email=email,
                    password=f'password{i+1}',
                    first_name=first_name,
                    last_name=last_name,
                    role='doctor'
                )
                doctors.append(doctor)
                self.stdout.write(f'  Created doctor user: {doctor.username}')
        
        return doctors
    
    def _create_students(self, num_students):
        self.stdout.write('Creating student users...')
        students = []
        
        # Create student users
        student_first_names = ['Алексей', 'Мария', 'Дмитрий', 'Екатерина', 'Никита', 'Вероника']
        student_last_names = ['Кузнецов', 'Новикова', 'Федоров', 'Волкова', 'Андреев', 'Лебедева']
        
        existing_count = User.objects.filter(role='student').count()
        for i in range(num_students):
            first_name = random.choice(student_first_names)
            last_name = random.choice(student_last_names)
            username = f'student{existing_count + i + 1}'
            email = f'{username}@example.com'
            
            if not User.objects.filter(username=username).exists():
                student = User.objects.create_user(
                    username=username,
                    email=email,
                    password=f'password{i+1}',
                    first_name=first_name,
                    last_name=last_name,
                    role='student'
                )
                students.append(student)
                self.stdout.write(f'  Created student user: {student.username}')
        
        return students
    
    def _create_courses(self, num_courses, doctors):
        self.stdout.write('Creating courses...')
        courses = []
        
        course_titles = [
            'Основы детской онкологии',
            'Детская гематология: современные подходы',
            'Лимфомы у детей: диагностика и лечение',
            'Лейкозы в педиатрической практике',
            'Опухоли ЦНС у детей',
            'Нейробластома: протоколы лечения',
            'Саркомы мягких тканей в детском возрасте',
            'Солидные опухоли у детей',
            'Поддерживающая терапия в детской онкологии',
            'Трансплантация костного мозга у детей'
        ]
        
        languages = ['ru', 'en', 'ky']
        existing_count = Course.objects.count()
        
        for i in range(num_courses):
            if i < len(course_titles):
                title = course_titles[i]
            else:
                title = f'Курс {existing_count + i + 1}'
            
            description = f"""
            Этот курс предназначен для медицинских специалистов, работающих в области детской онкологии и гематологии.
            
            Цели курса:
            - Ознакомить с современными методами диагностики и лечения
            - Изучить международные протоколы лечения
            - Разобрать клинические случаи и особенности ведения пациентов
            - Обсудить актуальные проблемы и новые исследования в данной области
            
            Курс включает теоретические материалы, видеолекции, протоколы лечения и тестирование знаний.
            """
            
            doctor = random.choice(doctors)
            language = random.choice(languages)
            is_published = random.choice([True, True, False])  # 2/3 chance of being published
            
            course = Course.objects.create(
                title=title,
                description=description,
                author=doctor,
                is_published=is_published,
                language=language
            )
            courses.append(course)
            self.stdout.write(f'  Created course: {course.title}')
        
        return courses
    
    def _create_materials(self, num_materials, courses, doctors):
        self.stdout.write('Creating materials...')
        materials = []
        
        material_names = [
            'Введение в детскую онкологию',
            'Современная классификация опухолей у детей',
            'Методы диагностики в детской онкологии',
            'Принципы химиотерапии в педиатрии',
            'Лучевая терапия у детей',
            'Хирургическое лечение опухолей',
            'Острый лимфобластный лейкоз: протокол лечения',
            'Острый миелобластный лейкоз: протокол лечения',
            'Нейробластома: стадирование и лечение',
            'Опухоли ЦНС: классификация и диагностика',
            'Медуллобластома: современные подходы к лечению',
            'Саркомы мягких тканей: протоколы лечения',
            'Саркома Юинга: диагностика и лечение',
            'Остеосаркома: хирургическое лечение',
            'Лимфома Ходжкина у детей',
            'Неходжкинские лимфомы в педиатрии',
            'Опухоли печени у детей',
            'Ретинобластома: диагностика и лечение',
            'Опухоль Вильмса: протокол лечения',
            'Поддерживающая терапия при химиотерапии',
            'Инфекционные осложнения в детской онкологии',
            'Трансплантация костного мозга: показания и методы',
            'Психологическая поддержка детей с онкологическими заболеваниями',
            'Реабилитация после лечения'
        ]
        
        # Creating a media folder if it doesn't exist
        media_folder = os.path.join(settings.MEDIA_ROOT, 'materials')
        os.makedirs(media_folder, exist_ok=True)
        
        material_types = list(MaterialType)
        languages = ['ru', 'en', 'ky']
        
        existing_count = Material.objects.count()
        
        for i in range(num_materials):
            if i < len(material_names):
                name = material_names[i]
            else:
                name = f'Материал {existing_count + i + 1}'
            
            description = f"Учебный материал по теме '{name}'. Содержит основную информацию, методические рекомендации и практические примеры."
            material_type = random.choice(material_types).value
            doctor = random.choice(doctors)
            course = random.choice(courses) if courses and random.random() > 0.1 else None  # 10% chance of not being assigned to a course
            language = random.choice(languages)
            
            # Create a placeholder file (in production, real files would be uploaded)
            file_name = f"{slugify(name)}.txt"
            file_path = f"materials/{file_name}"
            
            # Create the file
            with open(os.path.join(settings.MEDIA_ROOT, 'materials', file_name), 'w', encoding='utf-8') as f:
                f.write(f"Sample content for {name}\n\n{description}")
            
            material = Material.objects.create(
                name=name,
                description=description,
                file=file_path,
                material_type=material_type,
                author=doctor,
                course=course,
                language=language
            )
            materials.append(material)
            self.stdout.write(f'  Created material: {material.name}')
        
        return materials
    
    def _create_tests(self, num_tests, courses):
        self.stdout.write('Creating tests...')
        tests = []
        
        test_titles = [
            'Тест по основам детской онкологии',
            'Проверка знаний по лейкозам',
            'Тест по солидным опухолям',
            'Контрольный тест по лимфомам',
            'Итоговый тест по опухолям ЦНС',
            'Проверка знаний по саркомам',
            'Тест по поддерживающей терапии',
            'Итоговый экзамен по курсу'
        ]
        
        languages = ['ru', 'en', 'ky']
        existing_count = Test.objects.count()
        
        for i in range(num_tests):
            if i < len(test_titles):
                title = test_titles[i]
            else:
                title = f'Тест {existing_count + i + 1}'
            
            description = f"Проверка знаний по темам курса. Для успешного прохождения необходимо набрать не менее {random.randint(60, 80)}% правильных ответов."
            course = random.choice(courses)
            passing_score = random.randint(60, 80)
            language = random.choice(languages)
            
            test = Test.objects.create(
                title=title,
                description=description,
                course=course,
                passing_score=passing_score,
                language=language
            )
            tests.append(test)
            self.stdout.write(f'  Created test: {test.title}')
        
        return tests
    
    def _create_questions_and_answers(self, tests):
        self.stdout.write('Creating questions and answers...')
        
        question_texts = [
            'Какой метод диагностики является основным при первичном обследовании ребенка с подозрением на онкологическое заболевание?',
            'Какой тип лейкоза наиболее часто встречается в детском возрасте?',
            'Какой цитостатический препарат относится к группе алкилирующих агентов?',
            'Какое осложнение химиотерапии требует немедленного прекращения введения препарата?',
            'Что такое нейробластома?',
            'Какой метод лечения является основным при остеосаркоме?',
            'Назовите основной метод лечения медуллобластомы у детей:',
            'Какие критерии используются для стадирования лимфомы Ходжкина?',
            'Какой препарат является антиметаболитом?',
            'Какое обследование необходимо провести перед началом химиотерапии?',
            'Что такое трансплантация гемопоэтических стволовых клеток?',
            'Каковы показания к трансплантации костного мозга при лейкозах у детей?',
            'Какой тип опухоли головного мозга наиболее часто встречается у детей?',
            'Какие факторы риска неблагоприятного исхода при остром лимфобластном лейкозе?',
            'Какое осложнение наиболее характерно для лучевой терапии опухолей ЦНС?',
            'Что такое таргетная терапия?',
            'Какой протокол лечения используется при стандартном риске острого лимфобластного лейкоза?',
            'Какова 5-летняя выживаемость при нейробластоме 4 стадии?',
            'Какие признаки характерны для синдрома лизиса опухоли?',
            'Какие заболевания относятся к опухолям кроветворной ткани?'
        ]
        
        for test in tests:
            # Create 5-10 questions per test
            num_questions = random.randint(5, 10)
            
            for i in range(num_questions):
                # Use predefined questions if available, otherwise generate a placeholder
                if i < len(question_texts):
                    text = question_texts[i]
                else:
                    text = f'Вопрос #{i+1} по теме "{test.title}"'
                
                points = random.randint(1, 3)  # Random points between 1-3
                
                question = Question.objects.create(
                    test=test,
                    text=text,
                    points=points
                )
                
                # Create 3-5 answers per question
                num_answers = random.randint(3, 5)
                correct_answer_index = random.randint(0, num_answers - 1)
                
                # Generate custom answers based on the question
                answers = self._generate_answers_for_question(text, num_answers)
                
                for j in range(num_answers):
                    is_correct = (j == correct_answer_index)
                    answer_text = answers[j] if j < len(answers) else f'Вариант ответа #{j+1}'
                    
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=is_correct
                    )
            
            self.stdout.write(f'  Created {num_questions} questions for test: {test.title}')
    
    def _generate_answers_for_question(self, question, num_answers):
        """Generate appropriate answers based on the question text"""
        
        if 'метод диагностики' in question:
            return ['МРТ', 'КТ', 'Рентгенография', 'Биопсия', 'УЗИ']
        elif 'тип лейкоза' in question:
            return ['Острый лимфобластный лейкоз', 'Острый миелобластный лейкоз', 'Хронический миелолейкоз', 'Хронический лимфолейкоз']
        elif 'препарат' in question and 'алкилирующих' in question:
            return ['Циклофосфамид', 'Метотрексат', 'Винкристин', 'Доксорубицин', 'Цитарабин']
        elif 'нейробластома' in question:
            return ['Злокачественная опухоль из клеток нервного гребня', 'Опухоль печени', 'Опухоль почки', 'Опухоль костного мозга']
        elif 'метод лечения' in question and 'остеосаркоме' in question:
            return ['Хирургическое удаление с химиотерапией', 'Только лучевая терапия', 'Только химиотерапия', 'Иммунотерапия']
        elif 'медуллобластомы' in question:
            return ['Комбинированное лечение (операция, лучевая терапия, химиотерапия)', 'Только хирургическое лечение', 'Только химиотерапия', 'Только лучевая терапия']
        elif 'лимфомы Ходжкина' in question:
            return ['Система Ann Arbor', 'Система TNM', 'Система Lugano', 'Система FIGO']
        elif 'антиметаболитом' in question:
            return ['Метотрексат', 'Доксорубицин', 'Винкристин', 'Циклофосфамид', 'Этопозид']
        elif 'трансплантация' in question:
            return ['Введение донорских стволовых клеток после миелоаблативной терапии', 'Переливание крови', 'Трансплантация костного мозга без предварительной подготовки', 'Введение стволовых клеток печени']
        elif 'опухоли головного мозга' in question:
            return ['Медуллобластома', 'Глиобластома', 'Менингиома', 'Астроцитома', 'Эпендимома']
        elif 'факторы риска' in question and 'лимфобластном лейкозе' in question:
            return ['Возраст старше 10 лет, гиперлейкоцитоз, t(9;22)', 'Возраст младше 1 года', 'Женский пол', 'Тип В-клеточный']
        elif 'осложнение' in question and 'лучевой терапии' in question:
            return ['Нейрокогнитивные нарушения', 'Полинейропатия', 'Кардиотоксичность', 'Нефротоксичность']
        elif 'таргетная терапия' in question:
            return ['Лечение, направленное на специфические молекулярные мишени опухолевых клеток', 'Химиотерапия', 'Лучевая терапия', 'Хирургическое лечение']
        elif 'протокол' in question and 'лимфобластного лейкоза' in question:
            return ['ALL-BFM', 'AIEOP-BFM', 'SIOP', 'COG', 'St. Jude']
        elif '5-летняя выживаемость' in question:
            return ['30-50%', '70-90%', '10-20%', 'Менее 10%', 'Более 90%']
        elif 'синдрома лизиса опухоли' in question:
            return ['Гиперурикемия, гиперкалиемия, гиперфосфатемия, гипокальциемия', 'Лихорадка и нейтропения', 'Тошнота и рвота', 'Анемия и тромбоцитопения']
        elif 'опухолям кроветворной ткани' in question:
            return ['Лейкозы, лимфомы, миелодиспластический синдром', 'Нейробластома, опухоль Вильмса', 'Саркомы мягких тканей', 'Опухоли ЦНС']
        else:
            # Default generic answers
            return [f'Вариант {i+1}' for i in range(num_answers)]
    
    def _enroll_students(self, students, courses):
        self.stdout.write('Enrolling students in courses...')
        
        for student in students:
            # Enroll each student in 1-3 random courses
            num_courses = random.randint(1, min(3, len(courses)))
            selected_courses = random.sample(courses, num_courses)
            
            for course in selected_courses:
                if not UserProgress.objects.filter(user=student, course=course).exists():
                    progress = UserProgress.objects.create(
                        user=student,
                        course=course
                    )
                    
                    # Randomly mark some materials as completed
                    course_materials = Material.objects.filter(course=course)
                    if course_materials.exists():
                        completed_count = random.randint(0, course_materials.count())
                        if completed_count > 0:
                            completed_materials = random.sample(list(course_materials), completed_count)
                            progress.materials_completed.add(*completed_materials)
                    
                    # Randomly mark some tests as completed
                    course_tests = Test.objects.filter(course=course)
                    if course_tests.exists():
                        completed_count = random.randint(0, course_tests.count())
                        if completed_count > 0:
                            completed_tests = random.sample(list(course_tests), completed_count)
                            progress.tests_completed.add(*completed_tests)
                    
                    # If all tests are completed, generate a certificate
                    all_completed = course_tests.count() > 0 and progress.tests_completed.count() == course_tests.count()
                    if all_completed:
                        certificate_id = f"{course.id}-{student.id}-{random.randint(10000, 99999)}"
                        score = random.uniform(70.0, 100.0)
                        
                        Certificate.objects.create(
                            user=student,
                            course=course,
                            certificate_id=certificate_id,
                            score=score
                        )
                        
                        self.stdout.write(f'  Created certificate for {student.username} in course "{course.title}"')
                    
                    self.stdout.write(f'  Enrolled {student.username} in course "{course.title}"') 