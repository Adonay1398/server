# api/urls.py

from django.urls import path
from .views import (
    CreateUserView, CreateTutorView , ScoreConstructoDetailViews, ScoreIndicadorListViews, ScoreIndicadorDetailViews,ConstructoListViews,IndicadorListViews,IndicadorDetailViews,ScoreConstructoListViews,ConstructoDetailViews)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register-user/', CreateTutorView.as_view(), name='register_user'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('token/', TokenObtainPairView.as_view(), name='get_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh'),

    #path('profile/', ProfileListViews.as_view(), name='profile-list'),
    path('score-constructo/', ScoreConstructoListViews.as_view(), name='score-constructo-list'),
    path('score-constructo/<int:pk>/', ScoreConstructoDetailViews.as_view(), name='score-constructo-detail'),
    path('score-indicador/', ScoreIndicadorListViews.as_view(), name='score-indicador-list'),
    path('score-indicador/<int:pk>/', ScoreIndicadorDetailViews.as_view(), name='score-indicador-detail'),
    path('indicador/', IndicadorListViews.as_view(), name='indicador-list'),
    path('indicador/<int:pk>/', IndicadorDetailViews.as_view(), name='indicador-detail'),
    path('constructo/<int:pk>/', ConstructoDetailViews.as_view(), name='constructo-detail'),
    path('constructo/', ConstructoListViews.as_view(), name='constructo-list'),

]