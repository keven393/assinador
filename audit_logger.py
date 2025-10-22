import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def _ensure_logs_dir(logs_dir: str) -> None:
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        pass


# Configure audit logger
_DEFAULT_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
_ensure_logs_dir(_DEFAULT_LOGS_DIR)
_AUDIT_LOG_PATH = os.path.join(_DEFAULT_LOGS_DIR, 'audit.log')

audit_logger = logging.getLogger("assinador_audit")
if not audit_logger.handlers:
    audit_handler = RotatingFileHandler(_AUDIT_LOG_PATH, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    audit_handler.setFormatter(logging.Formatter('%(message)s'))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)


def log_event(action: str,
              actor_user_id: int | None = None,
              status: str | None = None,
              ip_address: str | None = None,
              details: dict | None = None,
              target_user_id: int | None = None) -> None:
    """Logs a generic audit event as one JSON line.

    action: short action key, e.g. 'login', 'logout', 'ad_sync_all'
    status: optional status like 'success' | 'error'
    details: optional dict with extra fields
    """
    try:
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "status": status,
            "actor_user_id": actor_user_id,
            "target_user_id": target_user_id,
            "ip_address": ip_address,
            "details": details or {}
        }
        audit_logger.info(json.dumps(event, ensure_ascii=False))
    except Exception:
        # Never raise from audit logging
        pass


def log_signature_event(user_id: int | None, file_id: str | None, status: str, ip_address: str | None = None, details: dict | None = None):
    data = {"file_id": file_id}
    if details:
        data.update(details)
    log_event(action="signature", actor_user_id=user_id, status=status, ip_address=ip_address, details=data)


def log_validation_event(file_id: str | None, status: str, ip_address: str | None = None, is_valid: bool | None = None):
    details = {"file_id": file_id, "is_valid": is_valid}
    log_event(action="validation", status=status, ip_address=ip_address, details=details)

"""
Módulo de logging de auditoria estruturado em JSON
"""
import logging
import json
import os
from datetime import datetime
from config import Config

# Configurar logger de auditoria
audit_logger = logging.getLogger("assinador_audit")
audit_logger.setLevel(logging.INFO)

# Handler para arquivo de auditoria
audit_log_path = os.path.join(Config.LOGS_DIR, "audit.log")
audit_handler = logging.FileHandler(audit_log_path)
audit_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(audit_handler)

# Evitar propagação para o logger root
audit_logger.propagate = False

def log_signature_event(user_id, file_id, status, ip_address=None, details=None):
    """
    Loga evento de assinatura em formato JSON
    
    Args:
        user_id: ID do usuário
        file_id: ID do arquivo
        status: Status da assinatura (success, failed, etc)
        ip_address: Endereço IP do cliente
        details: Dicionário com detalhes adicionais
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "signature",
        "user_id": user_id,
        "file_id": file_id,
        "status": status,
        "ip_address": ip_address,
        "details": details or {}
    }
    audit_logger.info(json.dumps(event))

def log_validation_event(file_id, status, ip_address=None, is_valid=None):
    """
    Loga evento de validação
    
    Args:
        file_id: ID do arquivo
        status: Status da validação
        ip_address: Endereço IP do cliente
        is_valid: Se a validação foi bem-sucedida
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "validation",
        "file_id": file_id,
        "status": status,
        "is_valid": is_valid,
        "ip_address": ip_address
    }
    audit_logger.info(json.dumps(event))

def log_failed_signature(user_id, file_id, ip_address, reason):
    """
    Loga tentativa de assinatura falhada
    
    Args:
        user_id: ID do usuário
        file_id: ID do arquivo
        ip_address: Endereço IP do cliente
        reason: Motivo da falha
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "signature_failed",
        "user_id": user_id,
        "file_id": file_id,
        "ip_address": ip_address,
        "reason": reason
    }
    audit_logger.warning(json.dumps(event))

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    Loga evento de segurança
    
    Args:
        event_type: Tipo do evento (login_failed, rate_limit_exceeded, etc)
        user_id: ID do usuário (opcional)
        ip_address: Endereço IP do cliente
        details: Dicionário com detalhes adicionais
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "security",
        "security_event": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    audit_logger.warning(json.dumps(event))

def log_admin_action(admin_id, action, target_id=None, ip_address=None, details=None):
    """
    Loga ação administrativa
    
    Args:
        admin_id: ID do administrador
        action: Ação realizada
        target_id: ID do alvo da ação (opcional)
        ip_address: Endereço IP do administrador
        details: Dicionário com detalhes adicionais
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "admin_action",
        "admin_id": admin_id,
        "action": action,
        "target_id": target_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    audit_logger.info(json.dumps(event))

