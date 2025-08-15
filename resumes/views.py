# resume-api/resumes/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from .models import CustomUser
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import Resume
from .serializers import ResumeSerializer


class ResumeViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD for resumes.
    """
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-created')

    # In resumes/views.py, inside the ResumeViewSet class

    def perform_create(self, serializer):
        print("--- A: NEW RESUME REQUEST RECEIVED ---")
        
        # This will show us the entire raw request body from the frontend
        print("--- B: FULL REQUEST BODY ---")
        print(self.request.data)
        
        # This will show us the 'data' object we are trying to extract
        data = self.request.data.get("data", {})
        print("--- C: EXTRACTED 'data' OBJECT ---")
        print(data)
        
        # We save the instance and then immediately print what was saved to the database
        instance = serializer.save(user=self.request.user, data=data)
        print("--- D: DATA SAVED TO DATABASE ---")
        print(instance.data)
        
        print("--- E: REQUEST FINISHED ---")


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not email or not password:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    if CustomUser.objects.filter(email=email).exists():
        return Response({"error": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    CustomUser.objects.create_user(username=username, email=email, password=password)
    return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    user = request.user
    user.premium = True
    user.save()
    return Response({"message": "Payment confirmed. Account upgraded to premium."}, status=status.HTTP_200_OK)