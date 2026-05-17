from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkeyketemuinorange'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_laporan TEXT NOT NULL,
            nama_barang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            warna TEXT NOT NULL,
            lokasi TEXT NOT NULL,
            tanggal TEXT NOT NULL,
            ciri_khusus TEXT,
            foto TEXT,
            status TEXT DEFAULT 'Menunggu'
        )
    ''')
    conn.commit()
    conn.close()

def hitung_matching_score(item_baru, item_lama):
    skor = 0
    if item_baru['nama_barang'].lower() in item_lama['nama_barang'].lower() or item_lama['nama_barang'].lower() in item_baru['nama_barang'].lower():
        skor += 30
    if item_baru['kategori'].lower() == item_lama['kategori'].lower():
        skor += 20
    if item_baru['warna'].lower() == item_lama['warna'].lower():
        skor += 20
    if item_baru['lokasi'].lower() == item_lama['lokasi'].lower():
        skor += 15
    return skor

@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY id_barang DESC').fetchall()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/lapor', methods=('GET', 'POST'))
def lapor():
    if request.method == 'POST':
        jenis_laporan = request.form['jenis_laporan']
        nama_barang = request.form['nama_barang']
        kategori = request.form['kategori']
        warna = request.form['warna']
        lokasi = request.form['lokasi']
        tanggal = request.form['tanggal']
        ciri_khusus = request.form['ciri_khusus']
        foto_barang = request.form.get('foto_barang')

        item_baru = {
            'jenis_laporan': jenis_laporan, 'nama_barang': nama_barang,
            'kategori': kategori, 'warna': warna, 'lokasi': lokasi
        }

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (jenis_laporan, nama_barang, kategori, warna, lokasi, tanggal, ciri_khusus, foto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (jenis_laporan, nama_barang, kategori, warna, lokasi, tanggal, ciri_khusus, foto_barang))
        conn.commit()
        
        id_baru = cursor.lastrowid
        jenis_lawan = 'Barang Temuan' if jenis_laporan == 'Barang Hilang' else 'Barang Hilang'
        data_lawan = conn.execute('SELECT * FROM items WHERE jenis_laporan = ? AND id_barang != ?', (jenis_lawan, id_baru)).fetchall()

        match_terbanyak = None
        skor_tertinggi = 0

        for lawan in data_lawan:
            skor = hitung_matching_score(item_baru, lawan)
            if skor > skor_tertinggi:
                skor_tertinggi = skor
                match_terbanyak = lawan

        conn.close()

        if skor_tertinggi >= 70:
            flash(f"🚨 KECOCOKAN TINGGI ({skor_tertinggi}%)! Terdeteksi mirip dengan '{match_terbanyak['nama_barang']}' di {match_terbanyak['lokasi']}.", "success")
        elif 40 <= skor_tertinggi < 70:
            flash(f"⚠️ KECOCOKAN SEDANG ({skor_tertinggi}%)! Ada kandidat mirip: '{match_terbanyak['nama_barang']}'.", "warning")
        else:
            flash("✨ Laporan berhasil disimpan ke database!", "info")

        return redirect(url_for('index'))

    return render_template('lapor.html')

if __name__ == '__main__':
    init_db()
    # Host '0.0.0.0' membuat server Flask bisa diakses dari perangkat lain
    app.run(host='0.0.0.0', port=5000, debug=True)