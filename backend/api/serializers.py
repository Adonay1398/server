
from datetime import date
from django.contrib.auth.models import Group
from rest_framework import serializers

from api.models import (
    CustomUser, Carrera, RetroChatGPT,  ScoreConstructo, ScoreIndicador, Constructo, Indicador,
    Instituto, Departamento, DatosAplicacion, Respuesta, Cuestionario, Pregunta,  #Reporte, 
)

#RetroChatGPT
class CarreraSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Carrera. Retorna su clave, nombre e instituto.
    """
    class Meta:
        model = Carrera
        fields = ['cve_carrera', 'nombre', 'instituto']


class CarreraDetailSerializer(serializers.ModelSerializer):
    """
    Serializador detallado de la Carrera.
    Incluye el departamento y el instituto asociados, retornando sus nombres.
    """
    departamento = serializers.SerializerMethodField()
    instituto = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = ['nombre', 'departamento', 'instituto']

    def get_departamento(self, obj):
        """Retorna el nombre del departamento asociado a la carrera."""
        return obj.departamento.nombre

    def get_instituto(self, obj):
        """Retorna el nombre completo del instituto asociado a la carrera."""
        return obj.instituto.nombre_completo


class InstitutoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Instituto, mostrando datos básicos.
    """
    class Meta:
        model = Instituto
        fields = ['cve_inst', 'nombre_completo', 'tipo', 'ruta']


class DepartamentoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Departamento, mostrando su clave, nombre y jefe.
    """
    class Meta:
        model = Departamento
        fields = ['cve_depto', 'nombre', 'jefe']


class ConstructoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Constructo, mostrando su clave, descripción y acrónimo.
    """
    class Meta:
        model = Constructo
        fields = ['cve_const', 'descripcion', 'acronimo']


class ScoreConstructoSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar los puntajes por constructo.
    Incluye el constructo asociado.
    """
    constructo = ConstructoSerializer()

    class Meta:
        model = ScoreConstructo
        fields = ['constructo', 'score']


class IndicadorScoreSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar las puntuaciones de un indicador, incluyendo
    el nombre del indicador, los constructos que lo componen y el puntaje promedio.
    """
    nombre = serializers.CharField(source='indicador.nombre')
    constructos = serializers.SerializerMethodField()
    prom_score = serializers.SerializerMethodField()

    class Meta:
        model = ScoreIndicador
        fields = ['nombre', 'constructos', 'prom_score']

    def get_constructos(self, obj):
        """Retorna el detalle de los constructos asociados al indicador y al usuario."""
        constructos = ScoreConstructo.objects.filter(
            constructo__indicadorconstructo__indicador=obj.indicador,
            usuario=obj.usuario
        )
        return ScoreConstructoSerializer(constructos, many=True).data

    def get_prom_score(self, obj):
        """Calcula el puntaje promedio del indicador sumando el score de sus constructos."""
        constructos = ScoreConstructo.objects.filter(
            constructo__indicadorconstructo__indicador=obj.indicador,
            usuario=obj.usuario
        )
        if constructos.exists():
            total_score = sum([c.score for c in constructos])
            promedio = total_score / constructos.count()
            return int(promedio)
        return 0


class UserPersonalInfoSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar información personal básica del usuario autenticado.
    Incluye nombre, apellido, fecha de nacimiento, email y carrera.
    """
    carrera = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'fecha_nacimiento', 'email', 'carrera']

    def get_carrera(self, obj):
        """
        Retorna el nombre de la carrera del usuario autenticado.
        """
        # Obtener el usuario autenticado desde el contexto
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        return obj.carrera.nombre if obj.carrera else None


class UserRelatedDataSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar datos relacionados al usuario:
    - Información personal
    - Indicadores y sus puntajes
    - Retroalimentación de RetroChatGPT
    """
    informacion_personal = UserPersonalInfoSerializer(source='*')
    indicador = serializers.SerializerMethodField()
    retrochatgpt = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['informacion_personal', 'indicador', 'retrochatgpt']

    def get_indicador(self, obj):
        """
        Retorna los indicadores con sus puntajes para el usuario dado.
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuario no autenticado.")

        user = request.user
        indicadores = ScoreIndicador.objects.filter(usuario=user)
        return IndicadorScoreSerializer(indicadores, many=True).data

    def get_retrochatgpt(self, obj):
        """
        Retorna la retroalimentación de RetroChatGPT para el usuario dado.
        """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuario no autenticado.")

        user = request.user
        retros = RetroChatGPT.objects.filter(usuario=user)
        return [
            {
                "texto1": retro.texto1 if retro.texto1 else None,
                "texto2": retro.texto2 if retro.texto2 else None,
            }
            for retro in retros
        ]

class DatosAplicacionSerializer(serializers.ModelSerializer):
    """
    Serializador para DatosAplicacion, mostrando información de la aplicación,
    fecha, hora y cuestionarios asociados.
    """
    class Meta:
        model = DatosAplicacion
        fields = ['cve_aplic', 'fecha', 'hora', 'cuestionario', 'observaciones']


class RespuestaSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Respuesta, mostrando la respuesta a una pregunta.
    """
    class Meta:
        model = Respuesta
        fields = ['cve_resp', 'pregunta', 'cve_aplic', 'user', 'valor']


class PreguntaSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Pregunta, mostrando su texto, cuestionario
    y constructos asociados.
    """
    class Meta:
        model = Pregunta
        fields = [
            'cve_pregunta', 'texto_pregunta', 'cuestionario',
            'cve_const1', 'cve_const2', 'cve_const3', 'cve_const4', 'scorekey'
        ]
        ref_name = 'PreguntaSerializerV1'  # Para evitar conflictos en la documentación


class CuestionarioSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Cuestionario, incluyendo:
    - Preguntas asociadas (lectura)
    - Respuestas asociadas (escritura)
    - Indicador booleano si la fecha actual sobrepasa la fecha fin (is_past)
    """
    preguntas = PreguntaSerializer(many=True, read_only=True, source='pregunta_set')
    respuestas = RespuestaSerializer(many=True, write_only=True)
    is_past = serializers.SerializerMethodField()

    class Meta:
        model = Cuestionario
        fields = [
            'cve_cuestionario', 'nombre_corto', 'preguntas', 'respuestas',
            'is_active', 'fecha_inicio', 'fecha_fin', 'is_past'
        ]

    def create(self, validated_data):
        """Crea un cuestionario y sus respuestas asociadas."""
        respuestas_data = validated_data.pop('respuestas')
        cuestionario = Cuestionario.objects.create(**validated_data)
        for respuesta_data in respuestas_data:
            Respuesta.objects.create(cuestionario=cuestionario, **respuesta_data)
        return cuestionario

    def update(self, instance, validated_data):
        """Actualiza un cuestionario y las respuestas asociadas."""
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

    def get_is_past(self, obj):
        """Retorna True si la fecha actual es posterior a la fecha fin del cuestionario."""
        if obj.fecha_fin:
            return date.today() > obj.fecha_fin
        return False


