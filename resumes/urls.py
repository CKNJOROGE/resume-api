from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResumeViewSet, signup, EmailTokenObtainPairView, confirm_payment, initiate_mpesa_payment, mpesa_callback, rephrase_with_ai  
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # ← ADD THIS
    path('signup/', signup, name='signup'),
    path('rephrase/', rephrase_with_ai, name='rephrase-with-ai'),
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('initiate-mpesa/', initiate_mpesa_payment, name='initiate_mpesa'),
    path('mpesa-callback/', mpesa_callback, name='mpesa_callback'),

]