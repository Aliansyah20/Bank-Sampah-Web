from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, lempar ke dashboard masing-masing
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Cari user di database
        user = User.query.filter_by(username=username).first()

        # Cek apakah user ada DAN password cocok 
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['nama_lengkap'] = user.nama_lengkap
            session['role'] = user.role
            
            return redirect_by_role(user.role)
        else:
            flash('Username atau password salah!', 'danger')
            return redirect(url_for('auth.login'))

    # INI ADALAH JAWABAN LANGKAH 3: Memanggil file login.html
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('auth.login'))

def redirect_by_role(role):
    if role == 'sekben':
        return redirect(url_for('sekben.dashboard'))
    elif role == 'pengolah':
        return redirect(url_for('pengolah.dashboard'))
    elif role == 'pemasaran':
        return redirect(url_for('pemasaran.dashboard'))
    else:
        return redirect(url_for('warga.dashboard'))