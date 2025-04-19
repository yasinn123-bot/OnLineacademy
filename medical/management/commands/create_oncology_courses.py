from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import CustomUser, Course, Material, MaterialType
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create oncology and oncohematology related courses and materials'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating oncology courses and materials...')
        
        # Get first admin or doctor for course authorship
        try:
            author = CustomUser.objects.filter(is_staff=True).first() or CustomUser.objects.filter(role='doctor').first()
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('No suitable author found. Please create an admin or doctor user first.'))
            return
        
        self.stdout.write(f'Using author: {author}')
        
        # Create courses
        courses_data = [
            {
                'title': 'Основы детской онкологии',
                'description': 'Введение в детскую онкологию для медицинских специалистов. Курс охватывает основные принципы диагностики, лечения и последующего наблюдения детей с онкологическими заболеваниями.',
                'language': 'ru',
                'is_published': True,
                'materials': [
                    {
                        'name': 'Введение в детскую онкологию',
                        'description': 'Обзор особенностей онкологических заболеваний у детей',
                        'material_type': MaterialType.PRESENTATION,
                        'language': 'ru'
                    },
                    {
                        'name': 'Эпидемиология детского рака',
                        'description': 'Статистика и распространенность онкологических заболеваний среди детей',
                        'material_type': MaterialType.DOCUMENT,
                        'language': 'ru'
                    },
                    {
                        'name': 'Диагностические методы',
                        'description': 'Современные методы диагностики онкологических заболеваний у детей',
                        'material_type': MaterialType.VIDEO,
                        'language': 'ru'
                    },
                    {
                        'name': 'Основные протоколы лечения',
                        'description': 'Обзор стандартных протоколов лечения детских онкологических заболеваний',
                        'material_type': MaterialType.PROTOCOL,
                        'language': 'ru'
                    }
                ]
            },
            {
                'title': 'Детская онкогематология: новые подходы',
                'description': 'Углубленный курс по современным методам лечения гематологических злокачественных новообразований у детей.',
                'language': 'ru',
                'is_published': True,
                'materials': [
                    {
                        'name': 'Острый лимфобластный лейкоз: современные протоколы',
                        'description': 'Детальный обзор современных протоколов лечения ОЛЛ у детей',
                        'material_type': MaterialType.PROTOCOL,
                        'language': 'ru'
                    },
                    {
                        'name': 'Острый миелоидный лейкоз у детей',
                        'description': 'Особенности диагностики и лечения ОМЛ в педиатрии',
                        'material_type': MaterialType.PRESENTATION,
                        'language': 'ru'
                    },
                    {
                        'name': 'Трансплантация костного мозга',
                        'description': 'Показания и методики трансплантации костного мозга у детей',
                        'material_type': MaterialType.VIDEO,
                        'language': 'ru'
                    },
                    {
                        'name': 'Таргетная терапия в детской онкогематологии',
                        'description': 'Новые таргетные препараты и их применение в детской онкогематологии',
                        'material_type': MaterialType.RESEARCH,
                        'language': 'ru'
                    }
                ]
            },
            {
                'title': 'Солидные опухоли у детей',
                'description': 'Комплексный курс по диагностике и лечению солидных опухолей у детей, включая нейробластому, опухоль Вильмса и другие.',
                'language': 'ru',
                'is_published': True,
                'materials': [
                    {
                        'name': 'Нейробластома: диагностика и стадирование',
                        'description': 'Современные подходы к диагностике и определению стадии нейробластомы',
                        'material_type': MaterialType.PRESENTATION,
                        'language': 'ru'
                    },
                    {
                        'name': 'Опухоль Вильмса: хирургические аспекты',
                        'description': 'Хирургическое лечение опухоли Вильмса у детей',
                        'material_type': MaterialType.VIDEO,
                        'language': 'ru'
                    },
                    {
                        'name': 'Рабдомиосаркома: комплексный подход',
                        'description': 'Мультидисциплинарный подход к лечению рабдомиосаркомы',
                        'material_type': MaterialType.DOCUMENT,
                        'language': 'ru'
                    },
                    {
                        'name': 'Новые методы лучевой терапии при солидных опухолях',
                        'description': 'Инновационные методики лучевой терапии для минимизации побочных эффектов',
                        'material_type': MaterialType.RESEARCH,
                        'language': 'ru'
                    }
                ]
            },
            {
                'title': 'Психосоциальная поддержка детей с онкологическими заболеваниями',
                'description': 'Курс для медицинских работников о психологических аспектах сопровождения детей с онкологическими заболеваниями и их семей.',
                'language': 'ru',
                'is_published': True,
                'materials': [
                    {
                        'name': 'Психологические аспекты диагностики рака у ребенка',
                        'description': 'Как говорить с семьей о диагнозе и помогать адаптироваться',
                        'material_type': MaterialType.PRESENTATION,
                        'language': 'ru'
                    },
                    {
                        'name': 'Поддержка во время лечения',
                        'description': 'Методы психологической поддержки пациентов и их семей во время лечения',
                        'material_type': MaterialType.VIDEO,
                        'language': 'ru'
                    },
                    {
                        'name': 'Возвращение к обычной жизни после лечения',
                        'description': 'Социальная реабилитация после окончания активной фазы лечения',
                        'material_type': MaterialType.DOCUMENT,
                        'language': 'ru'
                    },
                    {
                        'name': 'Работа с детьми в паллиативной ситуации',
                        'description': 'Особенности поддержки детей и семей в паллиативной ситуации',
                        'material_type': MaterialType.RECOMMENDATION,
                        'language': 'ru'
                    }
                ]
            },
        ]
        
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'description': course_data['description'],
                    'language': course_data['language'],
                    'is_published': course_data['is_published'],
                    'author': author,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(f'Created course: {course.title}')
                
                # Create materials for this course
                for material_data in course_data['materials']:
                    material = Material.objects.create(
                        name=material_data['name'],
                        description=material_data['description'],
                        material_type=material_data['material_type'],
                        language=material_data['language'],
                        author=author,
                        course=course,
                        # Using a placeholder file since we can't create actual files in this example
                        file=None
                    )
                    self.stdout.write(f'  - Created material: {material.name}')
            else:
                self.stdout.write(f'Course already exists: {course.title}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created oncology courses and materials!')) 