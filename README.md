# Онлайн-академия детской онкологии и онкогематологии

Платформа для обучения врачей, студентов и родителей основам детской онкологии и онкогематологии.

## О проекте

Онлайн-академия предоставляет доступ к образовательным материалам по детской онкологии и онкогематологии, помогая специалистам повышать свою квалификацию, студентам получать необходимые знания, а родителям лучше понимать диагнозы и методы лечения своих детей.

### Функциональность

- Личный кабинет для трех ролей пользователей (врач/студент/родитель)
- Раздел видеолекций и презентаций с возможностью загрузки нового контента
- Библиотека документов (протоколы, исследования, рекомендации)
- Система комментариев для обсуждения материалов
- Тестирование и выдача сертификатов
- Поддержка русского, английского и кыргызского языков

## Технологии

- **Backend**: Django, PostgreSQL
- **Frontend**: Django templates, Bootstrap 5
- **API**: Django REST Framework

## Установка и запуск

### Предварительные требования

- Python 3.8+
- PostgreSQL
- pip

### Установка

1. Клонировать репозиторий:
```
git clone https://github.com/username/online_academy_backend.git
cd online_academy_backend
```

2. Создать и активировать виртуальное окружение:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Установить зависимости:
```
pip install -r requirements.txt
```

4. Создать базу данных PostgreSQL:
```sql
CREATE DATABASE online_academy;
CREATE USER postgres WITH PASSWORD 'postgres';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE online_academy TO postgres;
```

5. Выполнить миграции:
```
python manage.py migrate
```

6. Создать суперпользователя:
```
python manage.py createsuperuser
```

7. Запустить сервер разработки:
```
python manage.py runserver
```

## Разработка

Для разработки проекта выполните следующие шаги:

1. Настройте локальное окружение согласно инструкциям выше
2. Создайте ветку для своих изменений:
```
git checkout -b feature/name-of-feature
```
3. Внесите изменения и создайте pull request

### Структура проекта

- `online_academy_backend/` - Основной проект Django
- `core/` - Основное приложение
  - `models.py` - Модели данных
  - `views.py` - Представления
  - `serializers.py` - Сериализаторы DRF
  - `urls.py` - Маршруты URL
- `templates/` - HTML шаблоны
- `static/` - Статические файлы (CSS, JS, изображения)
- `media/` - Загружаемые файлы (видео, презентации, документы)

## Команда проекта

- Руководитель проекта: Yasin Arstanbekov
- Разработчики: Yasin Arstanbekov, Rahatbekov Iman

## Лицензия

Этот проект распространяется под лицензией [указать лицензию]. См. файл LICENSE для получения дополнительной информации.

## Контакт