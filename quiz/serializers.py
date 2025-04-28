from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']
        extra_kwargs = {'is_correct': {'write_only': True}}  # Hide correct answers in API responses

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'explanation', 'image', 'order', 'choices']
        extra_kwargs = {'explanation': {'write_only': True}}  # Hide explanation initially

class ChoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']

class QuestionCreateSerializer(serializers.ModelSerializer):
    choices = ChoiceCreateSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'explanation', 'image', 'order', 'choices']
    
    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data)
        
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        
        return question
    
    def update(self, instance, validated_data):
        choices_data = validated_data.pop('choices', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if choices_data is not None:
            # Clear existing choices and create new ones
            instance.choices.all().delete()
            for choice_data in choices_data:
                Choice.objects.create(question=instance, **choice_data)
        
        return instance

class QuizListSerializer(serializers.ModelSerializer):
    total_questions = serializers.IntegerField(read_only=True)
    author_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'course', 'course_title', 'author', 'author_name', 
                 'time_limit', 'passing_score', 'is_published', 'total_questions', 'created_at']
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
    
    def get_course_title(self, obj):
        if obj.course:
            return obj.course.title
        return None

class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    author_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'course', 'course_title', 'author', 'author_name', 
                 'time_limit', 'passing_score', 'is_published', 'questions', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
    
    def get_course_title(self, obj):
        if obj.course:
            return obj.course.title
        return None

class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    questions = QuestionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'course', 'author', 'time_limit', 
                 'passing_score', 'is_published', 'questions']
    
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        quiz = Quiz.objects.create(**validated_data)
        
        for question_data in questions_data:
            choices_data = question_data.pop('choices', [])
            question = Question.objects.create(quiz=quiz, **question_data)
            
            for choice_data in choices_data:
                Choice.objects.create(question=question, **choice_data)
        
        return quiz
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if questions_data is not None:
            # Handle questions update if provided
            instance.questions.all().delete()  # Clear existing questions
            
            for question_data in questions_data:
                choices_data = question_data.pop('choices', [])
                question = Question.objects.create(quiz=instance, **question_data)
                
                for choice_data in choices_data:
                    Choice.objects.create(question=question, **choice_data)
        
        return instance

class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.SerializerMethodField()
    selected_choice_texts = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentAnswer
        fields = ['id', 'question', 'question_text', 'selected_choices', 'selected_choice_texts', 
                 'text_answer', 'is_correct', 'points_earned', 'created_at']
    
    def get_question_text(self, obj):
        return obj.question.text
    
    def get_selected_choice_texts(self, obj):
        return [choice.text for choice in obj.selected_choices.all()]

class QuizAttemptListSerializer(serializers.ModelSerializer):
    quiz_title = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    score_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'user', 'user_name', 'started_at', 
                 'completed_at', 'score', 'score_percentage', 'passed']
    
    def get_quiz_title(self, obj):
        return obj.quiz.title
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class QuizAttemptDetailSerializer(serializers.ModelSerializer):
    quiz_title = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    answers = StudentAnswerSerializer(many=True, read_only=True)
    score_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'user', 'user_name', 'started_at', 
                 'completed_at', 'score', 'score_percentage', 'passed', 'answers']
    
    def get_quiz_title(self, obj):
        return obj.quiz.title
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" 