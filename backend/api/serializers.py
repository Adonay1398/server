
from datetime import date
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

from api.models import (
    AsignacionCuestionario, CustomUser, Carrera, IndicadorPromedio, Region, RetroChatGPT,  ScoreConstructo, ScoreIndicador, Constructo, Indicador,
    Instituto, Departamento, DatosAplicacion, Respuesta, Cuestionario ,  Pregunta,  Reporte, 
)

#RetroChatGPT
class CarreraSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Carrera. Retorna su clave, nombre e instituto.
    """
    def get_carrera(self,obj):
        datos = Carrera.objects.filter(cve_carrera=obj.cve_carrera, nombre=obj.nombre)
    class Meta:
        model = Carrera
        fields = [ 'nombre' ]


class CarreraDetailSerializer(serializers.ModelSerializer):
    """
    Serializador detallado de la Carrera.
    Incluye el departamento y el instituto asociados, retornando sus nombres.
    """
    departamento = serializers.SerializerMethodField()
    instituto = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = ['cve_carrera','nombre', 'departamento', 'instituto']

    def get_departamento(self, obj):
        """Retorna el nombre del departamento asociado a la carrera."""
        return obj.departamento.id

    def get_instituto(self, obj):
        """Retorna el nombre completo del instituto asociado a la carrera."""
        Instituto.objects.get(cve_inst=obj.instituto.cve_inst)
        return (Instituto.objects.get(cve_inst=obj.instituto.cve_inst)).nombre_completo
    


class InstitutoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Instituto, mostrando datos básicos.
    """
    def get_isntitos(self,obj):
        datos = Instituto.objects.filter(cve_inst=obj.cve_inst, nombre_completo=obj.nombre_completo)
    class Meta:
        model = Instituto
        fields = [ 'nombre_completo']


class DepartamentoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Departamento, mostrando su clave, nombre y jefe.
    """
    carreras= CarreraSerializer(many=True, read_only=True)
    def get_departamento(self,obj):
        datos = Departamento.objects.filter(cve_depto=obj.cve_depto, nombre=obj.nombre)
    class Meta:
        model = Departamento
        fields = [ 'nombre','carreras' ]


class ConstructoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Constructo, mostrando su clave, descripción y acrónimo.
    """
    class Meta:
        model = Constructo
        fields = ['cve_const', 'descripcion']


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
    - Retroalimentación basada en indicadores del cuestionario.
    """
    #informacion_personal = UserPersonalInfoSerializer(source='*')
    #indicador = serializers.SerializerMethodField()
    retrochatgpt = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [  'retrochatgpt']

    

    def get_retrochatgpt(self, obj):
        """
        Retorna la retroalimentación basada en indicadores de un cuestionario específico.
        """
        request = self.context.get('request')
        cuestionario_id = self.context.get('Cuestionario_id')
        aplicacion_id = self.context.get('aplicacion')
        
        if not cuestionario_id :
            raise serializers.ValidationError("El parámetro 'cuestionario_id' es obligatorio.")
        
        if not aplicacion_id:
            raise serializers.ValidationError("Los parámetros  'aplicacion_id' son obligatorios.")

        
        user = request.user

        # Filtrar indicadores del cuestionario específico
        #indicadores = ScoreIndicador.objects.filter(
        #    usuario=user,
         #   aplicacion__cuestionario__cve_cuestionario=cuestionario_id
        #)

        #if not indicadores.exists():
         #   return []

        # Obtener retroalimentaciones relacionadas con esos indicadores
        print("ok")
        retroalimentaciones = RetroChatGPT.objects.filter(
            usuario=user,Cuestionario_id =cuestionario_id, aplicacion_id = aplicacion_id
        )
        print("ok2")
        if not retroalimentaciones.exists():
            return {"mensaje": "No se encontraron retroalimentaciones para este cuestionario y aplicación."}

        return [
            {
                retro.texto1 if retro.texto1 else None,
                retro.texto2 if retro.texto2 else None
            }
            for retro in retroalimentaciones
        ]
class UserRelatedDataReporteSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar datos relacionados al usuario:
    - Información personal
    - Indicadores y sus puntajes basados en un cuestionario
    - Información del reporte asociado al cuestionario
    """
    informacion_personal = UserPersonalInfoSerializer(source='*')
    indicador = serializers.SerializerMethodField()
    reporte = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['informacion_personal', 'indicador', 'reporte']

    def get_indicador(self, obj):
        """
        Retorna los indicadores y sus puntajes para el cuestionario especificado.
        """
        request = self.context.get('request')
        cuestionario_id = self.context.get('cuestionario_id')

        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuario no autenticado.")

        # Filtrar los indicadores por usuario y cuestionario
        user = request.user
        indicadores = ScoreIndicador.objects.filter(usuario=user, cuestionario_id=cuestionario_id)
        return IndicadorScoreSerializer(indicadores, many=True).data

    def get_reporte(self, obj):
        """
        Retorna el reporte basado en el cuestionario especificado.
        """
        request = self.context.get('request')
        cuestionario_id = self.context.get('cuestionario_id')

        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuario no autenticado.")

        # Filtrar el reporte por usuario y cuestionario
        user = request.user
        reporte = Reporte.objects.filter(usuario_generador=user, cuestionario_id=cuestionario_id).order_by('-fecha_generacion').first()
        if not reporte:
            return None
        return {
            "id": reporte.id,
            "texto_fortalezas": reporte.texto_fortalezas,
            "texto_oportunidades": reporte.texto_oportunidades,
            "observaciones": reporte.observaciones,
        }





