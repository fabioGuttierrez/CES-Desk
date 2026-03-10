from rest_framework import serializers
from apps.accounts.models import User
from apps.companies.models import Company
from apps.tickets.models import Ticket, TicketCategory, TicketMessage
from apps.attachments.models import Attachment
from apps.sla.models import TicketSLA
from apps.notifications.models import Notification
from apps.knowledge_base.models import Article


# ── Accounts ──────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'role', 'company', 'phone', 'avatar', 'is_active')
        read_only_fields = ('id',)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password', 'role', 'company', 'phone')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ── Companies ─────────────────────────────────────────────────────────────────

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = '__all__'


class TicketSLASerializer(serializers.ModelSerializer):
    response_status = serializers.ReadOnlyField()
    resolution_status = serializers.ReadOnlyField()

    class Meta:
        model = TicketSLA
        fields = '__all__'


class AttachmentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name', read_only=True
    )

    class Meta:
        model = Attachment
        fields = ('id', 'file_url', 'file_name', 'file_size', 'file_size_display',
                  'content_type', 'uploaded_by', 'uploaded_by_name', 'created_at')
        read_only_fields = ('id', 'created_at')


class TicketMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = ('id', 'ticket', 'author', 'author_name', 'author_role',
                  'message', 'is_internal', 'attachments', 'created_at')
        read_only_fields = ('id', 'author', 'created_at')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            'id', 'number', 'subject', 'company', 'company_name',
            'category', 'category_name', 'priority', 'status',
            'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        )


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    sla = TicketSLASerializer(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True
    )

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('id', 'number', 'created_by', 'company', 'created_at', 'updated_at')


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('subject', 'description', 'category', 'priority')

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        validated_data['company'] = request.user.company
        return super().create(validated_data)


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at')


# ── Knowledge Base ────────────────────────────────────────────────────────────

class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Article
        fields = '__all__'
        read_only_fields = ('id', 'views', 'author', 'created_at', 'updated_at')
