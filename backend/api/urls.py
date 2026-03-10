from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomAuthToken,
    UserViewSet,
    CompanyViewSet,
    TicketCategoryViewSet,
    TicketViewSet,
    TicketMessageViewSet,
    NotificationViewSet,
    ArticleViewSet,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('companies', CompanyViewSet, basename='company')
router.register('categories', TicketCategoryViewSet, basename='category')
router.register('tickets', TicketViewSet, basename='ticket')
router.register('messages', TicketMessageViewSet, basename='message')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('knowledge', ArticleViewSet, basename='article')

urlpatterns = [
    path('auth/login/', CustomAuthToken.as_view(), name='api_login'),
    path('', include(router.urls)),
]
