from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from .views import CerrarAplicacionCuestionarioView
class CustomUserAdmin(UserAdmin):
    # Campos que se mostrarán en la lista de usuarios
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    
    # Campos que se pueden buscar
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Campos que se pueden editar en el formulario de edición de usuario
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'fecha_nacimiento')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # Campos que se pueden editar en el formulario de creación de usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# Registrar el modelo CustomUser con la configuración personalizada
admin.site.register(CustomUser, CustomUserAdmin)


# Personalizar la barra lateral del admin para incluir la nueva vista
class CustomAdminSite(admin.AdminSite):
    site_header = "Administrador personalizado"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'cerrar-cuestionario/',
                self.admin_view(CerrarAplicacionCuestionarioView.as_view()),
                name='cerrar_aplicacion_cuestionario'
            ),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        # Agregar información adicional al dashboard
        extra_context = extra_context or {}
        extra_context['custom_section'] = format_html(
            '<a href="{}" class="button">Cerrar Cuestionario</a>',
            path('cerrar-cuestionario/')
        )
        return super().index(request, extra_context=extra_context)

# Instanciar el sitio de administración personalizado
custom_admin_site = CustomAdminSite(name='custom_admin')

# Registrar los modelos en el sitio de administración personalizado
custom_admin_site.register(CustomUser, CustomUserAdmin)

""" 
def get_custom_urls():
    return [
        path('cerrar-cuestionario/', CerrarAplicacionCuestionarioView.as_view(), name="cerrar_aplicacion_cuestionario")
    ]
original_get_urls = admin.site.get_urls
def custom_admin_urls():
    return get_custom_urls() + original_get_urls()
    #admin_site = MyAdminSte(name="custom_admin")
admin.site.get_urls = custom_admin_urls
# Registrar el modelo solo i no está registrado
# try:
    admin.site.register(PeriodicTask)
except admin.sites.AlreadyRegistered:
    pass
  """