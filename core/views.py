from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count, Prefetch
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import uuid
import json
from django.contrib import messages
import os
from django.views.decorators.http import require_POST
from django.utils import timezone

from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import (
    CustomUser, Course, Material, Comment, Test, Question, Answer,
    Certificate, UserProgress, Module, Lesson, LessonContent, LearningOutcome
)
from .serializers import (
    CustomUserSerializer, CourseSerializer, MaterialSerializer,
    CommentSerializer, TestSerializer, QuestionSerializer, 
    AnswerSerializer, CertificateSerializer, UserProgressSerializer,
    RegisterSerializer, LoginSerializer
)
from .forms import (
    CourseForm, MaterialForm, CommentForm, ModuleForm, LessonForm, LessonContentForm
)

# Helper functions
def get_user_role(user):
    return user.role if user.is_authenticated else None

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# REST API Views
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        tokens = get_tokens_for_user(user)
        
        return Response({
            'user': serializer.data,
            'tokens': tokens,
            'message': _('User registered successfully')
        }, status=status.HTTP_201_CREATED)

class CustomLoginView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        
        # Generate JWT tokens
        tokens = get_tokens_for_user(user)
        
        return Response({
            'tokens': tokens,
            'user_id': user.pk,
            'email': user.email,
            'role': user.role
        })

class CustomLogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def post(self, request):
        try:
            # Get the JWT token from the request
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Also perform Django logout
            logout(request)
            
            return Response({"message": _("Successfully logged out.")})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAdminUser,)
    authentication_classes = [JWTAuthentication, SessionAuthentication]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        # If user is admin or author, show all courses
        if user.is_staff or Course.objects.filter(author=user).exists():
            return Course.objects.all()
        # Others can only see published courses
        return Course.objects.filter(is_published=True)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        # Check if user is already enrolled
        if UserProgress.objects.filter(user=user, course=course).exists():
            return Response({"detail": _("Already enrolled in this course.")}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Create progress record
        progress = UserProgress.objects.create(user=user, course=course)
        
        return Response({"detail": _("Successfully enrolled.")}, 
                       status=status.HTTP_201_CREATED)

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all().order_by('-created_at')
    serializer_class = MaterialSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        # Admins and content creators see all
        if user.is_staff or Material.objects.filter(author=user).exists():
            return Material.objects.all().order_by('-created_at')
        # Filter by language or course if specified
        queryset = Material.objects.filter(
            Q(course__is_published=True) | Q(course__isnull=True)
        ).order_by('-created_at')
        
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
            
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        material_type = self.request.query_params.get('type')
        if material_type:
            queryset = queryset.filter(material_type=material_type)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        material = self.get_object()
        user = request.user
        
        # Ensure the user is enrolled in the course
        if not material.course:
            return Response({"detail": _("This material is not part of any course.")}, 
                           status=status.HTTP_400_BAD_REQUEST)
            
        progress, created = UserProgress.objects.get_or_create(
            user=user, course=material.course
        )
        
        progress.materials_completed.add(material)
        
        return Response({"detail": _("Material marked as completed.")})

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        test = self.get_object()
        user = request.user
        answers = request.data.get('answers', [])
        
        total_points = sum(q.points for q in test.questions.all())
        earned_points = 0
        
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            answer_id = answer_data.get('answer_id')
            
            question = get_object_or_404(Question, id=question_id, test=test)
            correct_answers = Answer.objects.filter(question=question, is_correct=True)
            selected_answer = get_object_or_404(Answer, id=answer_id, question=question)
            
            if selected_answer.is_correct:
                earned_points += question.points
        
        score_percentage = (earned_points / total_points) * 100 if total_points > 0 else 0
        
        # Mark test as completed
        progress, created = UserProgress.objects.get_or_create(
            user=user, course=test.course
        )
        progress.tests_completed.add(test)
        
        # Check if user passed the test
        if score_percentage >= test.passing_score:
            # Generate certificate if all tests are completed
            course_tests = Test.objects.filter(course=test.course)
            completed_tests = progress.tests_completed.all()
            
            if set(course_tests) <= set(completed_tests):
                certificate_id = f"{test.course.id}-{user.id}-{uuid.uuid4().hex[:8]}"
                certificate, created = Certificate.objects.get_or_create(
                    user=user,
                    course=test.course,
                    defaults={
                        'certificate_id': certificate_id,
                        'score': score_percentage
                    }
                )
                
                return Response({
                    "score": score_percentage,
                    "passed": True,
                    "certificate_id": certificate.certificate_id if certificate else None
                })
        
        return Response({
            "score": score_percentage,
            "passed": score_percentage >= test.passing_score
        })

class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Certificate.objects.all()
        return Certificate.objects.filter(user=user)

class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        material_id = self.request.query_params.get('material')
        if material_id:
            return Comment.objects.filter(material_id=material_id, parent__isnull=True)
        return Comment.objects.filter(parent__isnull=True)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(author=user)

class UserProgressView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        progress, created = UserProgress.objects.get_or_create(
            user=request.user, course=course
        )
        
        serializer = UserProgressSerializer(progress)
        return Response(serializer.data)

# Template-based Views
@cache_page(60 * 5)  # Cache for 5 minutes
def home(request):
    user_role = get_user_role(request.user)
    # Get featured courses for homepage with select_related for author
    featured_courses = Course.objects.filter(is_published=True).select_related('author').order_by('-created_at')[:6]
    
    context = {
        'featured_courses': featured_courses,
        'user_role': user_role,
    }
    return render(request, 'core/home.html', context)

def login_view(request):
    """Template view for login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'dashboard')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, otherwise to dashboard
            return redirect(next_url)
        else:
            # Show error message
            return render(request, 'core/login.html', {
                'form': {'errors': True},
                'next': next_url
            })
    
    # For GET requests, show the login form
    next_url = request.GET.get('next', '')
    context = {'next': next_url}
    return render(request, 'core/login.html', context)

def register_view(request):
    """Template view for registration page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Extract form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        
        # Basic validation
        context = {'errors': []}
        
        # Check if the username exists
        if CustomUser.objects.filter(username=username).exists():
            context['errors'].append(_('Имя пользователя уже занято'))
        
        # Check if the email exists
        if CustomUser.objects.filter(email=email).exists():
            context['errors'].append(_('Email уже используется'))
        
        # Check if passwords match
        if password != password_confirm:
            context['errors'].append(_('Пароли не совпадают'))
        
        # If there are errors, return them
        if context['errors']:
            return render(request, 'core/register.html', context)
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        # Log the user in
        login(request, user)
        
        # Redirect to dashboard
        return redirect('dashboard')
    
    context = {}
    return render(request, 'core/register.html', context)

def logout_view(request):
    """Template view for logout"""
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    user_role = user.role
    context = {
        'user': user,
        'user_role': user_role,
    }
    
    # Get all courses the user is enrolled in
    user_progress_list = UserProgress.objects.filter(user=user).select_related('course').prefetch_related(
        'materials_completed', 'tests_completed', 'lessons_completed'
    )
    
    # For student and parent dashboard
    if user_role in ['student', 'parent']:
        enrolled_courses = []
        completed_lessons_count = 0
        total_lessons_count = 0
        completed_quizzes_count = 0
        total_quizzes_count = 0
        
        # Process each course enrollment
        for progress in user_progress_list:
            course = progress.course
            
            # Calculate progress percentage
            total_lessons = Lesson.objects.filter(module__course=course).count()
            completed_lessons = progress.lessons_completed.count()
            
            if total_lessons > 0:
                progress_percentage = (completed_lessons / total_lessons) * 100
            else:
                progress_percentage = 0
                
            # Find next lesson to continue
            next_lesson = None
            for module in course.modules.all().order_by('order'):
                if not next_lesson:
                    for lesson in module.lessons.all().order_by('order'):
                        if lesson not in progress.lessons_completed.all():
                            next_lesson = lesson
                            break
            
            enrolled_courses.append({
                'course': course,
                'progress_percentage': round(progress_percentage),
                'last_access': progress.last_access,
                'next_lesson': next_lesson
            })
            
            # Update statistics
            completed_lessons_count += completed_lessons
            total_lessons_count += total_lessons
            completed_quizzes_count += progress.tests_completed.count()
            total_quizzes_count += course.quizzes.count()
        
        # Get certificates
        certificates = Certificate.objects.filter(user=user).select_related('course')
        
        # Calculate averages for statistics
        completed_lessons_percentage = 0
        if total_lessons_count > 0:
            completed_lessons_percentage = (completed_lessons_count / total_lessons_count) * 100
            
        completed_quizzes_percentage = 0
        if total_quizzes_count > 0:
            completed_quizzes_percentage = (completed_quizzes_count / total_quizzes_count) * 100
        
        # Find next content to study
        next_content = None
        if enrolled_courses:
            for enrollment in enrolled_courses:
                if enrollment['next_lesson']:
                    next_content = {
                        'type': 'lesson',
                        'title': enrollment['next_lesson'].title,
                        'course': enrollment['course'],
                        'estimated_time': enrollment['next_lesson'].estimated_time,
                        'url': f"/lessons/{enrollment['next_lesson'].id}/"
                    }
                    break
        
        # Get suggested courses based on user's interests and enrollment history
        suggested_courses = Course.objects.filter(is_published=True).exclude(
            id__in=[enrollment['course'].id for enrollment in enrolled_courses]
        )[:3]
        
        # Get recent activities (placeholder - implement actual activity tracking)
        recent_activities = []
        
        context.update({
            'enrolled_courses': enrolled_courses,
            'enrolled_courses_count': len(enrolled_courses),
            'completed_courses_count': Certificate.objects.filter(user=user).count(),
            'certificates_count': certificates.count(),
            'certificates': certificates[:3],  # Show only the most recent certificates
            'completed_lessons_count': completed_lessons_count,
            'total_lessons_count': total_lessons_count,
            'completed_lessons_percentage': round(completed_lessons_percentage),
            'completed_quizzes_count': completed_quizzes_count,
            'total_quizzes_count': total_quizzes_count,
            'completed_quizzes_percentage': round(completed_quizzes_percentage),
            'average_quiz_score': 0,  # Placeholder - implement actual calculation
            'next_content': next_content,
            'suggested_courses': suggested_courses,
            'recent_activities': recent_activities
        })
    
    # For doctor dashboard
    elif user_role == 'doctor':
        created_courses = Course.objects.filter(author=user)
        created_materials = Material.objects.filter(author=user)
        
        context.update({
            'created_courses': created_courses,
            'created_materials': created_materials,
        })
    
    return render(request, 'core/dashboard.html', context)

@cache_page(60 * 5)  # Cache for 5 minutes
def course_list(request):
    user_role = get_user_role(request.user)
    
    # Start with a base queryset with select_related for author
    courses = Course.objects.filter(is_published=True).select_related('author')
    
    # Filter by language if specified
    language = request.GET.get('language')
    if language:
        courses = courses.filter(language=language)
    
    context = {
        'courses': courses,
        'user_role': user_role,
    }
    return render(request, 'core/course_list.html', context)

def course_detail(request, pk):
    # Try to get from cache first
    cache_key = f'course_detail_{pk}_{request.user.id if request.user.is_authenticated else 0}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'core/course_detail.html', cached_data)
    
    course = get_object_or_404(Course.objects.select_related('author'), pk=pk)
    user_role = get_user_role(request.user)
    
    # Check if the user is enrolled
    is_enrolled = False
    user_progress = None
    next_lesson = None
    
    if request.user.is_authenticated:
        user_progress = UserProgress.objects.filter(
            user=request.user, course=course
        ).prefetch_related('materials_completed', 'tests_completed', 'lessons_completed').first()
        is_enrolled = user_progress is not None
    
    # Import Quiz model here to avoid circular imports
    from quiz.models import Quiz, QuizAttempt
    
    # Get quizzes for this course
    quizzes = Quiz.objects.filter(course=course).prefetch_related('questions')
    
    # Check for completed quizzes
    completed_quizzes = {}
    if is_enrolled and request.user.is_authenticated:
        # Get all passed attempts
        passed_attempts = QuizAttempt.objects.filter(
            user=request.user,
            quiz__in=quizzes,
            is_completed=True
        ).values_list('quiz_id', flat=True)
        
        # Mark quizzes as completed
        completed_quizzes = {quiz_id: True for quiz_id in passed_attempts}
        
        # Find the next lesson to continue with
        if user_progress:
            # Get all lessons for this course
            from core.models import Lesson
            all_lessons = Lesson.objects.filter(module__course=course).order_by('module__order', 'order')
            
            # Get the completed lessons IDs
            completed_lesson_ids = set(user_progress.lessons_completed.values_list('id', flat=True))
            
            # Find the first uncompleted lesson
            for lesson in all_lessons:
                if lesson.id not in completed_lesson_ids:
                    next_lesson = lesson
                    break
            
            # If all lessons are completed but no next lesson is set, set it to the first lesson
            if next_lesson is None and all_lessons.exists():
                next_lesson = all_lessons.first()
    
    context = {
        'course': course,
        'materials': Material.objects.filter(course=course).select_related('author'),
        'tests': quizzes,
        'is_enrolled': is_enrolled,
        'user_progress': user_progress,
        'user_role': user_role,
        'completed_quizzes': completed_quizzes,
        'next_lesson': next_lesson
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, context, 60 * 5)
    
    return render(request, 'core/course_detail.html', context)

@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material.objects.select_related('author', 'course'), pk=pk)
    user_role = get_user_role(request.user)
    
    # Get comments with their authors
    comments = Comment.objects.filter(material=material, parent__isnull=True).select_related('author')
    
    # Check if material is completed by user
    is_completed = False
    if request.user.is_authenticated and material.course:
        progress = UserProgress.objects.filter(
            user=request.user, course=material.course
        ).prefetch_related('materials_completed').first()
        if progress:
            is_completed = material in progress.materials_completed.all()
    
    context = {
        'material': material,
        'comments': comments,
        'is_completed': is_completed,
        'user_role': user_role,
    }
    return render(request, 'core/material_detail.html', context)

