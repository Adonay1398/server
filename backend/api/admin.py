from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.contrib import admin
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

class MyAdminSite(admin.AdminSite):
    site_header ="Cerrar Aplicacion"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('cerrar_aplicacion/', self.admin_view(self.CerrarAplicacionCuestionarioView))
        ]
        return urls 

admin_site = MyAdminSite(name="custom_admin")

# Registrar el modelo solo si no está registrado
""" try:
    admin.site.register(PeriodicTask)
except admin.sites.AlreadyRegistered:
    pass
 """