# api/urls.py

from django.urls import path
from .views import (
    CreateUserView, RegisterTutorView, ScoreConstructoDetailViews, ScoreIndicadoreListViews, ScoreIndicadoreDetailViews)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register-user/', RegisterTutorView.as_view(), name='register_user'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('token/', TokenObtainPairView.as_view(), name='get_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('score-constructo/', ScoreConstructoDetailViews.as_view(), name='score-constructo-list'),
    path('score-constructo/<int:pk>/', ScoreConstructoDetailViews.as_view(), name='score-constructo-detail'),
    path('score-indicador/', ScoreIndicadoreListViews.as_view(), name='score-indicador-list'),
    path('score-indicador/<int:pk>/', ScoreIndicadoreDetailViews.as_view(), name='score-indicador-detail'),
]