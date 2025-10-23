import re
from django.core.exceptions import ValidationError

def validate_email_domain(value):
    """Allow only gmail.com, yahoo.com, outlook.com, or cit.edu."""
    pattern = r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|cit\.edu)$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Email must be @gmail.com, @yahoo.com, @outlook.com, or @cit.edu."
        )

class CustomPasswordValidator:
    """Require at least 1 uppercase letter and 1 special character."""
    def validate(self, password, user=None):
        pattern = r'^(?=.*[A-Z])(?=.*[!@#$%^&*()_+{}\[\]:;<>,.?~\-]).+$'
        if not re.match(pattern, password):
            raise ValidationError(
                "Password must contain at least 1 uppercase letter and 1 special character."
            )

    def get_help_text(self):
        return "Your password must contain at least 1 uppercase letter and 1 special character."
