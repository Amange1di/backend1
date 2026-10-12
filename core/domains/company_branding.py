from rest_framework.views import APIView
from rest_framework.response import Response

class CompanyLogoView(APIView):
    def get(self, request):
        return Response({'logo': None})