@login_required
def comment_create(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        material_id = request.POST.get('material_id')
        parent_id = request.POST.get('parent_id')
        
        material = get_object_or_404(Material, id=material_id)
        
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id)
            Comment.objects.create(
                content=content,
                author=request.user,
                material=material,
                parent=parent
            )
        else:
            Comment.objects.create(
                content=content,
                author=request.user,
                material=material
            )
        
        return redirect('material-detail', pk=material_id)
    
    return redirect('home')

@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, id=pk)
    
    # Check if the user is the author of the comment
    if request.user == comment.author or request.user.is_staff:
        material_id = comment.material.id
        comment.delete()
        return redirect('material-detail', pk=material_id)
    
    # If not authorized
    return redirect('home')

@login_required
def add_comment(request, material_id):
    """
    Add a comment to a material
    """
    material = get_object_or_404(Material, id=material_id)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Comment.objects.create(
                material=material,
                author=request.user,
                text=text,
                parent=None
            )
            messages.success(request, _("Комментарий добавлен."))
        else:
            messages.error(request, _("Текст комментария не может быть пустым."))
    
    return redirect('material-detail', pk=material_id)

@login_required
def add_reply(request, comment_id):
    """
    Add a reply to a comment
    """
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Comment.objects.create(
                material=parent_comment.material,
                author=request.user,
                text=text,
                parent=parent_comment
            )
            messages.success(request, _("Ответ добавлен."))
        else:
            messages.error(request, _("Текст ответа не может быть пустым."))
    
    return redirect('material-detail', pk=parent_comment.material.id)

