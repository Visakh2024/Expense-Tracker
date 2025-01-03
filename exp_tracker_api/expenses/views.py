from rest_framework import viewsets, generics
from .models import Expense, Profile
from .serializers import ExpenseSerializer, UserSerializer, ProfileSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework.parsers import MultiPartParser, FormParser


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    queryset = Expense.objects.none()

    def get_queryset(self):
        # Return only expenses of the logged-in user
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user
        serializer.save(user=self.request.user)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid Credentials'}, status=400)


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Enables file upload handling

    def get_object(self):
        try:
            return self.get_queryset().get(user=self.request.user)
        except Profile.DoesNotExist:
            raise Http404("Profile not found")

    def update(self, request, *args, **kwargs):
        profile = self.get_object()

        # Create a mutable copy of the request data
        data = request.data.copy()

        # Check if a new profile picture is provided, if not, retain the existing one
        if 'profile_picture' not in request.FILES:
            # If no new file is uploaded, use the existing profile picture
            data['profile_picture'] = profile.profile_picture

        # Proceed with the update as normal
        serializer = self.get_serializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)