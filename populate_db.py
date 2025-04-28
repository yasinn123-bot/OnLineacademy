import os
import django
import random
import uuid
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_academy_backend.settings')
django.setup()

# Import models
from core.models import (
    CustomUser, Course, Module, Lesson, LessonContent, UserProgress, LearningOutcome
)
from quiz.models import Quiz, Question, Choice

# Create a superuser (if it doesn't exist)
def create_users():
    # Create a superuser
    if not CustomUser.objects.filter(username='admin').exists():
        superuser = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        print(f"Created superuser: {superuser.username}")
    
    # Create a doctor user
    if not CustomUser.objects.filter(username='doctor').exists():
        doctor = CustomUser.objects.create_user(
            username='doctor',
            email='doctor@example.com',
            password='doctorpassword',
            first_name='Doctor',
            last_name='Smith',
            role='doctor'
        )
        print(f"Created doctor user: {doctor.username}")
    
    # Create a student user
    if not CustomUser.objects.filter(username='student').exists():
        student = CustomUser.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpassword',
            first_name='Student',
            last_name='Johnson',
            role='student'
        )
        print(f"Created student user: {student.username}")
    
    return CustomUser.objects.get(username='doctor'), CustomUser.objects.get(username='student')

# Sample data for courses
course_data = [
    {
        'title': 'Основы детской онкологии',
        'description': 'Базовый курс по основам детской онкологии. Включает в себя введение в предмет, основные патологии и подходы к лечению.',
        'language': 'ru',
        'time_limit': 60,
        'passing_score': 70,
    },
    {
        'title': 'Современные методы лечения в детской онкогематологии',
        'description': 'Курс посвящен современным методам лечения злокачественных заболеваний крови у детей. Рассматриваются протоколы химиотерапии, таргетная терапия и трансплантация костного мозга.',
        'language': 'ru',
        'time_limit': 90,
        'passing_score': 75,
    },
    {
        'title': 'Диагностика солидных опухолей у детей',
        'description': 'Углубленный курс по диагностике солидных опухолей у детей. Рассматриваются методы визуализации, лабораторной диагностики и патоморфологические исследования.',
        'language': 'ru',
        'time_limit': 60,
        'passing_score': 80,
    }
]

# Sample learning outcomes
learning_outcomes = [
    'Понимание основных принципов диагностики онкологических заболеваний у детей',
    'Знание современных протоколов лечения детских онкологических заболеваний',
    'Умение интерпретировать результаты лабораторных и инструментальных исследований',
    'Навыки планирования и мониторинга терапии',
    'Понимание психосоциальных аспектов ведения онкологических пациентов детского возраста',
    'Знание принципов паллиативной помощи детям с онкологическими заболеваниями'
]

# Module template data 
module_templates = [
    {
        'title': 'Введение в предмет',
        'description': 'Вводный модуль, знакомящий с основными понятиями и терминологией.'
    },
    {
        'title': 'Диагностические методы',
        'description': 'Обзор современных методов диагностики в детской онкологии.'
    },
    {
        'title': 'Основные протоколы лечения',
        'description': 'Изучение стандартных протоколов лечения различных онкологических заболеваний у детей.'
    },
    {
        'title': 'Практические аспекты',
        'description': 'Практические аспекты ведения пациентов с онкологическими заболеваниями.'
    }
]

