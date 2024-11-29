
from django.contrib import admin
from django.urls import path,include
from api.views import * #CreateUserView,RegisterTutorView, ScoreConstructoDetailViews, ScoreIndicadorListViews, ConstructoListViews, IndicadorListViews, ScoreConstructoListViews, IndicadorDetailViews, ConstructoDetailViews,ScoreIndicadorDetailViews

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api import urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/create-user/", CreateUserView.as_view(), name="create_user"),
    path("api/create-tutor/", CreateTutorView.as_view(), name="register_user"),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="get_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"), 
    path("api-auth/", include("rest_framework.urls")),
    
    path('profile/',ProfileListView.as_view(), name='profile-list'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('score-constructo/', ScoreConstructoListViews.as_view(), name='score-constructo-list'),
    path('score-constructo/<int:pk>/', ScoreConstructoDetailViews.as_view(), name='score-constructo-detail'),
    path('score-indicador/', ScoreIndicadorListViews.as_view(), name='score-indicador-list'),
    path('score-indicador/<int:pk>/', ScoreIndicadorDetailViews.as_view(), name='score-indicador-detail'),
    path('constructo/', ConstructoListViews.as_view(), name='constructo-list'),
    path('constructo/<int:pk>/', ConstructoDetailViews.as_view(), name='constructo-detail'),
    path('indicador/', IndicadorListViews.as_view(), name='indicador-list'),
    path('indicador/<int:pk>/', IndicadorDetailViews.as_view(), name='indicador-detail'),
    path('user/', UserRelateDataListView.as_view(), name='user-related-data-list'),

    path('user/<int:user_id>/score-constructo/', UserScoreConstructoListView.as_view(), name='user-score-constructo-list'),
    path('user/<int:user_id>/score-indicador/', UserScoreIndicadorListView.as_view(), name='user-score-indicador-list'),
    path('user/<int:pk>/related-data/', UserRelatedDataView.as_view(), name='user-related-data'),
]


    #path("")

