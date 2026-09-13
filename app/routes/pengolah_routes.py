import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from app.models import DetailPenyetoran
from app.extensions import db
from app.utils import role_required

pengolah_bp = Blueprint('pengolah', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def file_valid(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pengolah_bp.route('/dashboard')
@role_required(['pengolah'])
def dashboard():
    antrean = DetailPenyetoran.query.filter_by(status='menunggu').all()
    riwayat = DetailPenyetoran.query.filter(DetailPenyetoran.status.in_(['siap_jual', 'ditolak'])).order_by(DetailPenyetoran.id.desc()).limit(10).all()
    return render_template('dashboard/pengolah_dashboard.html', antrean=antrean, riwayat=riwayat)

@pengolah_bp.route('/verifikasi/<int:detail_id>', methods=['POST'])
@role_required(['pengolah'])
def verifikasi(detail_id):
    detail = DetailPenyetoran.query.get_or_404(detail_id)
    aksi = request.form.get('aksi') # 'setuju' atau 'tolak'
    foto = request.files.get('foto_bukti')

    if not foto or not file_valid(foto.filename):
        flash('Wajib melampirkan foto bukti kondisi sampah / timbangan (format jpg/png)!', 'danger')
        return redirect(url_for('pengolah.dashboard'))

    # Simpan berkas dengan nama unik
    nama_unik = f"{uuid.uuid4().hex}_{secure_filename(foto.filename)}"
    foto.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nama_unik))

    detail.foto_bukti = nama_unik
    detail.id_pengolah = session.get('user_id')

    if aksi == 'setuju':
        berat_riil = request.form.get('berat_verifikasi')
        detail.berat_verifikasi = berat_riil
        detail.status = 'siap_jual'
        flash(f'Sampah {detail.jenis_sampah.nama_jenis} disetujui (Berat: {berat_riil} Kg). Siap dijual oleh Marketing!', 'success')
    else:
        detail.alasan_tolak = request.form.get('alasan_tolak', 'Sampah tidak memenuhi standar')
        detail.status = 'ditolak'
        flash(f'Sampah {detail.jenis_sampah.nama_jenis} berhasil ditolak!', 'warning')

    db.session.commit()
    return redirect(url_for('pengolah.dashboard'))