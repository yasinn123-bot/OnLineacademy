from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from .models import (
    CustomUser, Course, Material, Comment, Test, Question, Answer,
    Certificate, UserProgress
)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'role')
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(_("Passwords do not match."))
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'student')
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError(_("User account is disabled."))
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError(_("Unable to log in with provided credentials."))
        else:
            raise serializers.ValidationError(_("Must include 'username' and 'password'."))

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'profile_picture', 'bio')
        read_only_fields = ('username', 'email')

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'text', 'is_correct')
        extra_kwargs = {'is_correct': {'write_only': True}}  # Hide correct answers from users

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'points', 'answers')

class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'description', 'created_at', 'updated_at', 'course', 'passing_score', 'language', 'questions')

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.get_full_name')
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'content', 'created_at', 'updated_at', 'author', 'author_name', 'material', 'parent', 'replies')
        extra_kwargs = {'author': {'read_only': True}}
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

class MaterialSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.get_full_name')
    comments_count = serializers.SerializerMethodField()
    material_type_display = serializers.ReadOnlyField(source='get_material_type_display')
    
    class Meta:
        model = Material
        fields = ('id', 'name', 'description', 'file', 'created_at', 'updated_at', 'author', 
                 'author_name', 'course', 'material_type', 'material_type_display', 
                 'language', 'comments_count')
        extra_kwargs = {'file': {'required': True}}
    
    def get_comments_count(self, obj):
        return obj.comments.count()

class CourseSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.get_full_name')
    materials_count = serializers.SerializerMethodField()
    tests_count = serializers.SerializerMethodField()
    language_display = serializers.ReadOnlyField(source='get_language_display')
    
    class Meta:
        model = Course
        fields = ('id', 'title', 'description', 'created_at', 'updated_at', 'author', 
                 'author_name', 'is_published', 'language', 'language_display',
                 'materials_count', 'tests_count')
    
    def get_materials_count(self, obj):
        return obj.materials.count()
    
    def get_tests_count(self, obj):
        return obj.tests.count()

class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    course_title = serializers.ReadOnlyField(source='course.title')
    
    class Meta:
        model = Certificate
        fields = ('id', 'user', 'user_name', 'course', 'course_title', 'issued_at', 'certificate_id', 'score')

class UserProgressSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    course_title = serializers.ReadOnlyField(source='course.title')
    materials_completed_count = serializers.SerializerMethodField()
    tests_completed_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProgress
        fields = ('id', 'user', 'user_name', 'course', 'course_title', 'last_access',
                 'materials_completed', 'tests_completed', 'materials_completed_count', 'tests_completed_count')
    
    def get_materials_completed_count(self, obj):
        return obj.materials_completed.count()
    
    def get_tests_completed_count(self, obj):
        return obj.tests_completed.count() 