from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Q, Prefetch
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.urls import reverse

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer
from .serializers import (
    QuizListSerializer, QuizDetailSerializer, QuizCreateUpdateSerializer,
    QuestionCreateSerializer, QuestionSerializer, ChoiceSerializer,
    QuizAttemptListSerializer, QuizAttemptDetailSerializer, StudentAnswerSerializer
)
from core.models import Course, CustomUser
from .forms import QuizForm, QuestionForm

# API Viewsets
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().select_related('course', 'module')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return QuizCreateUpdateSerializer
        else:
            return QuizDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # If staff user, return all quizzes
        if user.is_staff:
            return Quiz.objects.all().select_related('course', 'module')
        
        # If teacher/doctor, return published quizzes + quizzes for their courses
        if user.role == 'doctor':
            return Quiz.objects.filter(
                Q(is_published=True) |
                Q(course__author=user)
            ).select_related('course', 'module')
        
        # For students, only return published quizzes
        return Quiz.objects.filter(
            is_published=True
        ).select_related('course', 'module')
    
    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        
        # Check if there's an incomplete attempt
        existing_incomplete = QuizAttempt.objects.filter(
            quiz=quiz, 
            user=user, 
            end_time__isnull=True
        ).first()
        
        if existing_incomplete:
            serializer = QuizAttemptDetailSerializer(existing_incomplete)
            return Response(serializer.data)
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=user
        )
        
        serializer = QuizAttemptDetailSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        
        # Admin can see all attempts, users can only see their own
        if user.is_staff:
            attempts = QuizAttempt.objects.filter(quiz=quiz)
        else:
            attempts = QuizAttempt.objects.filter(quiz=quiz, user=user)
        
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)

class QuizAttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return QuizAttempt.objects.all()
        return QuizAttempt.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        # This endpoint is not directly accessible, use start_attempt on quiz
        return Response(
            {"detail": _("Please use the /quizzes/{id}/start_attempt/ endpoint")}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        attempt = self.get_object()
        user = request.user
        
        # Verify this attempt belongs to the user
        if attempt.user != user:
            return Response(
                {"detail": _("This attempt does not belong to you")}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify attempt is not already completed
        if attempt.end_time is not None:
            return Response(
                {"detail": _("This attempt is already completed")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get question and answer data
        question_id = request.data.get('question_id')
        selected_choice_ids = request.data.get('selected_choice_ids', [])
        text_answer = request.data.get('text_answer')
        
        # Validate question belongs to quiz
        try:
            question = Question.objects.get(id=question_id, quiz=attempt.quiz)
        except Question.DoesNotExist:
            return Response(
                {"detail": _("Question not found or does not belong to this quiz")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if question was already answered
        if StudentAnswer.objects.filter(attempt=attempt, question=question).exists():
            return Response(
                {"detail": _("This question was already answered")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the answer
        with transaction.atomic():
            answer = StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                text_answer=text_answer
            )
            
            # For choice-based questions
            if question.question_type in ['single', 'multiple', 'true_false']:
                # Get choices and add them to the answer
                valid_choices = Choice.objects.filter(
                    id__in=selected_choice_ids,
                    question=question
                )
                answer.selected_choices.set(valid_choices)
                
                # Calculate if answer is correct
                if question.question_type == 'single' or question.question_type == 'true_false':
                    # Single choice - correct if the one selected choice is correct
                    if valid_choices.count() == 1 and valid_choices.first().is_correct:
                        answer.is_correct = True
                        answer.points_earned = question.points
                elif question.question_type == 'multiple':
                    # Multiple choice - all correct choices must be selected and no incorrect ones
                    all_choices = Choice.objects.filter(question=question)
                    correct_choices = all_choices.filter(is_correct=True)
                    
                    # Get sets of IDs for comparison
                    selected_ids = set(valid_choices.values_list('id', flat=True))
                    correct_ids = set(correct_choices.values_list('id', flat=True))
                    
                    if selected_ids == correct_ids:
                        answer.is_correct = True
                        answer.points_earned = question.points
            
            # For short answer questions (to be evaluated manually or by exact match)
            elif question.question_type == 'short_answer':
                # Simple exact match validation
                correct_choices = Choice.objects.filter(question=question, is_correct=True)
                
                if correct_choices.exists():
                    # Check if text answer matches any of the correct answers
                    for choice in correct_choices:
                        if text_answer and text_answer.lower().strip() == choice.text.lower().strip():
                            answer.is_correct = True
                            answer.points_earned = question.points
                            break
            
            answer.save()
        
        # Check if all questions have been answered
        total_questions = attempt.quiz.questions.count()
        answered_questions = StudentAnswer.objects.filter(attempt=attempt).count()
        
        if answered_questions >= total_questions:
            # Complete the attempt
            total_points = StudentAnswer.objects.filter(attempt=attempt).aggregate(
                total=Sum('points_earned')
            )['total'] or 0
            
            attempt.score = total_points
            attempt.end_time = timezone.now()
            
            # Check if passed
            max_points = attempt.quiz.total_points
            if max_points > 0:
                percentage = (total_points / max_points) * 100
                attempt.is_completed = True
            
            attempt.save()
        
        serializer = StudentAnswerSerializer(answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        attempt = self.get_object()
        user = request.user
        
        # Verify this attempt belongs to the user
        if attempt.user != user:
            return Response(
                {"detail": _("This attempt does not belong to you")}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify attempt is not already completed
        if attempt.end_time is not None:
            return Response(
                {"detail": _("This attempt is already completed")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Complete the attempt
        with transaction.atomic():
            total_points = StudentAnswer.objects.filter(attempt=attempt).aggregate(
                total=Sum('points_earned')
            )['total'] or 0
            
            attempt.score = total_points
            attempt.end_time = timezone.now()
            
            # Check if passed
            max_points = attempt.quiz.total_points
            if max_points > 0:
                percentage = (total_points / max_points) * 100
                attempt.is_completed = True
            
            attempt.save()
        
        serializer = self.get_serializer(attempt)
        return Response(serializer.data)

# Template Views
@login_required
def quiz_list(request):
    # Get filter parameters
    course_id = request.GET.get('course')
    user_quizzes = request.GET.get('mine') == '1'
    
    # Base queryset with optimized relationships
    base_queryset = Quiz.objects.select_related('course', 'module').prefetch_related('questions')
    
    if request.user.is_staff or request.user.role == 'doctor':
        quizzes = base_queryset
    else:
        quizzes = base_queryset.filter(is_published=True)
    
    # Apply filters
    if course_id:
        quizzes = quizzes.filter(course_id=course_id)
    
    if user_quizzes:
        quizzes = quizzes.filter(author=request.user)
    
    # Get user's attempts for these quizzes
    user_attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz__in=quizzes
    ).select_related('quiz')
    
    # Get courses for filter dropdown
    courses = Course.objects.filter(is_published=True)
    
    context = {
        'quizzes': quizzes,
        'user_attempts': {attempt.quiz_id: attempt for attempt in user_attempts},
        'courses': courses,
        'selected_course': course_id,
        'user_quizzes': user_quizzes,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/quiz_list.html', context)

@login_required
def quiz_detail(request, pk):
    # Get quiz with all related data in one query
    quiz = get_object_or_404(
        Quiz.objects.select_related('course', 'module'),
        pk=pk
    )
    
    # Check if user has permission to view quiz
    course_author = quiz.course.author if quiz.course else None
    if not quiz.is_published and not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет доступа к этому тесту"))
        return redirect('quiz:quiz_list')
    
    # Get user's attempts for this quiz with efficient prefetching
    attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    ).order_by('-start_time')
    
    # Get latest attempt
    latest_attempt = attempts.first()
    
    # Get question count in one query
    question_count = Question.objects.filter(quiz=quiz).count()
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
        'latest_attempt': latest_attempt,
        'user_role': request.user.role,
        'question_count': question_count
    }
    
    return render(request, 'quiz/quiz_detail.html', context)

@login_required
def take_quiz(request, pk):
    # Get quiz with related data
    quiz = get_object_or_404(
        Quiz.objects.select_related('course', 'module'),
        pk=pk
    )
    
    # Check if quiz is available to the user
    course_author = quiz.course.author if quiz.course else None
    if not quiz.is_published and not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет доступа к этому тесту"))
        return redirect('quiz:quiz_list')
    
    # Check if there's an incomplete attempt
    attempt = QuizAttempt.objects.filter(
        quiz=quiz,
        user=request.user,
        end_time__isnull=True
    ).first()
    
    # If no existing attempt, create one
    if not attempt:
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user
        )
    
    # If the attempt is already complete, redirect to results
    if attempt.end_time:
        return redirect('quiz:quiz_results', attempt_id=attempt.id)
    
    # Get questions and answered question IDs efficiently
    questions = list(Question.objects.filter(quiz=quiz).prefetch_related('choices').order_by('order', 'id'))
    answered_questions = list(StudentAnswer.objects.filter(
        attempt=attempt
    ).values_list('question_id', flat=True))
    
    # Get current question (first unanswered)
    current_question = None
    for question in questions:
        if question.id not in answered_questions:
            current_question = question
            break
    
    # If all questions are answered, show completion page
    if not current_question:
        return render(request, 'quiz/quiz_complete.html', {
            'quiz': quiz,
            'attempt': attempt,
            'user_role': request.user.role,
        })
    
    # Calculate progress percentage
    progress_percentage = (len(answered_questions) / len(questions)) * 100 if questions else 0
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'question': current_question,
        'question_number': [q.id for q in questions].index(current_question.id) + 1 if current_question else 0,
        'total_questions': len(questions),
        'answered_count': len(answered_questions),
        'progress_percentage': progress_percentage,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/take_quiz.html', context)

@login_required
def submit_answer(request, attempt_id):
    if request.method != 'POST':
        return JsonResponse({'error': _('Method not allowed')}, status=405)
    
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    
    # Ensure attempt is not already completed
    if attempt.end_time:
        return JsonResponse({'error': _('This attempt is already completed')}, status=400)
    
    # Get POST data
    question_id = request.POST.get('question_id')
    question = get_object_or_404(Question, pk=question_id, quiz=attempt.quiz)
    
    # Check if already answered
    if StudentAnswer.objects.filter(attempt=attempt, question=question).exists():
        return JsonResponse({'error': _('Question already answered')}, status=400)
    
    # Process the answer
    with transaction.atomic():
        answer = StudentAnswer(
            attempt=attempt,
            question=question,
            is_correct=False,
            points_earned=0
        )
        
        # Handle different question types
        if question.question_type in ['single', 'true_false']:
            choice_id = request.POST.get('choice_id')
            
            if choice_id:
                choice = get_object_or_404(Choice, pk=choice_id, question=question)
                answer.save()  # Save to get an ID before setting many-to-many
                answer.choices.add(choice)
                
                if choice.is_correct:
                    answer.is_correct = True
                    answer.points_earned = question.points
        
        elif question.question_type == 'multiple':
            choice_ids = request.POST.getlist('choice_ids')
            
            if choice_ids:
                answer.save()  # Save to get an ID before setting many-to-many
                
                selected_choices = Choice.objects.filter(id__in=choice_ids, question=question)
                answer.choices.set(selected_choices)
                
                # Check if all correct choices are selected and no incorrect ones
                all_choices = Choice.objects.filter(question=question)
                correct_choices = all_choices.filter(is_correct=True)
                
                selected_ids = set(selected_choices.values_list('id', flat=True))
                correct_ids = set(correct_choices.values_list('id', flat=True))
                
                if selected_ids == correct_ids:
                    answer.is_correct = True
                    answer.points_earned = question.points
        
        elif question.question_type == 'short_answer':
            text_answer = request.POST.get('text_answer', '').strip()
            answer.text_answer = text_answer
            
            # Check against correct answers
            correct_choices = Choice.objects.filter(question=question, is_correct=True)
            
            for choice in correct_choices:
                if text_answer.lower() == choice.text.lower().strip():
                    answer.is_correct = True
                    answer.points_earned = question.points
                    break
        
        answer.save()
        
        # Check if all questions are now answered
        total_questions = attempt.quiz.questions.count()
        answered_questions = StudentAnswer.objects.filter(attempt=attempt).count()
        
        if answered_questions >= total_questions:
            # Complete the attempt
            total_points = StudentAnswer.objects.filter(attempt=attempt).aggregate(
                total=Sum('points_earned')
            )['total'] or 0
            
            attempt.score = total_points
            attempt.end_time = timezone.now()
            
            # Check if passed
            max_points = attempt.quiz.total_points
            if max_points > 0:
                percentage = (total_points / max_points) * 100
                attempt.is_completed = True
            
            attempt.save()
    
    # Redirect to next question or results page
    if answered_questions >= total_questions:
        return redirect('quiz:quiz_results', attempt_id=attempt.id)
    else:
        return redirect('quiz:take_quiz', pk=attempt.quiz.id)

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    
    # Make sure the attempt is completed
    if not attempt.end_time:
        messages.warning(request, _("Этот тест еще не завершен"))
        return redirect('take_quiz', pk=attempt.quiz.id)
    
    # Get all answers with questions and choices
    answers = StudentAnswer.objects.filter(attempt=attempt).select_related('question')
    
    context = {
        'quiz': attempt.quiz,
        'attempt': attempt,
        'answers': answers,
        'score_percentage': attempt.score_percentage,
        'passed': attempt.is_passed,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/quiz_results.html', context)

@login_required
def create_quiz(request):
    # Only staff and doctors can create quizzes
    if not request.user.is_staff and request.user.role != 'doctor':
        messages.error(request, _("У вас нет доступа к созданию тестов"))
        return redirect('quiz:quiz_list')
    
    if request.method == 'POST':
        form = QuizForm(request.POST, user=request.user)
        if form.is_valid():
            quiz = form.save(commit=False)
            # The author is the course author, not directly the quiz author
            # Just save the quiz, don't set author directly
            quiz.save()
            messages.success(request, _("Тест успешно создан"))
            return redirect('quiz:edit_quiz', pk=quiz.pk)
    else:
        # Get course_id from query parameters
        course_id = request.GET.get('course')
        initial = {}
        if course_id:
            initial['course'] = course_id
        form = QuizForm(user=request.user, initial=initial)
    
    context = {
        'form': form,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/quiz_form.html', context)

@login_required
def edit_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related('course'), pk=pk)
    
    # Only staff or the course author can edit quizzes
    course_author = quiz.course.author if quiz.course else None
    if not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет доступа к редактированию этого теста"))
        return redirect('quiz:quiz_list')
    
    # Get courses for dropdown
    if request.user.is_staff:
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(Q(is_published=True) | Q(author=request.user))
    
    # Get questions
    questions = Question.objects.filter(quiz=quiz).prefetch_related('choices')
    
    if request.method == 'POST':
        # Process form data for quiz details
        title = request.POST.get('title')
        description = request.POST.get('description')
        course_id = request.POST.get('course')
        time_limit = request.POST.get('time_limit') or 30
        passing_score = request.POST.get('passing_score') or 70
        is_published = request.POST.get('is_published') == 'on'
        
        if not title:
            messages.error(request, _("Название теста обязательно"))
            return render(request, 'quiz/edit_quiz.html', {
                'quiz': quiz,
                'courses': courses,
                'questions': questions,
                'user_role': request.user.role,
            })
        
        # Update quiz
        quiz.title = title
        quiz.description = description
        quiz.time_limit = time_limit
        quiz.passing_score = passing_score
        quiz.is_published = is_published
        
        if course_id:
            quiz.course = get_object_or_404(Course, pk=course_id)
        else:
            quiz.course = None
        
        quiz.save()
        messages.success(request, _("Тест успешно обновлен"))
        return redirect('edit_quiz', pk=quiz.id)
    
    context = {
        'quiz': quiz,
        'courses': courses,
        'questions': questions,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/edit_quiz.html', context)

@login_required
def create_question(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    
    # Check permissions
    course_author = quiz.course.author if quiz.course else None
    if not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет прав для добавления вопросов в этот тест"))
        return redirect('quiz:quiz_detail', pk=quiz.id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(quiz=quiz)
            
            if 'save_and_add' in request.POST:
                messages.success(request, _("Вопрос успешно создан. Добавьте еще один вопрос."))
                return redirect('quiz:create_question', quiz_id=quiz.id)
            else:
                messages.success(request, _("Вопрос успешно создан"))
                return redirect('quiz:edit_quiz', pk=quiz.id)
    else:
        form = QuestionForm()
    
    context = {
        'form': form,
        'quiz': quiz,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/add_question.html', context)

@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question.objects.select_related('quiz__course'), id=question_id)
    quiz = question.quiz
    
    # Check permissions
    course_author = quiz.course.author if quiz.course else None
    if not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет прав для редактирования этого вопроса"))
        return redirect('quiz:quiz_detail', pk=quiz.id)
    
    if request.method == 'POST':
        # Process form data
        text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        points = request.POST.get('points') or 1
        explanation = request.POST.get('explanation')
        order = request.POST.get('order') or 0
        
        if not text:
            messages.error(request, _("Текст вопроса обязателен"))
            context = {
                'question': question,
                'quiz': quiz,
                'user_role': request.user.role,
            }
            return render(request, 'quiz/edit_question.html', context)
        
        # Update question
        question.text = text
        question.question_type = question_type
        question.points = points
        question.explanation = explanation
        question.order = order
        question.save()
        
        # Process choices - delete existing and create new
        question.choices.all().delete()
        
        choice_texts = request.POST.getlist('choice_text[]')
        is_correct_values = request.POST.getlist('is_correct[]')
        
        for i, choice_text in enumerate(choice_texts):
            if choice_text.strip():
                is_correct = str(i) in is_correct_values
                Choice.objects.create(
                    question=question,
                    text=choice_text,
                    is_correct=is_correct
                )
        
        messages.success(request, _("Вопрос успешно обновлен"))
        return redirect('edit_quiz', pk=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/edit_question.html', context)

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question.objects.select_related('quiz__course'), id=question_id)
    quiz = question.quiz
    
    # Check permissions
    course_author = quiz.course.author if quiz.course else None
    if not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет прав для удаления этого вопроса"))
        return redirect('quiz:quiz_detail', pk=quiz.id)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, _("Вопрос успешно удален"))
    
    return redirect('edit_quiz', pk=quiz.id)

@login_required
def delete_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related('course'), pk=pk)
    
    # Check permissions
    course_author = quiz.course.author if quiz.course else None
    if not request.user.is_staff and course_author != request.user:
        messages.error(request, _("У вас нет прав для удаления этого теста"))
        return redirect('quiz:quiz_detail', pk=pk)
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, _("Тест успешно удален"))
        return redirect('quiz_list')
    
    context = {
        'quiz': quiz,
        'user_role': request.user.role,
    }
    
    return render(request, 'quiz/delete_quiz.html', context)
