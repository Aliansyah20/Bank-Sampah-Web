from .extensions import db # Mengambil instance db dari extensions.py
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('warga', 'sekben', 'pengolah', 'pemasaran'), nullable=False)
    saldo_terkini = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship untuk mempermudah pemanggilan data
    mutasi = db.relationship('MutasiSaldo', backref='user', lazy=True)

class JenisSampah(db.Model):
    __tablename__ = 'jenis_sampah'
    
    id = db.Column(db.Integer, primary_key=True)
    nama_jenis = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship ke detail penyetoran
    detail_penyetoran = db.relationship('DetailPenyetoran', backref='jenis_sampah', lazy=True)

class Penyetoran(db.Model):
    __tablename__ = 'penyetoran'
    
    id = db.Column(db.Integer, primary_key=True)
    id_warga = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_sekben = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    waktu_setor = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Karena ada 2 foreign key ke tabel users, kita harus spesifikasikan foreign_keys-nya
    warga = db.relationship('User', foreign_keys=[id_warga], backref='penyetoran_warga')
    sekben = db.relationship('User', foreign_keys=[id_sekben], backref='penyetoran_sekben')
    
    # Satu penyetoran bisa terdiri dari banyak detail (botol, kardus, dll)
    details = db.relationship('DetailPenyetoran', backref='penyetoran', lazy=True)

class PenjualanPengepul(db.Model):
    __tablename__ = 'penjualan_pengepul'
    
    id = db.Column(db.Integer, primary_key=True)
    id_pemasaran = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_sekben = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_jenis_sampah = db.Column(db.Integer, db.ForeignKey('jenis_sampah.id'), nullable=False)
    total_berat = db.Column(db.Numeric(8, 2), nullable=False)
    total_uang = db.Column(db.Numeric(12, 2), nullable=False)
    waktu_jual = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    pemasaran = db.relationship('User', foreign_keys=[id_pemasaran])
    sekben = db.relationship('User', foreign_keys=[id_sekben])
    jenis = db.relationship('JenisSampah')
    
    # Relasi balik ke detail penyetoran (untuk mengetahui detail mana saja yang ikut dijual di kloter ini)
    detail_penyetoran = db.relationship('DetailPenyetoran', backref='penjualan', lazy=True)

class DetailPenyetoran(db.Model):
    __tablename__ = 'detail_penyetoran'
    
    id = db.Column(db.Integer, primary_key=True)
    id_penyetoran = db.Column(db.Integer, db.ForeignKey('penyetoran.id'), nullable=False)
    id_jenis_sampah = db.Column(db.Integer, db.ForeignKey('jenis_sampah.id'), nullable=False)
    berat_awal = db.Column(db.Numeric(8, 2), nullable=False)
    berat_verifikasi = db.Column(db.Numeric(8, 2), default=0.00)
    
    id_pengolah = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Enum('menunggu', 'terverifikasi', 'terjual'), default='menunggu')
    id_penjualan = db.Column(db.Integer, db.ForeignKey('penjualan_pengepul.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    pengolah = db.relationship('User', foreign_keys=[id_pengolah])

class MutasiSaldo(db.Model):
    __tablename__ = 'mutasi_saldo'
    
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_penjualan = db.Column(db.Integer, db.ForeignKey('penjualan_pengepul.id'), nullable=True)
    jenis_mutasi = db.Column(db.Enum('masuk', 'keluar'), nullable=False)
    nominal = db.Column(db.Numeric(12, 2), nullable=False)
    keterangan = db.Column(db.Text)
    waktu_mutasi = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    penjualan = db.relationship('PenjualanPengepul')