from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)
router.register(r'materials', views.MaterialViewSet)
router.register(r'tests', views.TestViewSet)
router.register(r'certificates', views.CertificateViewSet, basename='certificate')
router.register(r'users', views.CustomUserViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    path('api/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/login/', views.CustomLoginView.as_view(), name='api-login'),
    path('api/logout/', views.CustomLogoutView.as_view(), name='api-logout'),
    path('api/profile/', views.ProfileView.as_view(), name='api-profile'),
    path('api/comments/', views.CommentListView.as_view(), name='comment-list'),
    path('api/comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
    path('api/courses/<int:course_id>/progress/', views.UserProgressView.as_view(), name='user-progress'),
    
    # Comment URLs
    path('comments/create/', views.comment_create, name='comment-create'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment-delete'),
    
    # Template views
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='user-profile'),
    
    # Course URLs
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/', views.course_detail, name='course-detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('courses/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course-update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course-delete'),
    path('courses/<int:pk>/enroll/', views.course_enroll, name='course-enroll'),
    
    # Material URLs
    path('materials/', views.MaterialListView.as_view(), name='material-list'),
    path('materials/<int:pk>/', views.material_detail, name='material-detail'),
    path('materials/create/', views.MaterialCreateView.as_view(), name='material-create'),
    path('materials/<int:pk>/update/', views.MaterialUpdateView.as_view(), name='material-update'),
    path('materials/<int:pk>/delete/', views.MaterialDeleteView.as_view(), name='material-delete'),
    
    # Other URLs
    path('tests/<int:pk>/', views.test_detail, name='test-detail'),
    path('certificates/', views.certificate_list, name='certificate-list'),
    path('certificates/<str:certificate_id>/', views.certificate_detail, name='certificate-detail'),
] 