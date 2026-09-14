from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from app.models import User, JenisSampah, Penyetoran, DetailPenyetoran
from app.extensions import db
from app.utils import role_required

sekben_bp = Blueprint('sekben', __name__)

# --- DASHBOARD UTAMA SEKBEN ---
@sekben_bp.route('/dashboard')
@role_required(['sekben'])
def dashboard():

    # Ambil user yang sedang login
    user = User.query.filter_by(
        id=session.get('user_id')
    ).first()

    # 1. Ambil data statistik ringkas
    total_warga = User.query.filter_by(role='warga').count()
    total_jenis = JenisSampah.query.count()
    total_setoran = Penyetoran.query.count()
    menunggu_verifikasi = DetailPenyetoran.query.filter_by(status='menunggu').count()

    # 2. Ambil 5 setoran terakhir untuk tabel riwayat
    riwayat_terbaru = (
        DetailPenyetoran.query
        .order_by(DetailPenyetoran.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashboard/sekben_dashboard.html',
        user=user,
        total_warga=total_warga,
        total_jenis=total_jenis,
        total_setoran=total_setoran,
        menunggu_verifikasi=menunggu_verifikasi,
        riwayat_terbaru=riwayat_terbaru
    )

# --- TERIMA SETORAN SAMPAH DARI WARGA ---
# --- TERIMA SETORAN SAMPAH DARI WARGA ---
@sekben_bp.route('/terima-setoran', methods=['GET', 'POST'])
@role_required(['sekben'])
def terima_setoran():
    if request.method == 'POST':
        id_warga = request.form.get('id_warga')
        id_jenis_sampah = request.form.get('id_jenis_sampah')
        berat_awal_raw = request.form.get('berat_awal', '').strip()

        # 1. Validasi input tidak boleh kosong
        if not id_warga or not id_jenis_sampah or not berat_awal_raw:
            flash('Semua kolom wajib diisi!', 'danger')
            return redirect(url_for('sekben.terima_setoran'))

        # 2. Tangani tanda koma agar menjadi titik desimal
        try:
            berat_awal = float(berat_awal_raw.replace(',', '.'))
            if berat_awal <= 0:
                flash('Berat sampah harus lebih besar dari 0 Kg!', 'danger')
                return redirect(url_for('sekben.terima_setoran'))
        except ValueError:
            flash('Format berat sampah tidak valid! Masukkan angka yang benar.', 'danger')
            return redirect(url_for('sekben.terima_setoran'))

        # 3. Simpan ke database dengan proteksi rollback jika terjadi kendala
        try:
            penyetoran_baru = Penyetoran(
                id_warga=int(id_warga), 
                id_sekben=session.get('user_id')
            )
            db.session.add(penyetoran_baru)
            db.session.flush()

            detail_baru = DetailPenyetoran(
                id_penyetoran=penyetoran_baru.id,
                id_jenis_sampah=int(id_jenis_sampah),
                berat_awal=berat_awal
            )
            db.session.add(detail_baru)
            db.session.commit()

            flash('Setoran berhasil dicatat dan masuk ke antrean pengolah!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan setoran: {str(e)}', 'danger')

        return redirect(url_for('sekben.terima_setoran'))

    warga_list = User.query.filter_by(role='warga').order_by(User.nama_lengkap.asc()).all()
    jenis_sampah_list = JenisSampah.query.order_by(JenisSampah.nama_jenis.asc()).all()
    return render_template('dashboard/terima_setoran.html', warga_list=warga_list, jenis_sampah_list=jenis_sampah_list)

# --- KELOLA MASTER JENIS SAMPAH ---
@sekben_bp.route('/jenis-sampah', methods=['GET', 'POST'])
@role_required(['sekben'])
def kelola_jenis_sampah():
    if request.method == 'POST':
        nama_jenis = request.form.get('nama_jenis', '').strip()
        if nama_jenis:
            sampah_baru = JenisSampah(nama_jenis=nama_jenis)
            db.session.add(sampah_baru)
            db.session.commit()
            flash(f'Jenis sampah "{nama_jenis}" berhasil ditambahkan!', 'success')
            return redirect(url_for('sekben.kelola_jenis_sampah'))

    daftar_sampah = JenisSampah.query.order_by(JenisSampah.id.desc()).all()
    return render_template('dashboard/kelola_jenis_sampah.html', daftar_sampah=daftar_sampah)

# --- DAFTAR WARGA (HANYA MONITORING DATA) ---
@sekben_bp.route('/warga')
@role_required(['sekben'])
def kelola_warga():
    daftar_warga = User.query.filter_by(role='warga').order_by(User.id.desc()).all()
    return render_template('dashboard/kelola_warga.html', daftar_warga=daftar_warga)