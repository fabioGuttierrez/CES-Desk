from django.db import models
from core.models import TimestampedModel


class Article(TimestampedModel):
    title = models.CharField(max_length=255, verbose_name='Título')
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(verbose_name='Conteúdo')
    category = models.CharField(max_length=100, verbose_name='Categoria')
    tags = models.CharField(max_length=255, blank=True)
    published = models.BooleanField(default=True, verbose_name='Publicado')
    views = models.IntegerField(default=0, verbose_name='Visualizações')
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name='Autor',
    )

    class Meta:
        verbose_name = 'Artigo'
        verbose_name_plural = 'Artigos'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
