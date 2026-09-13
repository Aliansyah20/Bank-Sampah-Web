from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            # Jika user sudah login tapi rolenya tidak cocok dengan halaman ini
            if session.get('role') not in allowed_roles:
                flash('Anda tidak memiliki izin untuk mengakses halaman tersebut!', 'danger')
                # Arahkan ke logout agar sesi aman dan tidak memicu redirect loop
                session.clear()
                return redirect(url_for('auth.login'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator