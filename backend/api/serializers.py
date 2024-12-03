from rest_framework import serializers
from api.models import CustomUser, Carrera, ScoreConstructo, ScoreIndicador, Constructo, Indicador, Instituto, Departamento, DatosAplicacion, Respuesta, Cuestionario, Reporte, Pregunta
from django.contrib.auth.models import Group
class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = ['cve_carrera', 'nombre', 'instituto']

class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instituto
        fields = ['cve_inst', 'nombre_completo', 'tipo', 'ruta']

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['cve_depto', 'nombre', 'jefe']

class ConstructoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constructo
        fields = ['cve_const', 'descripcion', 'acronimo']

class ScoreConstructoSerializer(serializers.ModelSerializer):
    constructo = ConstructoSerializer()

    class Meta:
        model = ScoreConstructo
        fields = ['constructo', 'score']

class IndicadorScoreSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='indicador.nombre')
    constructos = serializers.SerializerMethodField()
    usuario = serializers.CharField(source='usuario.get_full_name')
    class Meta:
        model = ScoreIndicador
        fields = ['nombre', 'constructos', 'usuario']

    def get_constructos(self, obj):
        constructos = ScoreConstructo.objects.filter(constructo__indicadorconstructo__indicador=obj.indicador, usuario=obj.usuario)
        return ScoreConstructoSerializer(constructos, many=True).data

class UserPersonalInfoSerializer(serializers.ModelSerializer):
    carrera = serializers.CharField(source='carrera.nombre')

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'fecha_nacimiento', 'email',  'carrera']

    def get_carrera(self, obj):
        return obj.carrera.nombre if obj.carrera else None

class UserRelatedDataSerializer(serializers.ModelSerializer):
    informacion_personal = UserPersonalInfoSerializer(source='*')
    score = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['informacion_personal', 'score']

    def get_score(self, obj):
        indicadores = ScoreIndicador.objects.filter(usuario=obj)
        return IndicadorScoreSerializer(indicadores, many=True).data

class DatosAplicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosAplicacion
        fields = ['cve_aplic', 'fecha', 'hora', 'cuestionario', 'observaciones']

class RespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Respuesta
        fields = ['cve_resp', 'pregunta', 'cve_aplic', 'user', 'valor']

class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = ['cve_pregunta', 'texto_pregunta', 'cuestionario', 'cve_const1', 'cve_const2', 'cve_const3', 'cve_const4', 'scorekey']

class CuestionarioSerializer(serializers.ModelSerializer):
    preguntas = PreguntaSerializer(many=True, read_only=True, source='pregunta_set')
    respuestas = RespuestaSerializer(many=True, write_only=True)

    class Meta:
        model = Cuestionario
        fields = ['cve_cuestionario', 'nombre_corto', 'preguntas', 'respuestas']

    def create(self, validated_data):
        respuestas_data = validated_data.pop('respuestas')
        cuestionario = Cuestionario.objects.create(**validated_data)
        for respuesta_data in respuestas_data:
            Respuesta.objects.create(cuestionario=cuestionario, **respuesta_data)
        return cuestionario

    def update(self, instance, validated_data):
        respuestas_data = validated_data.pop('respuestas')
        instance.nombre_corto = validated_data.get('nombre_corto', instance.nombre_corto)
        instance.save()

        for respuesta_data in respuestas_data:
            respuesta_id = respuesta_data.get('cve_resp')
            if respuesta_id:
                respuesta = Respuesta.objects.get(cve_resp=respuesta_id, cuestionario=instance)
                respuesta.valor = respuesta_data.get('valor', respuesta.valor)
                respuesta.save()
            else:
                Respuesta.objects.create(cuestionario=instance, **respuesta_data)

        return instance

class ReporteDetailSerializer(serializers.ModelSerializer):
    aplicacion = DatosAplicacionSerializer()
    user = UserPersonalInfoSerializer()

    class Meta:
        model = Reporte
        fields = ['cve_reporte', 'aplicacion', 'user', 'total', 'fecha', 'hora', 'texto', 'observaciones']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'groups']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        group_name = validated_data.pop('groups', [])
        user = CustomUser.objects.create_user(**validated_data)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return user
    
class TutorsRegistrationSerializer(serializers.ModelSerializer):
    escuela = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password2', 'fecha_nacimiento', 'carrera', 'escuela']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        # Extraer los campos necesarios
        username = validated_data['username']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        email = validated_data['email']
        fecha_nacimiento = validated_data['fecha_nacimiento']
        carrera = validated_data['carrera']
        escuela = validated_data['escuela']
        password = validated_data['password']

        # Obtener la instancia de Carrera
        carrera_instance = Carrera.objects.get(pk=carrera.pk)

        # Crear el usuario
        user = CustomUser(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            fecha_nacimiento=fecha_nacimiento,
            carrera=carrera_instance
        )
        user.set_password(password)
        user.save()

        # Asignar el usuario al grupo "Tutores"
        tutores_group, created = Group.objects.get_or_create(name='Tutores')
        user.groups.add(tutores_group)

        return user


class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = ['cve_pregunta', 'texto_pregunta', 'cuestionario', 'cve_const1', 'cve_const2', 'cve_const3', 'cve_const4', 'scorekey']