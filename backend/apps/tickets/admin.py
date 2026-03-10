from django.contrib import admin
from .models import Ticket, TicketCategory, TicketMessage


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sla_hours', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    ordering = ('order', 'name')


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ('author', 'created_at')
    fields = ('author', 'message', 'is_internal', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'subject', 'company', 'created_by',
        'assigned_to', 'category', 'priority', 'status', 'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'company')
    search_fields = ('number', 'subject', 'description')
    readonly_fields = ('number', 'created_at', 'updated_at')
    inlines = [TicketMessageInline]
    ordering = ('-created_at',)
