from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResumeViewSet, signup, EmailTokenObtainPairView
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # ← ADD THIS
    path('signup/', signup, name='signup'),
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),

]