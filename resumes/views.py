# resume-api/resumes/views.py
import os 
import google.generativeai as genai

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
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64



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



def get_mpesa_access_token():
    """Request an access token from Safaricom's Daraja API."""
    consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
    consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        r = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret), timeout=10)
        r.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return r.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_mpesa_payment(request):
    """Initiate an M-Pesa Express (STK Push) to the user's phone."""
    phone_number = request.data.get("phone_number")
    amount = 1 # The amount to be paid (e.g., 1 KES for testing)

    if not phone_number:
        return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

    access_token = get_mpesa_access_token()
    if not access_token:
        return Response({"error": "Failed to get M-Pesa access token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = os.environ.get('MPESA_SHORTCODE')
    passkey = os.environ.get('MPESA_PASSKEY')

    password_str = shortcode + passkey + timestamp
    password = base64.b64encode(password_str.encode()).decode('utf-8')

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        # This MUST be a live, publicly accessible URL that Safaricom can reach.
        # Your Heroku URL is perfect for this.
        "CallBackURL": f"https://{request.get_host()}/api/mpesa-callback/",
        "AccountReference": f"user_{request.user.id}", # A reference for the transaction
        "TransactionDesc": "Payment for Resume Builder Premium"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        # In a real app, you would save response.json()['CheckoutRequestID'] to your database
        # to track the status of this specific payment attempt.
        return Response(response.json(), status=status.HTTP_200_OK)
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny]) # This endpoint must be open to receive requests from Safaricom
def mpesa_callback(request):
    """
    Handle the callback from Safaricom. This is where you confirm the payment
    and grant the user premium access.
    """
    data = request.data
    print("M-Pesa Callback Received:", data)

    # In a real application, you would:
    # 1. Parse the `data` to get the CheckoutRequestID and ResultCode.
    # 2. Find the pending transaction in your database using the CheckoutRequestID.
    # 3. If ResultCode is 0 (success), mark the transaction as complete.
    # 4. Find the user associated with the transaction and set their `premium` status to True.

    # For now, we just log the data and return a success response.
    return Response(status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([AllowAny]) # This can be public as it doesn't handle sensitive user data
def rephrase_with_ai(request):
    """
    Accepts text and returns an AI-powered rephrased version for a resume.
    """
    text_to_rephrase = request.data.get("text")
    if not text_to_rephrase:
        return Response({"error": "Text to rephrase is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        api_key = os.environ.get('GEMINI_API_KEY')

        print(f"--- DEBUG: API Key being used: '{api_key}' ---")

        if not api_key:
             return Response({"error": "AI API key is not configured on the server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""You are a professional resume writer. Rephrase the following text to be more impactful and achievement-oriented for a resume. Use strong action verbs and quantifiable results where possible. Do not add any introductory text, quotation marks, or labels like "Suggestion:". Just provide the rephrased sentence directly. Text to rephrase: "{text_to_rephrase}" """
        
        response = model.generate_content(prompt)
        suggestion = response.text.strip()

        return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error during AI rephrasing: {e}")
        return Response({"error": "Failed to generate AI suggestion due to a server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
