from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('kanban/', views.kanban, name='kanban'),
    path('kanban/move/', views.kanban_move, name='kanban_move'),
    path('notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
    path('feriados/', views.holiday_list, name='holiday_list'),
    path('feriados/add/', views.holiday_create, name='holiday_create'),
    path('feriados/<int:pk>/delete/', views.holiday_delete, name='holiday_delete'),
]
