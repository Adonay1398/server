from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer,ScoreConstructoSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import ScoreConstructo




# Create your views here.
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    
class ScoreCosntructoListViews(generics.ListCreateAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,)
    
class ScoreCosntructoDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,)
class ScoreIndicadoreListViews(generics.ListCreateAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,)
    
class ScoreIndicadoreDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreConstructo.objects.all()
    serializer_class = ScoreConstructoSerializer
    permission_classes = (IsAuthenticated,)