class DatosAplicacionSerializer(serializers.ModelSerializer):
    """
    Serializador para DatosAplicacion, mostrando información de la aplicación,
    fecha, hora y cuestionarios asociados.
    """
    class Meta:
        model = DatosAplicacion 
        
        
    
        fields = ['cve_aplic', 'fecha', 'hora', 'cuestionario', 'observaciones']


class RespuestaSerializer(serializers.ModelSerializer):
    valor = serializers.IntegerField(min_value=0, max_value=4, help_text="Valor de respuesta entre 1 y 5.")
    pregunta = serializers.PrimaryKeyRelatedField(queryset=Pregunta.objects.all(), help_text="ID de la pregunta.")

    class Meta:
        model = Respuesta
        fields = ['pregunta', 'valor']


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




class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de un usuario genérico.
    Requiere confirmación de contraseña y asigna un grupo.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm password")
    groups = serializers.CharField(write_only=True, required=True)

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
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
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
            'id',  'first_name', 'last_name', 'email', 'password',
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
        
        fecha_nacimiento = data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            age = (
                today.year - fecha_nacimiento.year
                - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            )
            if age < 15 or age > 99:
                raise serializers.ValidationError({"fecha_nacimiento": "La edad debe estar entre 15 y 99 años."})

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
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            fecha_nacimiento=validated_data['fecha_nacimiento'],
            carrera=carrera,
            
            
        )
        user.set_password(validated_data['password'])
        user.save()

        # Asignar al grupo "Tutores"
        tutores_group, _ = Group.objects.get_or_create(name='Tutores')
        user.groups.add(tutores_group)
        try:
            aplicacion = DatosAplicacion.objects.get(pk=4)  # Busca la aplicación con ID 4
            cuestionario = Cuestionario.objects.get(pk=14)  # Busca el cuestionario con ID 4

            # Crear la asignación en el modelo AsignacionCuestionario
            AsignacionCuestionario.objects.create(
                usuario=user,
                cuestionario=cuestionario,
                aplicacion=aplicacion,   
            )
        except DatosAplicacion.DoesNotExist:
            raise serializers.ValidationError("La aplicación con ID 4 no existe.")
        except Cuestionario.DoesNotExist:
            raise serializers.ValidationError("El cuestionario con ID 4 no existe.")
        

        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
   def validate(self, attrs):
        # Obtén el modelo de usuario configurado en Django
        User = get_user_model()

        # Busca al usuario por email
        try:
            user = User.objects.get(email=attrs.get('email'))
        except User.DoesNotExist:
            raise AuthenticationFailed('No se encontró un usuario con este correo electrónico.')

        # Verifica la contraseña
        if not user.check_password(attrs.get('password')):
            raise AuthenticationFailed('Contraseña incorrecta.')

        # Verifica si el usuario está activo
        if not user.is_active:
            raise AuthenticationFailed('Esta cuenta está inactiva.')

        # Genera los tokens
        refresh_token = self.get_token(user)
        access_token = refresh_token.access_token

        # Incluye grupos en el token
        groups = [group.name for group in user.groups.all()]
        refresh_token['groups'] = groups

        # Devuelve los tokens con la información adicional
        return {
            'refresh': str(refresh_token),
            'access': str(access_token),
        }

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
    - on_hold: cuestionarios no contestados o incompletos, divididos en 'current' y 'past'.
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
        """Retorna cuestionarios en los que el usuario ha contestado todas las preguntas."""
        user = self.get_user()
        cuestionarios = Cuestionario.objects.filter(is_active=True)
        print(Cuestionario.objects.filter(is_active=True))
        

        submited = []
        for c in cuestionarios:
            total_preguntas = c.preguntas.count()
            preguntas_contestadas = Respuesta.objects.filter(user=user, pregunta__cuestionario=c).count()
            print(preguntas_contestadas, total_preguntas)
            if total_preguntas > 0 and total_preguntas == preguntas_contestadas:
                data = CuestionarioSerializer(c).data
                # Obtener fecha de contestado desde AsignacionCuestionario
                

                print(f"Cuestionario {c.cve_cuestionario}: Total preguntas {total_preguntas}, Contestadas {preguntas_contestadas}")
                # Agregar aplicaciones relacionadas al cuestionario
                aplicaciones = DatosAplicacion.objects.filter(cuestionario=c)
                data['aplicaciones'] = [{'cve_aplic': app.cve_aplic, 'fecha': app.fecha} for app in aplicaciones]
                data['total_preguntas'] = total_preguntas
                data['preguntas_contestadas'] = preguntas_contestadas
                submited.append(data)
                print(f"Submited data: {data}")

        return submited

    def get_on_hold(self, obj):
        """Retorna cuestionarios no contestados o incompletos por el usuario, separando en vigentes y pasados."""
        user = self.get_user()
        cuestionarios = Cuestionario.objects.filter(is_active=True)
        on_hold = {'current': [], 'past': []}
        for c in cuestionarios:
            total_preguntas = c.preguntas.count()
            preguntas_contestadas = Respuesta.objects.filter(user=user, pregunta__cuestionario=c).count()
            if preguntas_contestadas < total_preguntas:
                data = CuestionarioSerializer(c).data
                # Agregar aplicaciones relacionadas al cuestionario
                aplicaciones = DatosAplicacion.objects.filter(cuestionario=c)
                data['aplicaciones'] = [{'cve_aplic': app.cve_aplic} for app in aplicaciones]
                data['total_preguntas'] = total_preguntas
                data['preguntas_contestadas'] = preguntas_contestadas
                if data['is_past']:
                    on_hold['past'].append(data)
                else:
                    on_hold['current'].append(data)
        return on_hold

