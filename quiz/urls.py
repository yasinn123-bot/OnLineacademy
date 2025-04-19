from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'quizzes', views.QuizViewSet, basename='quiz-api')
router.register(r'quiz-attempts', views.QuizAttemptViewSet, basename='quiz-attempt-api')

app_name = 'quiz'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Template views
    path('', views.quiz_list, name='quiz_list'),
    path('<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('<int:pk>/take/', views.take_quiz, name='take_quiz'),
    path('attempts/<int:attempt_id>/submit/', views.submit_answer, name='submit_answer'),
    path('attempts/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
    
    # Quiz management
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:pk>/edit/', views.edit_quiz, name='edit_quiz'),
    path('<int:pk>/delete/', views.delete_quiz, name='delete_quiz'),
    path('<int:quiz_id>/questions/create/', views.create_question, name='create_question'),
    path('questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
] 