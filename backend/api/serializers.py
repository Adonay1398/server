from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile, Instituto, Departamento, Carrera, Cuestionario, Constructo, ScoreConstructo, ScoreIndicador

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True,}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ScoreConstructoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer()
    contructo = serializers.StringRelatedField()
    
    class Meta:
        model = ScoreConstructo
        fields = ['aplicacion', 'usuario', 'constructo', 'score']
        
class ScoreIndicadorSerializaer(serializers.ModelSerializer):
    usuario = UserSerializer()
    indicador = serializers.StringRelatedField()
    
    class Meta:
        model = ScoreIndicador
        fields = ['aplicacion', 'usuario', 'indicador', 'score']
        

class IdicadorSerializar():
    class Meta:
        model = Indicador
        fields = ['nombre', 'constructos']
        
class ConstructoSerializer(serializers.ModelSerializer):
    indicadores = IdicadorSerializar(many=True)
    
    class Meta:
        model = Constructo
        fields = [ 'indicadores']
        
