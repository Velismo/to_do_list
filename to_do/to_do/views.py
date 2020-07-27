#views.py
from rest_framework.views import APIView
from rest_framework.response import Response

class HelloWorld(APIView):
    def get(self, request):
        return Response('HELLO WORLD from Django.')


# VIew class to register user
class Register(APIView):
    def post(self, request):
        data = request.data
        return Response(request.data)