from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResumeViewSet,
    signup,
    EmailTokenObtainPairView,
    confirm_manual_payment,
    deduct_credits,
    rephrase_with_ai
)
from rest_framework_simplejwt.views import TokenRefreshView

# The router automatically creates the URLs for the Resume CRUD operations
router = DefaultRouter()
router.register(r'resumes', ResumeViewSet, basename='resume')

# Define all the API endpoints for the application
urlpatterns = [
    # Router URLs for Resume CRUD
    path('', include(router.urls)),

    # Authentication URLs
    path('signup/', signup, name='signup'),
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # New Credit System URLs
    path('manual-payment-confirm/', confirm_manual_payment, name='manual_payment_confirm'),
    path('deduct-credits/', deduct_credits, name='deduct_credits'),

    # AI Feature URL
    path('rephrase/', rephrase_with_ai, name='rephrase_ai'),
]