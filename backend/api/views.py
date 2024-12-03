from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import generics,status
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions,IsAdminUser
#from django.contrib.auth.models import CustomUser

from .models import *  #ScoreConstructo, Indicador, Constructo, CustomUser
from .serializers import * #UserSerializer, ScoreConstructoSerializer, IndicadorSerializer, ConstructoSerializer, ScoreIndicadorSerializer,ScoreIndicador
from .permissions import IsOwner
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView


""" class ValidateTokenView(APIView):
    def post(self, request):
        serializer = TokenValidationSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"detail": "Token válido."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Usar el serializer para obtener el token
        serializer = TokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            # Obtener el token
            refresh_token = serializer.validated_data['refresh']
            access_token = serializer.validated_data['access']

            # Establecer el token en la cookie (HttpOnly, Secure y SameSite)
            response = JsonResponse({"message": "Login successful"})
            response.set_cookie(
                'jwt', access_token, 
                httponly=False,  # No accesible desde JavaScript
                secure=False,  # Solo en HTTPS
                samesite= 'None',  # Impide el envío en solicitudes cruzadas
                path='/',  # Hacer la cookie accesible en todo el dominio
                
            )
            return response
        else:
            return Response({"detail": "Invalid credentials"}, status=400) """

class CreateUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    def perform_create(self, serializer):
        serializer.save()
    
class CreateTutorView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = TutorsRegistrationSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        serializer.save()
    
""" class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
     """
    
    
    
    
""" class ProfileListView(generics.ListAPIView):
    queryset = CustomUser.objects.all().select_related('user','carrera')
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    
    
class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all().select_related('user','carrera')
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]
    lookup_field = 'pk' """
    
class UserScoreConstructoListView(generics.ListAPIView):
    serializer_class = ScoreConstructoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ScoreConstructo.objects.filter(usuario__id=user_id)

class UserScoreIndicadorListView(generics.ListAPIView):
    serializer_class = IndicadorScoreSerializer
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
    serializer_class = IndicadorScoreSerializer
    permission_classes = [AllowAny] #[IsAuthenticated, DjangoModelPermissions]

class ScoreIndicadorDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScoreIndicador.objects.all().select_related('usuario','indicador')
    serializer_class = IndicadorScoreSerializer
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


""" 
class IndicadorListViews(generics.ListCreateAPIView):
    queryset = Indicador.objects.all().prefetch_related('constructos')
    serializer_class = IndicadorSerializer
    permission_classes = [AllowAny]#[IsAuthenticated, DjangoModelPermissions]



class IndicadorDetailViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = Indicador.objects.all()
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
     """

class UserRelateDataListView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRelatedDataSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions,IsOwner]

class UserRelatedDataView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRelatedDataSerializer
    permission_classes = [AllowAny]#[IsAuthenticated, DjangoModelPermissions,IsOwner]
    lookup_field = 'pk'

class CuestionarioListView(generics.ListCreateAPIView):
    queryset = Cuestionario.objects.all()
    serializer_class = CuestionarioSerializer
    permission_classes = [AllowAny]

class CuestionarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cuestionario.objects.all()
    serializer_class = CuestionarioSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'