@login_required
def delete_comment(request, comment_id):
    """
    Delete a comment
    """
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check if user is the author or has permission
    if request.user == comment.author or request.user.is_staff:
        material_id = comment.material.id
        comment.delete()
        messages.success(request, _("Комментарий удален."))
        return redirect('material-detail', pk=material_id)
    else:
        messages.error(request, _("У вас нет прав для удаления этого комментария."))
        return redirect('material-detail', pk=comment.material.id)

@login_required
def test_detail(request, pk):
    test = get_object_or_404(Test.objects.select_related('course'), pk=pk)
    user_role = get_user_role(request.user)
    
    # Check if test is already completed
    is_completed = False
    if request.user.is_authenticated:
        progress = UserProgress.objects.filter(
            user=request.user, course=test.course
        ).prefetch_related('tests_completed').first()
        if progress:
            is_completed = test in progress.tests_completed.all()
    
    # Prefetch questions with their answers
    questions = Question.objects.filter(test=test).prefetch_related('answers')
    
    context = {
        'test': test,
        'questions': questions,
        'is_completed': is_completed,
        'user_role': user_role,
    }
    return render(request, 'core/test_detail.html', context)

@login_required
def certificate_list(request):
    user_role = get_user_role(request.user)
    certificates = Certificate.objects.filter(user=request.user)
    
    context = {
        'certificates': certificates,
        'user_role': user_role,
    }
    return render(request, 'core/certificate_list.html', context)

