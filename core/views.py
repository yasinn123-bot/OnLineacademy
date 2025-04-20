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
    Certificate, UserProgress
)
from .serializers import (
    CustomUserSerializer, CourseSerializer, MaterialSerializer,
    CommentSerializer, TestSerializer, QuestionSerializer, 
    AnswerSerializer, CertificateSerializer, UserProgressSerializer,
    RegisterSerializer, LoginSerializer
)
from .forms import CourseForm, MaterialForm

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
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        # Admins and content creators see all
        if user.is_staff or Material.objects.filter(author=user).exists():
            return Material.objects.all()
        # Filter by language or course if specified
        queryset = Material.objects.filter(
            Q(course__is_published=True) | Q(course__isnull=True)
        )
        
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
    user_role = get_user_role(user)
    
    # Cache key specific to this user
    cache_key = f'dashboard_{user.id}'
    cached_context = cache.get(cache_key)
    
    if cached_context:
        return render(request, 'core/dashboard.html', cached_context)
    
    # Different dashboard content based on role
    if user_role == 'doctor':
        # For doctors: show their created courses and materials
        # Only fetch what's visible on the dashboard
        courses_count = Course.objects.filter(author=user).count()
        
        if courses_count > 0:
            # Only if there are courses, fetch the details with optimization
            context = {
                'created_courses': Course.objects.filter(author=user).select_related('author'),
                'created_materials': Material.objects.filter(author=user).select_related('course'),
                'courses_count': courses_count,
                'user_role': user_role,
            }
        else:
            # Don't waste resources fetching materials if no courses
            context = {
                'created_courses': [],
                'courses_count': 0, 
                'user_role': user_role,
            }
    elif user_role == 'student' or user_role == 'parent':
        # For students/parents: show their enrolled courses and progress
        enrolled_courses = Course.objects.filter(user_progress__user=user).select_related('author')
        
        # If user is enrolled in courses, fetch progress details
        if enrolled_courses.exists():
            progress_data = UserProgress.objects.filter(user=user).select_related('course').prefetch_related(
                Prefetch('materials_completed', queryset=Material.objects.select_related('author')),
                Prefetch('tests_completed', queryset=Test.objects.select_related('course'))
            )
            certificates = Certificate.objects.filter(user=user).select_related('course')
            
            context = {
                'enrolled_courses': enrolled_courses,
                'progress_data': progress_data,
                'certificates': certificates,
                'user_role': user_role,
            }
        else:
            # Don't waste resources fetching progress if not enrolled
            context = {
                'enrolled_courses': [],
                'user_role': user_role,
            }
    else:
        # Fallback for any other role
        context = {
            'user_role': user_role,
        }
    
    # Cache for 5 minutes
    cache.set(cache_key, context, 60 * 5)
    
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
    
    if request.user.is_authenticated:
        user_progress = UserProgress.objects.filter(
            user=request.user, course=course
        ).prefetch_related('materials_completed', 'tests_completed').first()
        is_enrolled = user_progress is not None
    
    context = {
        'course': course,
        'materials': Material.objects.filter(course=course).select_related('author'),
        'tests': Test.objects.filter(course=course).prefetch_related('questions'),
        'is_enrolled': is_enrolled,
        'user_progress': user_progress,
        'user_role': user_role,
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
        queryset = Material.objects.all().select_related('author', 'course')
        
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
