"""
Кастомный middleware для Rate Limiting и дополнительных заголовков безопасности
"""
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
import re


class RateLimitMiddleware:
    """
    Rate limiting по IP адресу для публичных endpoints
    Отключается при DEBUG=True для удобства локальной разработки.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Исключить из rate limit
        self.excluded_paths = ['/admin/', '/api/docs/']
    
    def __call__(self, request):
        # Пропустить rate limit при DEBUG (локальная разработка)
        if settings.DEBUG:
            return self.get_response(request)
        
        # Пропустить excluded пути
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)
        
        # Получаем IP адрес
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Ограничение: 200 запросов в минуту
        cache_key = f'rate_limit_{ip}'
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 200:
            return JsonResponse(
                {'detail': 'Слишком много запросов. Попробуйте позже.'},
                status=429
            )
        
        cache.set(cache_key, request_count + 1, 60)  # 60 секунд
        
        response = self.get_response(request)
        
        # Добавляем заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response


class SecurityHeadersMiddleware:
    """
    Добавление дополнительных заголовков безопасности
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Дополнительные заголовки безопасности
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
