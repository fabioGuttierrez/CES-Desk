from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.companies.models import Company
from apps.tickets.models import Ticket, TicketCategory, TicketMessage
from apps.attachments.models import Attachment
from apps.sla.models import TicketSLA
from apps.notifications.models import Notification
from apps.knowledge_base.models import Article
from core.mixins import CompanyScopedMixin
from core.permissions import IsAdmin, IsAnalyst, IsOwnerOrAnalyst

from .serializers import (
    UserSerializer, UserCreateSerializer,
    CompanySerializer,
    TicketCategorySerializer,
    TicketListSerializer, TicketDetailSerializer, TicketCreateSerializer,
    TicketMessageSerializer,
    AttachmentSerializer,
    TicketSLASerializer,
    NotificationSerializer,
    ArticleSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'company_id': user.company_id,
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['role', 'company', 'is_active']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAnalyst]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'cnpj', 'email']


class TicketCategoryViewSet(viewsets.ModelViewSet):
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAnalyst]


class TicketViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrAnalyst]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'company', 'category', 'assigned_to']
    search_fields = ['number', 'subject', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Ticket.objects.select_related(
            'company', 'created_by', 'assigned_to', 'category'
        )
        user = self.request.user
        if user.role == 'client' and user.company:
            return qs.filter(company=user.company)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        if self.action in ('retrieve', 'update', 'partial_update'):
            return TicketDetailSerializer
        return TicketListSerializer

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        ticket = self.get_object()
        msgs = ticket.messages.all()
        if request.user.role == 'client':
            msgs = msgs.filter(is_internal=False)
        serializer = TicketMessageSerializer(msgs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        data = request.data.copy()
        data['ticket'] = ticket.pk
        serializer = TicketMessageSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], permission_classes=[IsAnalyst])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        analyst_id = request.data.get('analyst_id')
        ticket.assigned_to_id = analyst_id
        ticket.status = 'in_progress'
        ticket.save(update_fields=['assigned_to', 'status'])
        return Response({'detail': 'Ticket atribuído.'})

    @action(detail=True, methods=['patch'], permission_classes=[IsAnalyst])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Ticket.STATUS_CHOICES):
            return Response({'detail': 'Status inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = new_status
        ticket.save(update_fields=['status'])
        return Response({'detail': 'Status atualizado.'})

    @action(detail=False, methods=['get'], permission_classes=[IsAnalyst])
    def metrics(self, request):
        qs = Ticket.objects.all()
        now = timezone.now()

        data = {
            'total': qs.count(),
            'open': qs.filter(status='open').count(),
            'in_progress': qs.filter(status='in_progress').count(),
            'waiting': qs.filter(status='waiting').count(),
            'resolved': qs.filter(status='resolved').count(),
            'closed': qs.filter(status='closed').count(),
            'urgent': qs.filter(priority='urgent', status__in=['open', 'in_progress']).count(),
            'sla_breached': TicketSLA.objects.filter(
                resolution_breached=True,
                ticket__status__in=['open', 'in_progress', 'waiting']
            ).count(),
            'by_category': list(
                qs.values('category__name').annotate(total=Count('id')).order_by('-total')
            ),
            'by_company': list(
                qs.values('company__name').annotate(total=Count('id')).order_by('-total')[:10]
            ),
            'by_priority': list(
                qs.values('priority').annotate(total=Count('id'))
            ),
        }
        return Response(data)


class TicketMessageViewSet(viewsets.ModelViewSet):
    queryset = TicketMessage.objects.all()
    serializer_class = TicketMessageSerializer
    permission_classes = [IsOwnerOrAnalyst]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ticket', 'is_internal']


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'detail': 'Todas marcadas como lidas.'})


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(published=True)
    serializer_class = ArticleSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content', 'tags']
    filterset_fields = ['category', 'published']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAnalyst()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        return super().retrieve(request, *args, **kwargs)
