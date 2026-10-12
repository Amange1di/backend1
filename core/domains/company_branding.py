import base64
from io import BytesIO
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from core.models import User

class CompanyLogoView(APIView):
    def get(self, request):
        if not request.user.company_id:
            raise ValidationError("company_required")
        return Response({"logo": request.user.company.logo_data or None})

    def post(self, request):
        if request.user.role not in (User.Role.COMPANY_OWNER, User.Role.COURSE_ADMIN):
            raise PermissionDenied("forbidden")
        if not request.user.company_id:
            raise ValidationError("company_required")
        upload = request.FILES.get("logo")
        if not upload or upload.size > 262144:
            raise ValidationError("logo_required_max_256kb")
        content = upload.read(262145)
        if len(content) > 262144:
            raise ValidationError("logo_too_large")
        try:
            with Image.open(BytesIO(content)) as img:
                img.verify()
            with Image.open(BytesIO(content)) as img:
                kind = img.format
                width, height = img.size
        except (OSError, ValueError):
            raise ValidationError("invalid_image")
        mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(kind)
        if not mime or width > 2000 or height > 2000:
            raise ValidationError("unsupported_image")
        company = request.user.company
        company.logo_data = "data:" + mime + ";base64," + base64.b64encode(content).decode("ascii")
        company.save(update_fields=["logo_data"])
        return Response({"logo": company.logo_data})
