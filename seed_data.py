from flask import request, flash, redirect, url_for, render_template, session
from app.models import User, JenisSampah, Penyetoran, DetailPenyetoran
from app.extensions import db
from werkzeug.security import generate_password_hash
import random

@sekben_bp.route('/terima-setoran', methods=['GET', 'POST'])
@role_required(['sekben'])
def terima_setoran():
    if request.method == 'POST':
        nama_warga = request.form.get('nama_warga').strip()
        id_jenis_sampah = request.form.get('id_jenis_sampah')
        berat_awal = request.form.get('berat_awal')
        
        # Cek apakah warga dengan nama tersebut sudah terdaftar
        warga = User.query.filter_by(nama_lengkap=nama_warga, role='warga').first()
        
        if not warga:
            # Jika belum ada, otomatis buat akun warga baru di background
            username_generated = nama_warga.lower().replace(" ", "_") + str(random.randint(100, 999))
            warga = User(
                nama_lengkap=nama_warga,
                username=username_generated,
                password=generate_password_hash("warga123"),
                role="warga"
            )
            db.session.add(warga)
            db.session.commit() # Commit untuk menghasilkan ID warga baru
        
        # 1. Catat ke tabel Penyetoran
        penyetoran_baru = Penyetoran(id_warga=warga.id, id_sekben=session.get('user_id'))
        db.session.add(penyetoran_baru)
        db.session.flush()
        
        # 2. Catat ke tabel Detail Penyetoran
        detail_baru = DetailPenyetoran(
            id_penyetoran=penyetoran_baru.id,
            id_jenis_sampah=id_jenis_sampah,
            berat_awal=berat_awal
        )
        db.session.add(detail_baru)
        db.session.commit()
        
        flash(f'Setoran atas nama "{nama_warga}" berhasil dicatat!', 'success')
        return redirect(url_for('sekben.terima_setoran'))

    # Hanya ambil data jenis sampah untuk dropdown
    jenis_sampah_list = JenisSampah.query.all()
    return render_template('dashboard/terima_setoran.html', jenis_sampah_list=jenis_sampah_list)