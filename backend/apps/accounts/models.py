from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('analyst', 'Analista DP'),
        ('client', 'Cliente'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    company = models.ForeignKey(
        'companies.Company',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(
        default=False,
        verbose_name='Deve trocar senha no próximo login',
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f'{self.get_full_name() or self.username} [{self.get_role_display()}]'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_analyst(self):
        return self.role in ('admin', 'analyst')

    @property
    def is_client(self):
        return self.role == 'client'
