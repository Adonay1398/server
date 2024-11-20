from django.contrib.auth.models import User,Group
from rest_framework import serializers
from .models import Profile, Instituto, Departamento, Carrera, Cuestionario, Constructo, ScoreConstructo, ScoreIndicador,Indicador


#el admin registra usuarios como  jefe de departamento, etc.

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password','groups']
        extra_kwargs = {'password': {'write_only': True,}}
    
    def create(self, validated_data):
        group_name = validated_data.pop('group')
        user = User.objects.create_user(**validated_data)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return user
    
class TutorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True,}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        group = Group.objects.get(name='Tutores')
        user.groups.add(group)
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
        

class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicador
        fields = ['nombre', 'constructos']
        
class ConstructoSerializer(serializers.ModelSerializer):
    indicadores = IndicadorSerializer(many=True)
    
    class Meta:
        model = Constructo
        fields = [ 'indicadores']
        
        
        