# Lesson template data
lesson_templates = [
    {
        'title': 'Введение и цели обучения',
        'description': 'Обзор целей и задач курса, основные понятия.',
        'estimated_time': 15
    },
    {
        'title': 'Эпидемиология детских онкологических заболеваний',
        'description': 'Статистика заболеваемости и распространенности онкологических заболеваний у детей.',
        'estimated_time': 30
    },
    {
        'title': 'Клинические проявления',
        'description': 'Основные симптомы и синдромы, характерные для онкологических заболеваний у детей.',
        'estimated_time': 45
    },
    {
        'title': 'Лабораторная диагностика',
        'description': 'Основные лабораторные методы диагностики онкологических заболеваний у детей.',
        'estimated_time': 40
    },
    {
        'title': 'Инструментальная диагностика',
        'description': 'Методы визуализации и другие инструментальные методы исследования.',
        'estimated_time': 35
    },
    {
        'title': 'Принципы химиотерапии',
        'description': 'Основные принципы и протоколы химиотерапии в детской онкологии.',
        'estimated_time': 50
    },
    {
        'title': 'Таргетная терапия',
        'description': 'Современные возможности таргетной терапии в детской онкологии.',
        'estimated_time': 40
    },
    {
        'title': 'Лучевая терапия',
        'description': 'Принципы и особенности применения лучевой терапии у детей с онкологическими заболеваниями.',
        'estimated_time': 35
    }
]

# Lesson content templates
content_templates = [
    {
        'title': 'Введение',
        'content': '<p>Добро пожаловать на урок. В этом материале мы рассмотрим основные аспекты темы, ключевые понятия и их применение в клинической практике.</p>'
    },
    {
        'title': 'Основные понятия',
        'content': '<p>В этом разделе рассматриваются основные понятия и терминология, необходимые для понимания темы.</p><ul><li>Понятие 1 - объяснение</li><li>Понятие 2 - объяснение</li><li>Понятие 3 - объяснение</li></ul>'
    },
    {
        'title': 'Клинические аспекты',
        'content': '<p>Клинические проявления и их значение в диагностике заболевания:</p><ol><li>Симптом 1 - описание и клиническое значение</li><li>Симптом 2 - описание и клиническое значение</li><li>Симптом 3 - описание и клиническое значение</li></ol>'
    },
    {
        'title': 'Диагностические критерии',
        'content': '<p>Для постановки диагноза необходимо учитывать следующие критерии:</p><ol><li>Критерий 1 - описание</li><li>Критерий 2 - описание</li><li>Критерий 3 - описание</li></ol>'
    },
    {
        'title': 'Алгоритм лечения',
        'content': '<p>Алгоритм лечения включает следующие этапы:</p><ol><li>Этап 1 - описание и рекомендации</li><li>Этап 2 - описание и рекомендации</li><li>Этап 3 - описание и рекомендации</li></ol>'
    },
    {
        'title': 'Итоги и выводы',
        'content': '<p>В этом уроке мы рассмотрели основные аспекты темы. Ключевые выводы:</p><ul><li>Вывод 1</li><li>Вывод 2</li><li>Вывод 3</li></ul>'
    }
]

# Quiz templates
quiz_templates = [
    {
        'title': 'Тест по основам онкологии',
        'description': 'Проверка знаний по основным понятиям детской онкологии',
        'time_limit': 20,
        'passing_score': 70
    },
    {
        'title': 'Тест по диагностике',
        'description': 'Оценка знаний методов диагностики онкологических заболеваний у детей',
        'time_limit': 30,
        'passing_score': 75
    },
    {
        'title': 'Тест по методам лечения',
        'description': 'Проверка знаний протоколов и стандартов лечения в детской онкологии',
        'time_limit': 25,
        'passing_score': 80
    }
]