""" class ReporteDetailSerializer(serializers.ModelSerializer):
    
    #Serializador detallado del Reporte, mostrando la aplicación, el usuario,
    #la fecha, hora y observaciones.
  
    aplicacion = DatosAplicacionSerializer()
    user = UserPersonalInfoSerializer()

    class Meta:
        model = Reporte
        fields = ['cve_reporte', 'aplicacion', 'user', 'total', 'fecha', 'hora', 'texto', 'observaciones']

 """
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de un usuario genérico.
    Requiere confirmación de contraseña y asigna un grupo.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'groups']

    def validate(self, data):
        """Valida que las contraseñas coincidan."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """Crea un usuario y lo asigna al grupo especificado."""
        group_name = validated_data.pop('groups', [])
        user = CustomUser.objects.create_user(**validated_data)
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return user

class TutorsRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de tutores.
    Recibe nombres de instituto y carrera en lugar de sus IDs.
    """
    instituto = serializers.CharField(write_only=True, required=True)  # Ahora recibe un nombre
    carrera = serializers.CharField(write_only=True, required=True)  # Ahora recibe un nombre
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'password',
            'password2', 'fecha_nacimiento', 'instituto', 'carrera'
        ]

    def validate(self, data):
        """Valida contraseñas y existencia de instituto y carrera por nombre."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        # Validar existencia de instituto y carrera por nombre
        instituto_nombre = data.get('instituto')
        carrera_nombre = data.get('carrera')

        if not Instituto.objects.filter(nombre_completo=instituto_nombre).exists():
            raise serializers.ValidationError({"instituto": "El instituto especificado no existe."})

        if not Carrera.objects.filter(nombre=carrera_nombre).exists():
            raise serializers.ValidationError({"carrera": "La carrera especificada no existe."})

        return data

    def create(self, validated_data):
        """Crea el usuario tutor y lo asocia a la carrera e instituto por nombre."""
        instituto_nombre = validated_data.pop('instituto')
        carrera_nombre = validated_data.pop('carrera')

        # Obtener los objetos relacionados por nombre
        instituto = Instituto.objects.get(nombre_completo=instituto_nombre)
        carrera = Carrera.objects.get(nombre=carrera_nombre)

        # Crear el usuario
        user = CustomUser(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            fecha_nacimiento=validated_data['fecha_nacimiento'],
            carrera=carrera
        )
        user.set_password(validated_data['password'])
        user.save()

        # Asignar al grupo "Tutores"
        tutores_group, _ = Group.objects.get_or_create(name='Tutores')
        user.groups.add(tutores_group)

        return user

class IndicadorPromedioSerializer(serializers.ModelSerializer):
    """
    Serializador que muestra el nombre del indicador y su puntaje promedio.
    """
    nombre = serializers.CharField(source='indicador.nombre')
    prom_score = serializers.SerializerMethodField()

    class Meta:
        model = ScoreIndicador
        fields = ['nombre', 'prom_score']

    def get_prom_score(self, obj):
        """Calcula el promedio de puntuación para el indicador en un usuario."""
        constructos = ScoreConstructo.objects.filter(
            constructo__indicadorconstructo__indicador=obj.indicador,
            usuario=obj.usuario
        )
        if constructos.exists():
            total_score = sum([c.score for c in constructos])
            promedio = total_score / constructos.count()
            return int(promedio)
        return 0


class GroupIndicadorPromedioSerializer(serializers.Serializer):
    """
    Serializador para obtener el promedio de indicadores de todos los usuarios
    de un determinado grupo.
    """
    group_name = serializers.CharField()
    indicadores = serializers.SerializerMethodField()

    def get_indicadores(self, obj):
        """Retorna los indicadores promedio para el grupo especificado."""
        group_name = obj['group_name']
        users = CustomUser.objects.filter(groups__name=group_name)
        indicadores = ScoreIndicador.objects.filter(usuario__in=users)
        return IndicadorPromedioSerializer(indicadores, many=True).data


class GroupIndicadorScorePlanStudySerializer(serializers.Serializer):
    """
    Serializador que calcula el promedio de indicadores de usuarios en
    un determinado departamento, asociado a un plan de estudios.
    """
    departamento = serializers.CharField()
    promedio_indicadores = serializers.SerializerMethodField()

    def get_promedio_indicadores(self, obj):
        """Calcula el promedio de indicadores para un departamento."""
        departamento = obj['cve_departamento']
        users = CustomUser.objects.filter(carrera__departamento__nombre=departamento)
        indicadores = ScoreIndicador.objects.filter(usuario__in=users)
        if indicadores.exists():
            total_score = sum([i.score for i in indicadores])
            promedio = total_score / indicadores.count()
            return int(promedio)
        return 0


class CuestionarioStatusSerializer(serializers.Serializer):
    """
    Serializador que indica el estado de los cuestionarios para un usuario:
    - submited: cuestionarios con respuestas contestadas por el usuario.
    - on_hold: cuestionarios no contestados, divididos en 'current' y 'past'.
    """
    submited = serializers.SerializerMethodField()
    on_hold = serializers.SerializerMethodField()

    def get_user(self):
        """Obtiene el usuario autenticado desde el contexto del serializer."""
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuario no autenticado.")
        return request.user

    def get_submited(self, obj):
        """Retorna cuestionarios en los que el usuario ha respondido al menos una pregunta."""
        user = self.get_user()
        cuestionarios = Cuestionario.objects.filter(is_active=True)
        submited = []
        for c in cuestionarios:
            if Respuesta.objects.filter(user=user, pregunta__cuestionario=c).exists():
                data = CuestionarioSerializer(c).data
                submited.append(data)
        return submited

    def get_on_hold(self, obj):
        """Retorna cuestionarios no contestados por el usuario, separando en vigentes y pasados."""
        user = self.get_user()
        cuestionarios = Cuestionario.objects.filter(is_active=True)
        on_hold = {'current': [], 'past': []}
        for c in cuestionarios:
            if not Respuesta.objects.filter(user=user, pregunta__cuestionario=c).exists():
                data = CuestionarioSerializer(c).data
                if data['is_past']:
                    on_hold['past'].append(data)
                else:
                    on_hold['current'].append(data)
        return on_hold



""" class ReporteService:
    @staticmethod
    def generar_reporte(nivel, referencia_id, usuario):
        
        # Filtrar datos de AggregateIndicatorScore
        datos = AggregateIndicatorScore.objects.filter(nivel=nivel, referencia_id=referencia_id)

        if not datos.exists():
            raise ValueError(f"No hay datos para el nivel {nivel} con referencia {referencia_id}.")

        # Calcular promedio general
        total_score = sum(d.average_score for d in datos)
        total_indicadores = datos.count()
        promedio_general = total_score / total_indicadores if total_indicadores > 0 else 0

        # Generar textos descriptivos
        texto_fortalezas = f"El promedio general del nivel {nivel} es {promedio_general:.2f}."
        texto_oportunidades = "Identificar áreas de mejora basadas en indicadores con menor desempeño."

        # Crear y guardar el reporte
        reporte = Reporte.objects.create(
            nivel=nivel,
            referencia_id=referencia_id,
            usuario_generador=usuario,
            promedio=promedio_general,
            texto_fortalezas=texto_fortalezas,
            texto_oportunidades=texto_oportunidades
        )

        return reporte
 """