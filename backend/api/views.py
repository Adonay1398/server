from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer,ScoreConstructoSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny,DjangoModelPermissions, IsAdminUser
from .models import ScoreConstructo




# Create your views here.
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,IsAdminUser)
    
    def perform_create(self, serializer):
        serializer.save()
    
class RegisterTutorView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    
class ScoreConstructoListViews(generics.ListCreateAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,DjangoModelPermissions,)
    
class ScoreConstructoDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,DjangoModelPermissions,)
class ScoreIndicadoreListViews(generics.ListCreateAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,DjangoModelPermissions,)
    
class ScoreIndicadoreDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,DjangoModelPermissions,)
