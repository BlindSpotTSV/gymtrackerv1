from functools import wraps

from flask import jsonify
from flask_login import current_user


def role_required(*allowed_roles):
    """Boundary-level RBAC guard. Domain ownership is also checked in controllers."""
    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify(error="Authentication required."), 401
            if not current_user.is_active:
                return jsonify(error="Account is inactive."), 403
            if current_user.role not in allowed_roles:
                return jsonify(error="You do not have permission to access this resource."), 403
            return view_function(*args, **kwargs)
        return wrapped
    return decorator
