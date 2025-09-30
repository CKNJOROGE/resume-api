# resume-api/resumes/serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser
from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    hidden_sections = serializers.JSONField(required=False)
    
    def validate_data(self, value):
        """
        Ensure each experience entry has a 'settings' dict,
        defaulting all fields to True if missing.
        """
        default = {
            'title': True,
            'company': True,
            'dates': True,
            'location': True,
            'description': True,
            'bullets': True,
        }
        for exp in value.get('experience', []):
            exp.setdefault('settings', default.copy())
        return value

    class Meta:
        model = Resume
        fields = ['id', 'user', 'title', 'template', 'data', 'hidden_sections', 'profile_image', 'created', 'updated']
        read_only_fields = ['user']

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")
            
        attrs["username"] = user.email

        data = super().validate(attrs)
        
        # Replace 'premium' with 'credits' in the login response
        data["credits"] = user.credits

        return data