from rest_framework import serializers
from django.contrib.auth.models import User,Group
from .models import * # ScoreConstructo, Constructo, Indicador, IndicadorConstructo, ScoreIndicador,Carrera,Profile
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model



#Serializadores para los modelos de la base de datos
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']    
        
User = get_user_model()
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # Especifica que el campo de autenticación es 'email'

    def validate(self, attrs):
        # Sobrescribimos el método validate para usar el email
        self.user = authenticate(
            username=attrs.get('email'),
            password=attrs.get('password')
        )

        if self.user is None or not self.user.is_active:
            raise serializers.ValidationError(_('No se pudo autenticar con las credenciales proporcionadas.'))

        return super().validate(attrs)



class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = ['cve_carrera','nombre','instituto']
        

class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instituto
        fields = ['cve_inst', 'nombre_completo', 'tipo', 'ruta']

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['cve_depto', 'nombre', 'jefe']

class CuestionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuestionario
        fields = ['cve_cuestionario', 'nombre_corto', 'nombre_largo', 'observaciones']

class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = ['cve_pregunta', 'texto_pregunta', 'cuestionario', 'cve_const1', 'cve_const2', 'cve_const3', 'cve_const4']

class TipoRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoRespuesta
        fields = ['cve_respuesta', 'descripcion']

class DatosAplicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosAplicacion
        fields = ['cve_aplic', 'fecha', 'hora', 'cuestionario', 'observaciones']

class RespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['id_resp', 'pregunta', 'cve_aplic', 'user', 'valor']

class ScoreAplicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreAplicacion
        fields = ['cve_score', 'cve_aplic', 'user', 'total']

class RetroChatGPTSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetroChatGPT
        fields = ['cve_retro', 'cve_score', 'texto1', 'texto2', 'texto3']

class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['cve_reporte', 'cve_aplic', 'user', 'total', 'fecha', 'hora', 'texto', 'observaciones']
        
        
        
        
#Serializadores compuestos para multiples consultas
class CarreraDetailSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer()
    instituto = InstitutoSerializer()
    
    class Meta:
        model = Carrera
        fields = ['cve_carrera','nombre','departamento','instituto']


class CuestionarioDetailSerializer(serializers.ModelSerializer):
    preguntas = PreguntaSerializer(source='pregunta_set', many=True)
    
    class Meta:
        model = Cuestionario
        fields = ['cve_cuestionario', 'nombre_corto', 'nombre_largo', 'observaciones', 'preguntas']
        


class ProfileSerializer(serializers.ModelSerializer):
    
    user = UserSerializer()
    carrera = CarreraSerializer()
    
    class Meta:
        model = Profile
        fields = ['id','user','carrera','nombre']


class ConstructoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constructo
        fields = ['cve_const','descripcion', 'signo', 'acronimo']

class ScoreConstructoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer()
    constructo = ConstructoSerializer()

    class Meta:
        model = ScoreConstructo
        fields = ['cve_scoreConstructo','aplicacion', 'usuario', 'constructo', 'score']
        
class IndicadorConstructoSerializer(serializers.ModelSerializer):
    constructo = ConstructoSerializer()
    score = serializers.SerializerMethodField()

    class Meta:
        model = IndicadorConstructo
        fields = ['constructo', 'score']

    def get_score(self, obj):
        score_constructo = ScoreConstructo.objects.filter(constructo=obj.constructo).first()
        return score_constructo.score if score_constructo else None


class IndicadorSerializer(serializers.ModelSerializer):
    constructos = IndicadorConstructoSerializer(source='indicadorconstructo_set', many=True)

    class Meta:
        model = Indicador
        fields = ['nombre', 'constructos']

class ScoreIndicadorSerializer(serializers.ModelSerializer):
    usuario = UserSerializer()
    indicador = IndicadorSerializer()

    class Meta:
        model = ScoreIndicador
        fields = ['cve_ScoreIndicador', 'aplicacion', 'usuario', 'indicador', 'score']

class TutorsRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2'] #modificar el email quitar  

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()

        # Asignar el usuario al grupo "Tutores"
        tutores_group, created = Group.objects.get_or_create(name='Tutores')
        user.groups.add(tutores_group)

        return user
    
class UserRegistrationSerializer(serializers.ModelSerializer):    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2','groups']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        group_name = validated_data.pop('group')
        user = User.objects.create_user(**validated_data)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return user
    


class ReporteDetailSerializer(serializers.ModelSerializer):
    aplicacion = DatosAplicacionSerializer()
    user = UserSerializer()
    
    class Meta:
        model = Reporte
        fields = ['cve_reporte', 'aplicacion', 'user', 'total', 'fecha', 'hora', 'texto', 'observaciones']
        

class UserRelatedDataSerializer(serializers.ModelSerializer):
    score_constructos = ScoreConstructoSerializer(many=True, source='scoreconstructo_set')
    score_indicadores = ScoreIndicadorSerializer(many=True, source='scoreindicador_set')
    username = serializers.CharField(source='user.username')

    class Meta:
        model = User
        fields = ['id','username', 'email', 'score_constructos', 'score_indicadores']
        