# Question templates
question_templates = [
    {
        'text': 'Какие из следующих симптомов являются наиболее характерными для лейкоза у детей?',
        'question_type': 'multiple',
        'points': 2,
        'explanation': 'Основными симптомами лейкоза у детей являются бледность, геморрагический синдром, лихорадка и увеличение лимфатических узлов.',
        'choices': [
            {'text': 'Бледность кожных покровов', 'is_correct': True},
            {'text': 'Геморрагический синдром', 'is_correct': True},
            {'text': 'Лихорадка', 'is_correct': True},
            {'text': 'Увеличение лимфатических узлов', 'is_correct': True},
            {'text': 'Повышение артериального давления', 'is_correct': False}
        ]
    },
    {
        'text': 'Какой метод является золотым стандартом для диагностики острого лимфобластного лейкоза?',
        'question_type': 'single',
        'points': 1,
        'explanation': 'Миелограмма (исследование костного мозга) является золотым стандартом диагностики ОЛЛ.',
        'choices': [
            {'text': 'Клинический анализ крови', 'is_correct': False},
            {'text': 'Миелограмма', 'is_correct': True},
            {'text': 'Компьютерная томография', 'is_correct': False},
            {'text': 'Ультразвуковое исследование', 'is_correct': False}
        ]
    },
    {
        'text': 'Верно ли утверждение, что нейробластома является наиболее распространенной солидной внечерепной опухолью у детей?',
        'question_type': 'true_false',
        'points': 1,
        'explanation': 'Нейробластома действительно является наиболее распространенной солидной внечерепной опухолью детского возраста.',
        'choices': [
            {'text': 'Верно', 'is_correct': True},
            {'text': 'Неверно', 'is_correct': False}
        ]
    },
    {
        'text': 'Какие из следующих факторов имеют неблагоприятное прогностическое значение при нейробластоме у детей?',
        'question_type': 'multiple',
        'points': 2,
        'explanation': 'Неблагоприятными прогностическими факторами при нейробластоме являются: возраст старше 18 месяцев, N-myc амплификация, поздняя стадия заболевания и неблагоприятный гистологический подтип.',
        'choices': [
            {'text': 'Возраст старше 18 месяцев', 'is_correct': True},
            {'text': 'N-myc амплификация', 'is_correct': True},
            {'text': 'Поздняя стадия заболевания', 'is_correct': True},
            {'text': 'Локализация в забрюшинном пространстве', 'is_correct': False},
            {'text': 'Неблагоприятный гистологический подтип', 'is_correct': True}
        ]
    },
    {
        'text': 'Какой антибиотик из группы антрациклинов чаще всего используется в протоколах лечения острого лимфобластного лейкоза у детей?',
        'question_type': 'single',
        'points': 1,
        'explanation': 'Доксорубицин является антрациклиновым антибиотиком, наиболее часто используемым в протоколах лечения ОЛЛ у детей.',
        'choices': [
            {'text': 'Доксорубицин', 'is_correct': True},
            {'text': 'Цисплатин', 'is_correct': False},
            {'text': 'Циклофосфамид', 'is_correct': False},
            {'text': 'Винкристин', 'is_correct': False}
        ]
    },
    {
        'text': 'Укажите, какой возраст является наиболее типичным для развития нефробластомы (опухоли Вильмса) у детей?',
        'question_type': 'short_answer',
        'points': 1,
        'explanation': 'Типичный возраст манифестации нефробластомы у детей - от 2 до 5 лет.',
        'choices': [
            {'text': '2-5 лет', 'is_correct': True},
            {'text': '2-5', 'is_correct': True},
            {'text': 'от 2 до 5 лет', 'is_correct': True}
        ]
    }
]

def create_courses(doctor):
    courses = []
    for course_data_item in course_data:
        # Check if course exists
        existing_course = Course.objects.filter(title=course_data_item['title']).first()
        if existing_course:
            courses.append(existing_course)
            print(f"Course already exists: {existing_course.title}")
            continue
        
        # Create course
        course = Course.objects.create(
            title=course_data_item['title'],
            description=course_data_item['description'],
            language=course_data_item['language'],
            author=doctor,
            is_published=True,
            created_at=timezone.now()
        )
        
        # Add learning outcomes
        sample_outcomes = random.sample(learning_outcomes, 3)
        for outcome_text in sample_outcomes:
            LearningOutcome.objects.create(
                course=course,
                text=outcome_text
            )
        
        courses.append(course)
        print(f"Created course: {course.title}")
    
    return courses

def create_modules(courses):
    modules = []
    for course in courses:
        # Check if module exists for this course
        existing_modules = Module.objects.filter(course=course)
        if existing_modules.exists():
            modules.extend(list(existing_modules))
            print(f"Modules already exist for course: {course.title}")
            continue
        
        # Create modules
        for i, module_template in enumerate(module_templates):
            module = Module.objects.create(
                title=module_template['title'],
                description=module_template['description'],
                course=course,
                order=i+1
            )
            modules.append(module)
            print(f"Created module: {module.title} for course: {course.title}")
    
    return modules

