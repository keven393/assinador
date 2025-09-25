#!/usr/bin/env python3
"""
Otimizações específicas para dispositivos móveis e tablets
"""

from flask import request, g
import time
import re

def is_mobile_device():
    """Detecta se é um dispositivo móvel/tablet"""
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_indicators = [
        'mobile', 'android', 'iphone', 'ipad', 'tablet', 
        'samsung', 'chrome', 'safari'
    ]
    return any(indicator in user_agent for indicator in mobile_indicators)

def is_tablet():
    """Detecta especificamente tablets"""
    user_agent = request.headers.get('User-Agent', '').lower()
    tablet_indicators = ['ipad', 'tablet', 'android(?!.*mobile)']
    return any(re.search(pattern, user_agent) for pattern in tablet_indicators)

def get_device_performance_level():
    """Determina o nível de performance do dispositivo"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Dispositivos de alta performance
    if any(device in user_agent.lower() for device in ['iphone', 'ipad', 'samsung galaxy']):
        return 'high'
    
    # Dispositivos de média performance
    if any(device in user_agent.lower() for device in ['android', 'chrome']):
        return 'medium'
    
    # Dispositivos de baixa performance (fallback)
    return 'low'

def optimize_for_device():
    """Aplica otimizações baseadas no dispositivo"""
    if not is_mobile_device():
        return
    
    performance_level = get_device_performance_level()
    
    # Configurações baseadas na performance
    if performance_level == 'low':
        # Para dispositivos de baixa performance
        g.max_records = 20
        g.cache_timeout = 600  # 10 minutos
        g.enable_compression = True
    elif performance_level == 'medium':
        # Para dispositivos de média performance
        g.max_records = 50
        g.cache_timeout = 300  # 5 minutos
        g.enable_compression = True
    else:
        # Para dispositivos de alta performance
        g.max_records = 100
        g.cache_timeout = 180  # 3 minutos
        g.enable_compression = False

def get_optimized_query_limits():
    """Retorna limites otimizados para queries baseados no dispositivo"""
    if not is_mobile_device():
        return 100  # Desktop
    
    performance_level = get_device_performance_level()
    
    if performance_level == 'low':
        return 20
    elif performance_level == 'medium':
        return 50
    else:
        return 100

def should_use_compression():
    """Determina se deve usar compressão baseado no dispositivo"""
    if not is_mobile_device():
        return False
    
    # Sempre comprimir para mobile/tablet
    return True

def get_cache_timeout():
    """Retorna timeout de cache baseado no dispositivo"""
    if not is_mobile_device():
        return 300  # 5 minutos para desktop
    
    performance_level = get_device_performance_level()
    
    if performance_level == 'low':
        return 600  # 10 minutos
    elif performance_level == 'medium':
        return 300  # 5 minutos
    else:
        return 180  # 3 minutos

def optimize_database_queries():
    """Aplica otimizações específicas para queries de banco"""
    if not is_mobile_device():
        return {}
    
    return {
        'limit': get_optimized_query_limits(),
        'use_index': True,
        'prefetch_related': False,  # Evita prefetch em mobile
        'select_related': True,     # Usa select_related para reduzir queries
    }

def get_mobile_headers():
    """Retorna headers otimizados para mobile"""
    if not is_mobile_device():
        return {}
    
    return {
        'Cache-Control': 'private, max-age=300',
        'Vary': 'Accept-Encoding, User-Agent',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
    }

def log_performance_metrics():
    """Log de métricas de performance para mobile"""
    if not is_mobile_device():
        return
    
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        user_agent = request.headers.get('User-Agent', '')
        
        # Log apenas requests muito lentos em mobile
        if duration > 2.0:
            print(f"SLOW MOBILE REQUEST: {duration:.2f}s - {request.endpoint} - {user_agent[:50]}")

def optimize_static_content():
    """Otimizações para conteúdo estático em mobile"""
    if not is_mobile_device():
        return {}
    
    return {
        'minify_css': True,
        'minify_js': True,
        'compress_images': True,
        'lazy_load': True,
    }
