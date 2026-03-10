from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Article
from django.urls import path


def article_list(request):
    category = request.GET.get('category')
    q = request.GET.get('q')

    articles = Article.objects.filter(published=True).order_by('-created_at')
    if category:
        articles = articles.filter(category=category)
    if q:
        articles = articles.filter(title__icontains=q)

    categories = Article.objects.filter(published=True).values_list('category', flat=True).distinct()
    return render(request, 'knowledge_base/list.html', {
        'articles': articles,
        'categories': categories,
        'current_category': category,
    })


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, published=True)
    article.views += 1
    article.save(update_fields=['views'])
    return render(request, 'knowledge_base/detail.html', {'article': article})


urlpatterns = [
    path('', article_list, name='knowledge_list'),
    path('<slug:slug>/', article_detail, name='knowledge_detail'),
]