def create_lessons(modules):
    lessons = []
    for module in modules:
        # Check if lessons exist for this module
        existing_lessons = Lesson.objects.filter(module=module)
        if existing_lessons.exists():
            lessons.extend(list(existing_lessons))
            print(f"Lessons already exist for module: {module.title}")
            continue
        
        # Create 2-3 lessons per module
        num_lessons = random.randint(2, 3)
        selected_lessons = random.sample(lesson_templates, num_lessons)
        
        for i, lesson_template in enumerate(selected_lessons):
            lesson = Lesson.objects.create(
                title=lesson_template['title'],
                description=lesson_template['description'],
                module=module,
                estimated_time=lesson_template['estimated_time'],
                order=i+1
            )
            lessons.append(lesson)
            print(f"Created lesson: {lesson.title} for module: {module.title}")
    
    return lessons

def create_lesson_contents(lessons):
    for lesson in lessons:
        # Check if content exists for this lesson
        existing_contents = LessonContent.objects.filter(lesson=lesson)
        if existing_contents.exists():
            print(f"Content already exists for lesson: {lesson.title}")
            continue
        
        # Create 3-5 content steps per lesson
        num_contents = random.randint(3, 5)
        selected_contents = random.sample(content_templates, num_contents)
        
        for i, content_template in enumerate(selected_contents):
            content = LessonContent.objects.create(
                lesson=lesson,
                title=content_template['title'],
                content=content_template['content'],
                order=i+1
            )
            print(f"Created content: {content.title} for lesson: {lesson.title}")

def create_quizzes(modules):
    for module in modules:
        # Check if quiz exists for this module
        existing_quiz = Quiz.objects.filter(module=module).first()
        if existing_quiz:
            print(f"Quiz already exists for module: {module.title}")
            continue
        
        # Create quiz
        quiz_template = random.choice(quiz_templates)
        quiz = Quiz.objects.create(
            title=f"{quiz_template['title']} - {module.title}",
            description=quiz_template['description'],
            course=module.course,
            module=module,
            time_limit=quiz_template['time_limit'],
            passing_score=quiz_template['passing_score'],
            is_published=True
        )
        
        # Create questions
        num_questions = random.randint(3, 6)
        selected_questions = random.sample(question_templates, num_questions)
        
        for i, question_template in enumerate(selected_questions):
            question = Question.objects.create(
                quiz=quiz,
                text=question_template['text'],
                question_type=question_template['question_type'],
                points=question_template['points'],
                explanation=question_template['explanation'],
                order=i+1
            )
            
            # Create choices
            for choice_data in question_template['choices']:
                Choice.objects.create(
                    question=question,
                    text=choice_data['text'],
                    is_correct=choice_data['is_correct']
                )
        
        print(f"Created quiz: {quiz.title} with {num_questions} questions")

def enroll_student(student, courses):
    for course in courses:
        # Check if already enrolled
        if UserProgress.objects.filter(user=student, course=course).exists():
            print(f"Student already enrolled in course: {course.title}")
            continue
        
        # Create progress record
        progress = UserProgress.objects.create(
            user=student,
            course=course,
            last_access=timezone.now()
        )
        print(f"Enrolled student in course: {course.title}")

def main():
    print("Starting database population...")
    
    # Create users
    doctor, student = create_users()
    
    # Create courses
    courses = create_courses(doctor)
    
    # Create modules
    modules = create_modules(courses)
    
    # Create lessons
    lessons = create_lessons(modules)
    
    # Create lesson content
    create_lesson_contents(lessons)
    
    # Create quizzes
    create_quizzes(modules)
    
    # Enroll student in courses
    enroll_student(student, courses)
    
    print("Database population complete!")

if __name__ == "__main__":
    main() 