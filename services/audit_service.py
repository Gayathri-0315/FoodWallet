import json
from models import db, AuditLog

def log_audit_event(actor_type, actor_id, action, entity, entity_id, details=None):
    """
    Logs an action to the AuditLog database table.
    """
    try:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
        log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details_str
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        print(f"Error recording audit log: {e}")
        return None
