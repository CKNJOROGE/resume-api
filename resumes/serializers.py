from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser
from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    # expose the new JSONField so that clients can PATCH it
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
        # if your JSON stores experiences under key "experience"
        for exp in value.get('experience', []):
            exp.setdefault('settings', default.copy())
        return value

    class Meta:
        model = Resume
        fields = ['id', 'user', 'title', 'template', 'data', 'hidden_sections', 'profile_image', 'created', 'updated']
        read_only_fields = ['user']

    def create(self, validated_data):
        # Always seed a full layout with ALL known sections on CREATE
        validated_data['data'] = self._ensure_default_data_on_create(validated_data.get('data', {}))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # On update, merge in defaults but respect an existing two-column layout if present
        data = validated_data.get('data', {})
        validated_data['data'] = self._ensure_default_data_on_update(data)
        return super().update(instance, validated_data)

    def _ensure_default_data_on_create(self, data):
        """
        On CREATE, completely ignore any incoming data['layout'] and assign
        a two-column default containing ALL known sections. Also seed design.
        """
        known_sections = [
            'header',
            'summary',
            'experience',
            'education',
            'skills',
            'projects',
            'courses',
            'achievements',
            'languages',
            'references',
            'passions',
            'hobbies',
            'myTime',
            'industrialExpertise',
            'awards',
            'keyAchievements',
            'professionalStrengths',
            'books',
            'volunteering',
            'additionalExperience',
            
        ]

        # Build a full two-column layout with every key
        half = (len(known_sections) + 1) // 2
        layout_obj = {
            'left': known_sections[:half],
            'right': known_sections[half:],
        }

        # hiddenSections defaults to empty list
        hidden = []

        # visibleSections defaults to true for all
        visible = {section: True for section in known_sections}

        # design defaults (always present)
        design_complete = {
            'font': 'Rubik',
            'fontSize': 3,
            'lineHeight': 1.6,
            'margin': 1,
            'spacing': 1.5,
            'titleColor': '#000000',
            'subtitleColor': '#444444',
        }

        # Merge back anything else the client sent (e.g. header text)
        merged = {**data}

        if 'header' not in merged:
            merged['header'] = {}
        if 'link' not in merged['header']:
            merged['header']['link'] = 'linkedin'


        merged.update({
            'layout': layout_obj,
            'hiddenSections': hidden,
            'visibleSections': visible,
            'design': design_complete,
        })
        return merged

    def _ensure_default_data_on_update(self, data):
        """
        On UPDATE, if client provided a valid two-column layout, keep it.
        Otherwise, fill in missing layout keys with defaults, and always ensure
        design + visibleSections exist.
        """
        known_sections = [
            'header',
            'summary',
            'experience',
            'education',
            'skills',
            'projects',
            'courses',
            'achievements',
            'languages',
            'references',
            'passions',
            'hobbies',
            'myTime',
            'industrialExpertise',
            'awards',
            'keyAchievements',
            'professionalStrengths',
            'books',
            'volunteering',
            'additionalExperience',
        ]

        incoming_layout = data.get('layout')
        if isinstance(incoming_layout, dict) and \
           isinstance(incoming_layout.get('left'), list) and \
           isinstance(incoming_layout.get('right'), list):
            layout_obj = {
                'left': list(incoming_layout['left']),
                'right': list(incoming_layout['right']),
            }
        else:
            # Build a full default if the existing layout is invalid
            half = (len(known_sections) + 1) // 2
            layout_obj = {
                'left': known_sections[:half],
                'right': known_sections[half:],
            }

        hidden = data.get('hiddenSections')
        if not isinstance(hidden, list):
            hidden = []

        visible = {section: (section not in hidden) for section in known_sections}
        client_vis = data.get('visibleSections')
        if isinstance(client_vis, dict):
            for k, v in client_vis.items():
                if k in visible and isinstance(v, bool):
                    visible[k] = v

        design = data.get('design', {})
        if not isinstance(design, dict):
            design = {}
        design_complete = {
            'font': design.get('font', 'Rubik'),
            'fontSize': design.get('fontSize', 3),
            'lineHeight': design.get('lineHeight', 1.6),
            'margin': design.get('margin', 1),
            'spacing': design.get('spacing', 1.5),
            'titleColor': design.get('titleColor', '#000000'),
            'subtitleColor': design.get('subtitleColor', '#444444'),
        }

        merged = {**data}
        merged.update({
            'layout': layout_obj,
            'hiddenSections': hidden,
            'visibleSections': visible,
            'design': design_complete,
        })
        return merged

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        attrs["username"] = user.email  # Needed for JWT logic

        # Call parent to get token data
        data = super().validate(attrs)

        # ✅ Add premium status to response
        data["premium"] = user.premium

        return data