class ConsultaJerarquicaSerializer(serializers.Serializer):
    identificador = serializers.CharField()  # Ajusta el tipo según lo que esperes

class ConsultaJerarquicaResponseSerializer(serializers.Serializer):
    resultados = serializers.DictField(
        child=serializers.DictField(
            child=serializers.FloatField(),
            help_text="Promedio del indicador específico."
        ),
        help_text="Diccionario que contiene los promedios de indicadores organizados por entidad. Cada clave principal representa una entidad, y sus valores son diccionarios de indicadores con sus respectivos promedios."
    )
    retroalimentacion = serializers.DictField(
        child=serializers.CharField(),
        help_text="Retroalimentación generada basada en los resultados de la consulta jerárquica, incluyendo fortalezas y oportunidades identificadas."
    )

# The `RegionSerializer` class serializes Region objects along with related Instituto objects.
class RegionSerializer(serializers.ModelSerializer):
    institutos = InstitutoSerializer(many=True, read_only=True, source='instituto_set')
    def get_region(self,obj):
        datos = Region.objects.filter(cve_region=obj.cve_region, nombre=obj.nombre)
    #obiene los datos de la region cve_region , nombre y institutos 
    class Meta:
        model = Region
        fields = ['cve_region', 'nombre', 'institutos']


class RetroChatGPTSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetroChatGPT
        fields = ['id', 'texto1', 'texto2', 'creado_en']
    #obtiene los datos de la retroalimentacion texto1, texto2 y creado_en
        

class IndicadorPromedioSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicadorPromedio
        fields = ['indicador', 'promedio']
        
class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['texto_fortalezas', 'texto_oportunidades', 'observaciones']
        


class InstitutoSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Instituto, incluyendo las carreras.
    """
    carreras = serializers.SerializerMethodField()

    class Meta:
        model = Instituto
        fields = ['nombre_completo', 'carreras']  # Solo incluir el nombre del instituto y las carreras

    def get_carreras(self, obj):
        """
        Obtiene las carreras asociadas al instituto a través de sus departamentos.
        """
        carreras = Carrera.objects.filter(departamento__instituto=obj)
        return CarreraSerializer(carreras, many=True).data