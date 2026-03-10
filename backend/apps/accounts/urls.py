from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('trocar-senha/', views.forced_password_change, name='forced_password_change'),

    # Gerenciamento de usuários (admin)
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/criar/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:pk>/toggle/', views.user_toggle_active, name='user_toggle_active'),
]
