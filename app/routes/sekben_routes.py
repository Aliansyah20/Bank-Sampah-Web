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

# --- TERIMA SETORAN SAMPAH DARI WARGA (MULTI-ITEM) ---
@sekben_bp.route('/terima-setoran', methods=['GET', 'POST'])
@role_required(['sekben'])
def terima_setoran():
    if request.method == 'POST':
        id_warga = request.form.get('id_warga')
        
        # Mengambil seluruh daftar sampah yang diinput (mendukung array maupun non-array)
        list_jenis = request.form.getlist('id_jenis_sampah[]') or request.form.getlist('id_jenis_sampah')
        list_berat = request.form.getlist('berat_awal[]') or request.form.getlist('berat_awal')

        # 1. Validasi warga
        if not id_warga:
            flash('Silakan pilih warga penyetor terlebih dahulu!', 'danger')
            return redirect(url_for('sekben.terima_setoran'))

        # 2. Validasi apakah ada sampah yang diinput
        if not list_jenis or not list_berat or len(list_jenis) == 0:
            flash('Daftar rincian sampah tidak boleh kosong!', 'danger')
            return redirect(url_for('sekben.terima_setoran'))

        try:
            # Buat 1 nota induk penyetoran untuk warga tersebut
            penyetoran_baru = Penyetoran(
                id_warga=int(id_warga),
                id_sekben=session.get('user_id')
            )
            db.session.add(penyetoran_baru)
            db.session.flush()  # Ambil ID nota penyetoran

            jumlah_tersimpan = 0

            # Lakukan perulangan (loop) untuk setiap barang yang diinput
            for jenis_id, berat_str in zip(list_jenis, list_berat):
                if not jenis_id or not berat_str:
                    continue
                
                # Tangani koma desimal agar jadi titik
                berat = float(str(berat_str).strip().replace(',', '.'))
                if berat <= 0:
                    continue

                # Simpan setiap jenis sampah ke detail penyetoran
                detail = DetailPenyetoran(
                    id_penyetoran=penyetoran_baru.id,
                    id_jenis_sampah=int(jenis_id),
                    berat_awal=berat,
                    status='menunggu'
                )
                db.session.add(detail)
                jumlah_tersimpan += 1

            if jumlah_tersimpan == 0:
                db.session.rollback()
                flash('Semua kolom jenis sampah dan berat wajib diisi dengan angka yang benar!', 'danger')
                return redirect(url_for('sekben.terima_setoran'))

            db.session.commit()
            flash(f'Setoran berhasil dicatat! Sebanyak {jumlah_tersimpan} jenis sampah telah masuk ke antrean pengolah.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kendala saat menyimpan: {str(e)}', 'danger')

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