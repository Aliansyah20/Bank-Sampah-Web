from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

# --- HALAMAN LOGIN ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['nama_lengkap'] = user.nama_lengkap
            session['role'] = user.role
            return redirect_by_role(user.role)
        else:
            flash('Username atau password salah! Silakan coba lagi.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


# --- HALAMAN DAFTAR AKUN (REGISTRASI) ---
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        tipe_daftar = request.form.get('tipe_daftar')  # 'warga' atau 'petugas'
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        konfirmasi_password = request.form.get('konfirmasi_password', '').strip()

        # Validasi kecocokan password
        if password != konfirmasi_password:
            flash('Konfirmasi password tidak cocok!', 'danger')
            return redirect(url_for('auth.register'))

        # Cek apakah username sudah dipakai
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" sudah digunakan, silakan pilih yang lain.', 'danger')
            return redirect(url_for('auth.register'))

        # Tentukan Role
        # Tentukan Role
        if tipe_daftar == 'petugas':
            role_pilihan = request.form.get('role', '').strip().lower()
            if role_pilihan not in ['sekben', 'pengolah', 'marketing', 'pengawas']:
                flash('Role petugas tidak valid!', 'danger')
                return redirect(url_for('auth.register'))
            role_final = role_pilihan
        else:
            role_final = 'warga'

        # Simpan Akun Baru ke Database
        user_baru = User(
            nama_lengkap=nama_lengkap,
            username=username,
            password=generate_password_hash(password),
            role=role_final,
            saldo_terkini=0.0
        )
        db.session.add(user_baru)
        db.session.commit()

        flash(f'Pendaftaran berhasil! Silakan login dengan akun baru Anda.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# --- LOGOUT ---
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('auth.login'))


# --- PENGALIHAN BERDASARKAN ROLE ---
def redirect_by_role(role):
    if role == 'sekben':
        return redirect(url_for('sekben.dashboard'))
    elif role == 'pengolah':
        return redirect(url_for('pengolah.dashboard'))
    elif role == 'marketing':
        return redirect(url_for('marketing.dashboard'))
    elif role == 'pengawas':
        return redirect(url_for('pengawas.dashboard'))
    elif role == 'warga':
        return redirect(url_for('warga.dashboard'))
    else:
        # Pengaman: jika role tidak dikenali, bersihkan sesi agar tidak loop
        session.clear()
        return redirect(url_for('auth.login'))