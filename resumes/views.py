# resume-api/resumes/views.py
import os 
import time
import google.generativeai as genai

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, ResumeSerializer
from .models import CustomUser, Resume, PendingPayment

class ResumeViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD for resumes.
    """
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-created')

    def perform_create(self, serializer):
        # Cleaned up version without debug prints
        data = self.request.data.get("data", {})
        serializer.save(user=self.request.user, data=data)


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
def confirm_manual_payment(request):
    """
    Receives a transaction ID, logs it, and adds credits on trust after a delay.
    """
    transaction_id = request.data.get("transaction_id")
    if not transaction_id:
        return Response({"error": "Transaction ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prevent duplicate transaction IDs from being used
    if PendingPayment.objects.filter(transaction_id=transaction_id).exists():
        return Response({"error": "This transaction ID has already been used."}, status=status.HTTP_400_BAD_REQUEST)

    # Log the payment attempt for admin verification
    PendingPayment.objects.create(
        user=request.user,
        transaction_id=transaction_id,
        amount=500,
        status='pending'
    )
    
    # Simulate processing delay as requested
    time.sleep(10)

    # Add credits to the user's account on trust
    user = request.user
    user.credits += 500
    user.save()

    return Response({
        "message": "Payment confirmation received. Credits have been added.",
        "new_credits": user.credits
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deduct_credits(request):
    """
    Deducts a specified amount of credits from the user's account.
    """
    user = request.user
    amount_to_deduct = request.data.get("amount", 100)

    if user.credits < amount_to_deduct:
        return Response({"error": "Insufficient credits."}, status=status.HTTP_400_BAD_REQUEST)

    user.credits -= amount_to_deduct
    user.save()

    return Response({
        "message": "Credits deducted successfully.",
        "new_credits": user.credits
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def rephrase_with_ai(request):
    """
    Accepts text and returns an AI-powered rephrased version for a resume.
    """
    text_to_rephrase = request.data.get("text")
    if not text_to_rephrase:
        return Response({"error": "Text to rephrase is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
             return Response({"error": "AI API key is not configured on the server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""You are a professional resume writer. Rephrase the following text to be more impactful and achievement-oriented for a resume. Use strong action verbs and quantifiable results where possible. Do not add any introductory text, quotation marks, or labels like "Suggestion:". Just provide the rephrased sentence directly. Text to rephrase: "{text_to_rephrase}" """
        
        response = model.generate_content(prompt)
        suggestion = response.text.strip()

        return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error during AI rephrasing: {e}")
        return Response({"error": "Failed to generate AI suggestion due to a server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
