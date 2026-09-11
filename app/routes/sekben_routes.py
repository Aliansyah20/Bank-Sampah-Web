from werkzeug.security import generate_password_hash

# --- KELOLA JENIS SAMPAH SECARA MANUAL ---
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


# --- KELOLA DATA WARGA SECARA MANUAL ---
@sekben_bp.route('/warga', methods=['GET', 'POST'])
@role_required(['sekben'])
def kelola_warga():
    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validasi username agar tidak dobel
        user_exist = User.query.filter_by(username=username).first()
        if user_exist:
            flash(f'Username "{username}" sudah dipakai! Gunakan username lain.', 'danger')
        elif nama_lengkap and username and password:
            warga_baru = User(
                nama_lengkap=nama_lengkap,
                username=username,
                password=generate_password_hash(password),
                role='warga'
            )
            db.session.add(warga_baru)
            db.session.commit()
            flash(f'Warga "{nama_lengkap}" berhasil didaftarkan!', 'success')
            return redirect(url_for('sekben.kelola_warga'))

    daftar_warga = User.query.filter_by(role='warga').order_by(User.id.desc()).all()
    return render_template('dashboard/kelola_warga.html', daftar_warga=daftar_warga)