def certificate_detail(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
    user_role = get_user_role(request.user)
    
    context = {
        'certificate': certificate,
        'user_role': user_role,
    }
    return render(request, 'core/certificate_detail.html', context)

@login_required
def profile(request):
    user = request.user
    user_role = get_user_role(user)
    
    if request.method == 'POST':
        # Simple form processing
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
            
        user.save()
        return redirect('user-profile')
    
    context = {
        'user': user,
        'user_role': user_role,
    }
    return render(request, 'core/profile.html', context)

@login_required
def course_certificate(request, course_id):
    """
    View for generating and displaying a course completion certificate
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    
    # Check if user has completed the course
    user_progress = get_object_or_404(UserProgress, user=user, course=course)
    
    if not user_progress.is_completed:
        messages.error(request, _("Вы должны завершить курс, чтобы получить сертификат."))
        return redirect('course-detail', pk=course_id)
    
    # Get or create certificate
    certificate, created = Certificate.objects.get_or_create(
        user=user,
        course=course,
        defaults={
            'certificate_id': str(uuid.uuid4())[:8].upper(),
            'issue_date': timezone.now()
        }
    )
    
    return redirect('certificate-detail', certificate_id=certificate.certificate_id)

@login_required
def course_enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    
    # Check if user is already enrolled
    if UserProgress.objects.filter(user=request.user, course=course).exists():
        messages.info(request, _("Вы уже записаны на этот курс."))
    else:
        # Create progress record
        UserProgress.objects.create(user=request.user, course=course)
        messages.success(request, _("Вы успешно записались на курс."))
    
    return redirect('course-detail', pk=pk)

# Course CRUD views for template-based UI
class CourseListView(ListView):
    model = Course
    template_name = 'core/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        # Start with select_related for better performance
        queryset = Course.objects.all().select_related('author')
        
        # If user is not staff or doctor, only show published courses
        if not self.request.user.is_staff and get_user_role(self.request.user) != 'doctor':
            queryset = queryset.filter(is_published=True)
        
        # Filter by search term
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filter by language
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'core/course_form.html'
    success_url = reverse_lazy('dashboard')
    
    def test_func(self):
        return get_user_role(self.request.user) == 'doctor'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'core/course_form.html'
    
    def test_func(self):
        course = self.get_object()
        return self.request.user.is_staff or course.author == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('course-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    success_url = reverse_lazy('dashboard')
    
    def test_func(self):
        course = self.get_object()
        return self.request.user.is_staff or course.author == self.request.user

# Material CRUD views for template-based UI
class MaterialListView(ListView):
    model = Material
    template_name = 'core/material_list.html'
    context_object_name = 'materials'
    paginate_by = 12
    
    def get_queryset(self):
        # Start with select_related for better performance
        queryset = Material.objects.all().select_related('author', 'course').order_by('-created_at')
        
        # Only doctors who created the materials can see unpublished ones
        user_role = get_user_role(self.request.user)
        if not self.request.user.is_staff and user_role != 'doctor':
            queryset = queryset.filter(
                Q(course__isnull=True) | Q(course__is_published=True)
            )
        
        # Filter by search term
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Filter by type
        material_type = self.request.GET.get('type')
        if material_type:
            queryset = queryset.filter(material_type=material_type)
        
        # Filter by language
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(language=language)
            
        # For non-staff users, only show materials in courses they are enrolled in
        if user_role in ['student', 'parent'] and not self.request.user.is_staff:
            enrolled_courses = Course.objects.filter(user_progress__user=self.request.user)
            queryset = queryset.filter(
                Q(course__in=enrolled_courses) | Q(course__isnull=True)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class MaterialCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'core/material_form.html'
    success_url = reverse_lazy('material-list')
    
    def test_func(self):
        return get_user_role(self.request.user) == 'doctor'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # For doctors, validate file type to ensure it's text-based
        if get_user_role(self.request.user) == 'doctor':
            file = self.request.FILES.get('file')
            if file:
                # List of allowed MIME types for text documents
                allowed_types = [
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/msword',
                    'text/plain'
                ]
                
                # Check file extension as a fallback
                file_ext = os.path.splitext(file.name)[1].lower()
                allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
                
                content_type = file.content_type
                if content_type not in allowed_types and file_ext not in allowed_extensions:
                    messages.error(self.request, _("Только текстовые документы (PDF, DOCX, DOC, TXT) разрешены для загрузки врачами."))
                    return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class MaterialUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'core/material_form.html'
    
    def test_func(self):
        material = self.get_object()
        return self.request.user.is_staff or material.author == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # For doctors, validate file type to ensure it's text-based
        if get_user_role(self.request.user) == 'doctor' and 'file' in self.request.FILES:
            file = self.request.FILES.get('file')
            if file:
                # List of allowed MIME types for text documents
                allowed_types = [
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/msword',
                    'text/plain'
                ]
                
                # Check file extension as a fallback
                file_ext = os.path.splitext(file.name)[1].lower()
                allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
                
                content_type = file.content_type
                if content_type not in allowed_types and file_ext not in allowed_extensions:
                    messages.error(self.request, _("Только текстовые документы (PDF, DOCX, DOC, TXT) разрешены для загрузки врачами."))
                    return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('material-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = get_user_role(self.request.user)
        return context

class MaterialDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Material
    success_url = reverse_lazy('material-list')
    
    def test_func(self):
        material = self.get_object()
        return self.request.user.is_staff or material.author == self.request.user

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if user is enrolled in the course
    try:
        user_progress = UserProgress.objects.get(user=request.user, course=course)
    except UserProgress.DoesNotExist:
        messages.warning(request, _("Вы не записаны на этот курс. Пожалуйста, запишитесь для просмотра уроков."))
        return redirect('course-detail', course.id)
    
    # Get all steps for this lesson
    lesson_steps = list(lesson.steps.all().order_by('order'))
    total_steps = len(lesson_steps)
    
    if total_steps == 0:
        messages.warning(request, _("В данном уроке пока нет содержимого. Попробуйте позже."))
        return redirect('course-detail', course.id)
    
    # Determine current step (from query parameter or user progress)
    try:
        current_step = int(request.GET.get('step', 1))
        if current_step < 1:
            current_step = 1
        elif current_step > total_steps:
            current_step = total_steps
    except ValueError:
        current_step = 1
    
    # Load content for current step
    current_content = lesson_steps[current_step - 1]
    
    # Calculate percentage for progress bar
    current_step_percentage = (current_step / total_steps) * 100
    
    # Get course progress percentage
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = user_progress.lessons_completed.count()
    
    if total_lessons > 0:
        course_progress = (completed_lessons / total_lessons) * 100
    else:
        course_progress = 0
    
    # Check if the user has already completed this step/lesson
    lesson_steps_completed = user_progress.lesson_steps_completed or {}
    
    # Convert string keys to integers if they're stored as strings
    if isinstance(lesson_steps_completed, dict):
        lesson_steps_completed = {int(k) if isinstance(k, str) else k: v 
                                 for k, v in lesson_steps_completed.items()}
    
    # Mark current step as viewed
    if str(lesson.id) not in lesson_steps_completed:
        lesson_steps_completed[str(lesson.id)] = []
    
    if current_step not in lesson_steps_completed.get(str(lesson.id), []):
        lesson_steps_completed.setdefault(str(lesson.id), []).append(current_step)
        user_progress.lesson_steps_completed = lesson_steps_completed
        user_progress.save()
    
    # If all steps are completed, mark the lesson as completed
    if total_steps == len(lesson_steps_completed.get(str(lesson.id), [])):
        user_progress.lessons_completed.add(lesson)
    
    context = {
        'lesson': lesson,
        'lesson_steps': lesson_steps,
        'current_step': current_step,
        'current_content': current_content,
        'total_steps': total_steps,
        'current_step_percentage': current_step_percentage,
        'course_progress': round(course_progress)
    }
    
    return render(request, 'core/lesson_detail.html', context)

@login_required
@require_POST
def mark_step_completed(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        step = int(data.get('step'))
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        course = lesson.course
        
        # Get user progress
        user_progress = get_object_or_404(UserProgress, user=request.user, course=course)
        
        # Update completed steps
        lesson_steps_completed = user_progress.lesson_steps_completed or {}
        
        if str(lesson_id) not in lesson_steps_completed:
            lesson_steps_completed[str(lesson_id)] = []
        
        if step not in lesson_steps_completed[str(lesson_id)]:
            lesson_steps_completed[str(lesson_id)].append(step)
        
        user_progress.lesson_steps_completed = lesson_steps_completed
        user_progress.save()
        
        # Check if all steps are completed
        total_steps = lesson.steps.count()
        if total_steps == len(lesson_steps_completed.get(str(lesson_id), [])):
            user_progress.lessons_completed.add(lesson)
            
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def module_create(request):
    """Create a new module for a course"""
    if request.user.role != 'doctor' and not request.user.is_staff:
        messages.error(request, _("У вас нет прав для создания модулей."))
        return redirect('dashboard')
    
    # Get course ID from URL parameters
    course_id = request.GET.get('course')
    course = None
    
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        # Check if user is the author of the course
        if course.author != request.user and not request.user.is_staff:
            messages.error(request, _("Вы не являетесь автором этого курса."))
            return redirect('course-detail', course_id)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            
            # Set the course
            if not module.course and course:
                module.course = course
            
            # Check if user is the author of the course
            if module.course.author != request.user and not request.user.is_staff:
                messages.error(request, _("Вы не являетесь автором этого курса."))
                return redirect('course-detail', module.course.id)
            
            # Set module order (last in course)
            last_module = Module.objects.filter(course=module.course).order_by('-order').first()
            if last_module:
                module.order = last_module.order + 1
            else:
                module.order = 1
            
            module.save()
            messages.success(request, _("Модуль успешно создан."))
            return redirect('course-detail', module.course.id)
    else:
        initial = {}
        if course:
            initial['course'] = course
        form = ModuleForm(initial=initial)
    
    context = {
        'form': form,
        'course': course,
    }
    
    return render(request, 'core/module_form.html', context)

@login_required
def lesson_create(request):
    """Create a new lesson for a module"""
    if request.user.role != 'doctor' and not request.user.is_staff:
        messages.error(request, _("У вас нет прав для создания уроков."))
        return redirect('dashboard')
    
    # Get module/course ID from URL parameters
    module_id = request.GET.get('module')
    course_id = request.GET.get('course')
    module = None
    course = None
    
    if module_id:
        module = get_object_or_404(Module, id=module_id)
        course = module.course
        # Check if user is the author of the course
        if course.author != request.user and not request.user.is_staff:
            messages.error(request, _("Вы не являетесь автором этого курса."))
            return redirect('course-detail', course.id)
    elif course_id:
        course = get_object_or_404(Course, id=course_id)
        # Check if user is the author of the course
        if course.author != request.user and not request.user.is_staff:
            messages.error(request, _("Вы не являетесь автором этого курса."))
            return redirect('course-detail', course_id)
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        content_form = LessonContentForm(request.POST, request.FILES, prefix='content')
        
        if form.is_valid() and content_form.is_valid():
            lesson = form.save(commit=False)
            
            # Set the module
            if not lesson.module and module:
                lesson.module = module
            
            # Check if module belongs to a course authored by user
            if lesson.module.course.author != request.user and not request.user.is_staff:
                messages.error(request, _("Вы не являетесь автором этого курса."))
                return redirect('course-detail', lesson.module.course.id)
            
            # Set lesson order (last in module)
            last_lesson = Lesson.objects.filter(module=lesson.module).order_by('-order').first()
            if last_lesson:
                lesson.order = last_lesson.order + 1
            else:
                lesson.order = 1
            
            lesson.save()
            
            # Create first content step
            content = content_form.save(commit=False)
            content.lesson = lesson
            content.order = 1
            content.save()
            
            messages.success(request, _("Урок успешно создан. Вы можете добавить больше содержимого."))
            return redirect('lesson-detail', lesson.id)
    else:
        initial = {}
        if module:
            initial['module'] = module
        
        form = LessonForm(initial=initial)
        content_form = LessonContentForm(prefix='content', initial={'title': _('Введение')})
    
    context = {
        'form': form,
        'content_form': content_form,
        'module': module,
        'course': course,
    }
    
    return render(request, 'core/lesson_form.html', context)

@login_required
def lesson_content_create(request, lesson_id):
    """Add a new content step to a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    
    # Check permissions
    if course.author != request.user and not request.user.is_staff:
        messages.error(request, _("У вас нет прав для редактирования этого урока."))
        return redirect('lesson-detail', lesson_id)
    
    if request.method == 'POST':
        form = LessonContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.lesson = lesson
            
            # Set content order (last in lesson)
            last_content = LessonContent.objects.filter(lesson=lesson).order_by('-order').first()
            if last_content:
                content.order = last_content.order + 1
            else:
                content.order = 1
            
            content.save()
            messages.success(request, _("Содержимое успешно добавлено."))
            return redirect('lesson-detail', lesson_id)
    else:
        form = LessonContentForm()
    
    context = {
        'form': form,
        'lesson': lesson,
    }
    
    return render(request, 'core/lesson_content_form.html', context)

@login_required
@csrf_exempt
def update_progress(request, course_id):
    """
    API endpoint to update user's progress in a course
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
    
    try:
        course = Course.objects.get(id=course_id)
        user = request.user
        
        # Get or create user progress
        progress, created = UserProgress.objects.get_or_create(
            user=user,
            course=course
        )
        
        data = json.loads(request.body)
        
        # Update progress
        if 'completed_items' in data:
            progress.completed_items = data['completed_items']
        
        if 'last_accessed_item' in data:
            progress.last_accessed_item = data['last_accessed_item']
        
        # Calculate completion percentage
        total_items = course.total_items_count
        if total_items > 0:
            progress.completion_percentage = (progress.completed_items / total_items) * 100
            
            # Check if course is completed
            if progress.completion_percentage >= 100:
                progress.is_completed = True
                progress.completed_at = timezone.now()
        
        progress.save()
        
        return JsonResponse({
            'status': 'success',
            'progress': {
                'completed_items': progress.completed_items,
                'completion_percentage': progress.completion_percentage,
                'is_completed': progress.is_completed
            }
        })
    
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
