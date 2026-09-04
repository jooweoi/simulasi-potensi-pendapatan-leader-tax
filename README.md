# Simulasi Potensi Pendapatan Leader Tax

Versi Flask untuk simulasi potensi pendapatan, penarikan bulanan, pajak 6%, dan estimasi komisi leader.

## Ranking Leader

- Rising Creator: 5%
- Professional Creator: 10%
- Senior Creator: 15%
- Creator Leader: 20%
- Agency Director: 25%
- Executive Agency Director: 30%

## Formula Komisi Leader

Untuk setiap member Level 1:

- Active User pertama dihitung menggunakan persentase penuh ranking Leader.
- Active User kedua dan seterusnya dihitung menggunakan selisih antara persentase Leader dan persentase member.
- Selisih minimum adalah 0%; komisi tidak boleh menjadi negatif.

```text
Komisi Member = Pendapatan per User ×
  [Leader % + (Total Active User - 1) × max(Leader % - Member %, 0%)]
```

Jalankan lokal:

```bash
pip install -r requirements.txt
python app.py
```

Lalu buka `http://127.0.0.1:5002`.
