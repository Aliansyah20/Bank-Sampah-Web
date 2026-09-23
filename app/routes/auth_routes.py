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
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()

        # 1. Kunci agar role warga tidak bisa didaftarkan dari luar
        if role not in ['sekben', 'pengolah', 'marketing']:
            flash('Pendaftaran warga hanya dapat dilakukan secara terpusat oleh Sekben!', 'danger')
            return redirect(url_for('auth.register'))

        # 2. Validasi kekuatan kata sandi (Min. 8 karakter, huruf besar, huruf kecil, dan angka)
        if len(password) < 8:
            flash('Kata sandi terlalu pendek! Minimal 8 karakter.', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[A-Z]', password):
            flash('Kata sandi wajib mengandung minimal satu huruf kapital (A-Z)!', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[a-z]', password):
            flash('Kata sandi wajib mengandung minimal satu huruf kecil (a-z)!', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'\d', password):
            flash('Kata sandi wajib mengandung minimal satu angka (0-9)!', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan, silakan pilih username lain!', 'danger')
            return redirect(url_for('auth.register'))

        # Buat akun petugas (is_aktif=False menunggu verifikasi Pengawas)
        petugas_baru = User(
            nama_lengkap=nama_lengkap,
            username=username,
            password=generate_password_hash(password),
            role=role,
            saldo_terkini=0.00,
            is_aktif=False
        )
        db.session.add(petugas_baru)
        db.session.commit()

        flash('Pendaftaran berhasil! Akun petugas Anda sedang menunggu persetujuan Pengawas RW sebelum dapat masuk.', 'warning')
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