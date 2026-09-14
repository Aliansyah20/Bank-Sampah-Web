import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from app.models import DetailPenyetoran, JenisSampah
from app.extensions import db
from app.utils import role_required

pengolah_bp = Blueprint('pengolah', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def file_valid(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pengolah_bp.route('/dashboard')
@role_required(['pengolah'])
def dashboard():
    # Daftar antrean sampah yang menunggu verifikasi fisik
    antrean = DetailPenyetoran.query.filter_by(status='menunggu').order_by(DetailPenyetoran.id.asc()).all()
    
    # Riwayat 15 sampah yang sudah selesai diverifikasi
    riwayat = DetailPenyetoran.query.filter(
        DetailPenyetoran.status.in_(['siap_jual', 'terjual'])
    ).order_by(DetailPenyetoran.id.desc()).limit(15).all()

    # Ambil master jenis sampah untuk opsi koreksi jenis jika Sekben salah input
    jenis_sampah_list = JenisSampah.query.order_by(JenisSampah.nama_jenis.asc()).all()

    return render_template(
        'dashboard/pengolah_dashboard.html',
        antrean=antrean,
        riwayat=riwayat,
        jenis_sampah_list=jenis_sampah_list
    )

@pengolah_bp.route('/verifikasi/<int:detail_id>', methods=['POST'])
@role_required(['pengolah'])
def verifikasi(detail_id):
    detail = DetailPenyetoran.query.get_or_404(detail_id)
    
    id_jenis_koreksi = request.form.get('id_jenis_sampah')
    berat_input = request.form.get('berat_verifikasi', '').strip().replace(',', '.')
    foto = request.files.get('foto_bukti')

    # 1. Validasi foto bukti fisik
    if not foto or not file_valid(foto.filename):
        flash('Wajib melampirkan foto bukti fisik timbangan (format: jpg, png, webp)!', 'danger')
        return redirect(url_for('pengolah.dashboard'))

    # 2. Validasi batas timbangan sampah (Minimal 0.1 Kg & Maksimal 300 Kg per kantong)
    try:
        berat_riil = float(berat_input)
        if berat_riil < 0.1:
            flash('Batas minimal timbangan adalah 0.1 Kg!', 'danger')
            return redirect(url_for('pengolah.dashboard'))
        if berat_riil > 300.0:
            flash('Batas maksimal timbangan per kantong adalah 300 Kg! Jika lebih, pisahkan setoran.', 'danger')
            return redirect(url_for('pengolah.dashboard'))
    except ValueError:
        flash('Format berat timbangan tidak valid! Masukkan angka yang sesuai.', 'danger')
        return redirect(url_for('pengolah.dashboard'))

    # 3. Simpan file foto bukti ke folder upload
    nama_unik = f"{uuid.uuid4().hex}_{secure_filename(foto.filename)}"
    folder_upload = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads', 'bukti'))
    os.makedirs(folder_upload, exist_ok=True)
    foto.save(os.path.join(folder_upload, nama_unik))

    # 4. Simpan hasil verifikasi & pembaruan data
    if id_jenis_koreksi:
        detail.id_jenis_sampah = int(id_jenis_koreksi)

    detail.berat_verifikasi = berat_riil
    detail.foto_bukti = nama_unik
    detail.id_pengolah = session.get('user_id')
    detail.status = 'siap_jual'

    db.session.commit()
    flash(f'Sampah {detail.jenis_sampah.nama_jenis} berhasil diverifikasi ({berat_riil} Kg) dan masuk ke status Siap Jual.', 'success')
    return redirect(url_for('pengolah.dashboard'))