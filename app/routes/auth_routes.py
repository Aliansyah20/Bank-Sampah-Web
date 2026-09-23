import re
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
            # Cegah masuk jika akun petugas belum diotorisasi pengawas
            if not user.is_aktif:
                flash('Akun Anda belum disetujui oleh Pengawas RW. Harap hubungi pengawas!', 'danger')
                return redirect(url_for('auth.login'))

            session['user_id'] = user.id
            session['role'] = user.role
            session['nama_lengkap'] = user.nama_lengkap
            return redirect_by_role(user.role)
        else:
            flash('Username atau kata sandi salah!', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


# --- HALAMAN DAFTAR AKUN (REGISTRASI) ---
# Tentukan kode rahasia RW (bisa kamu ubah sesuka hati)
KODE_RAHASIA_PENGAWAS = "RW2026"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        konfirmasi_password = request.form.get('konfirmasi_password', '').strip()
        role = request.form.get('role', '').strip().lower()
        kode_rw = request.form.get('kode_rw', '').strip()

        # 1. Pastikan role valid
        if role not in ['sekben', 'pengolah', 'marketing', 'pengawas']:
            flash('Pilihan posisi petugas tidak valid!', 'danger')
            return redirect(url_for('auth.register'))

        # 2. Validasi khusus Pengawas (Wajib punya kode rahasia RW)
        is_aktif_status = False
        if role == 'pengawas':
            if kode_rw != KODE_RAHASIA_PENGAWAS:
                flash('Kode Otorisasi RW salah! Anda tidak berhak mendaftar sebagai Pengawas.', 'danger')
                return redirect(url_for('auth.register'))
            is_aktif_status = True  # Pengawas langsung aktif karena memasukkan kode yang sah

        # 3. Validasi Password
        if password != konfirmasi_password:
            flash('Konfirmasi kata sandi tidak cocok!', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('Kata sandi harus minimal 8 karakter, ada huruf besar, kecil, dan angka!', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan, silakan pilih yang lain.', 'danger')
            return redirect(url_for('auth.register'))

        # 4. Simpan Akun
        user_baru = User(
            nama_lengkap=nama_lengkap,
            username=username,
            password=generate_password_hash(password),
            role=role,
            saldo_terkini=0.00,
            is_aktif=is_aktif_status
        )
        db.session.add(user_baru)
        db.session.commit()

        if role == 'pengawas':
            flash('Akun Pengawas RW berhasil didaftarkan dan langsung aktif! Silakan login.', 'success')
        else:
            flash('Pendaftaran berhasil! Akun Anda menunggu verifikasi oleh Pengawas RW.', 'warning')
            
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
    else:
        return redirect(url_for('warga.dashboard'))