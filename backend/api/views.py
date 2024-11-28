from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions,IsAdminUser
from django.contrib.auth.models import User
from .models import ScoreConstructo, Indicador, Constructo
from .serializers import * #UserSerializer, ScoreConstructoSerializer, IndicadorSerializer, ConstructoSerializer, ScoreIndicadorSerializer,ScoreIndicador
from .permissions import IsOwner

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    def perform_create(self, serializer):
        serializer.save()
    
class CreateTutorView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = TutorsRegistrationSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        serializer.save()
    
""" class ProfileListView(generics.ListAPIView):
    queryset = Profile.objects.all().select_related('user','carrera')
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    
    
class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all().select_related('user','carrera')
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    lookup_field = 'pk'
     """
class UserScoreConstructoListView(generics.ListAPIView):
    serializer_class = ScoreConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ScoreConstructo.objects.filter(usuario__id=user_id)

class UserScoreIndicadorListView(generics.ListAPIView):
    serializer_class = ScoreIndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ScoreIndicador.objects.filter(usuario__id=user_id)
    
    
""" class RegisterTutorView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
     """
     
     
class ScoreConstructoListViews(generics.ListCreateAPIView):
    queryset = ScoreConstructo.objects.all().select_related('usuario','constructo')
    serializer_class = ScoreConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


    
class ScoreConstructoDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreConstructo.objects.all().select_related('usuario','constructo')
    serializer_class = ScoreConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    lookup_field = 'pk'

class ScoreIndicadorListViews(generics.ListCreateAPIView):
    queryset = ScoreIndicador.objects.all().select_related('usuario','indicador')
    serializer_class = ScoreIndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class ScoreIndicadorDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreIndicador.objects.all().select_related('usuario','indicador')
    serializer_class = ScoreIndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    lookup_field = 'pk' 

class ConstructoListViews(generics.ListCreateAPIView):
    queryset = Constructo.objects.all()
    serializer_class = ConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class ConstructoDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = Constructo.objects.all()
    serializer_class = ConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]



class IndicadorListViews(generics.ListCreateAPIView):
    queryset = Indicador.objects.all().prefetch_related('constructo')
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]



class IndicadorDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = Indicador.objects.all()
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    

class UserRelateDataListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRelatedDataSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]

class UserRelatedDataView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserRelatedDataSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    lookup_field = 'pk'