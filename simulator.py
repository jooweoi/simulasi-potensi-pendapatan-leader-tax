from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


PACKAGE_RULES = {
    "sprint": {
        "label": "Sprint (30 Hari + 30 Hari)",
        "excel_label": "Sprint (30 Hari + 30 Hari)",
        "rules": [1.0, 0.2, 0.0, 0.0, 0.0, 0.0],
    },
    "pertumbuhan": {
        "label": "Growth (60 Hari + 60 Hari)",
        "excel_label": "Growth (60 Hari + 60 Hari)",
        "rules": [0.5, 0.5, 0.25, 0.25, 0.0, 0.0],
    },
    "skala": {
        "label": "Scale (90 Hari + 90 Hari)",
        "excel_label": "Scale (90 Hari + 90 Hari)",
        "rules": [1 / 3, 1 / 3, 1 / 3, 1 / 3, 1 / 3, 1 / 3],
    },
}

MINIMUM_PURCHASE = 300_000.0
TAX_RATE = 0.06
TAX_MULTIPLIER = 1 + TAX_RATE
PURCHASE_STEP = 1_000.0
DATE_INTERVAL_DAYS = 30
DEFAULT_SIMULATION_MONTHS = 120
MAX_LEADER_MEMBERS = 200

RANKING_RULES = {
    "active_user": {"label": "Active User", "percent": 0.0},
    "trainee_creator": {"label": "Trainee Creator", "percent": 0.10},
    "content_creator": {"label": "Content Creator", "percent": 0.15},
    "senior_creator": {"label": "Senior Creator", "percent": 0.20},
    "trainee_creative_director": {"label": "Trainee Creative Director", "percent": 0.25},
    "creative_director": {"label": "Creative Director", "percent": 0.30},
}


@dataclass
class SimulationInput:
    pembelian_awal: float
    paket: str
    metode_perhitungan: str
    durasi_beli_ulang: int
    bulan_pencairan_terakhir: int
    tanggal_mulai: date
    pembelian_tambahan_bulanan: float
    durasi_pembelian_tambahan: int
    penarikan_bulanan: float


@dataclass
class LeaderMember:
    name: str
    ranking: str
    active_user: int


@dataclass
class LeaderInput:
    leader_name: str
    ranking: str
    jumlah_member_level_1: int
    members: list[LeaderMember]


def parse_date(value: str) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def package_label(package_key: str) -> str:
    return PACKAGE_RULES[package_key]["label"]


def ranking_label(ranking_key: str) -> str:
    return RANKING_RULES.get(ranking_key, RANKING_RULES["active_user"])["label"]


def ranking_percent(ranking_key: str) -> float:
    return RANKING_RULES.get(ranking_key, RANKING_RULES["active_user"])["percent"]


def get_cycle_months(package_key: str) -> int:
    cycle = 0
    for index, rule in enumerate(PACKAGE_RULES[package_key]["rules"], start=1):
        if rule > 0:
            cycle = index
    return cycle


def round_purchase_amount(value: float) -> float:
    return max(0.0, (value // PURCHASE_STEP) * PURCHASE_STEP)


def simulate(data: SimulationInput) -> dict[str, Any]:
    if data.paket not in PACKAGE_RULES:
        raise ValueError("Paket tidak tersedia.")

    cycle_months = get_cycle_months(data.paket)
    if data.metode_perhitungan == "bulan_pencairan_terakhir":
        durasi_beli_ulang = max(0, data.bulan_pencairan_terakhir - cycle_months)
        bulan_pencairan_terakhir = max(data.bulan_pencairan_terakhir, cycle_months)
    else:
        durasi_beli_ulang = max(0, data.durasi_beli_ulang)
        bulan_pencairan_terakhir = max(durasi_beli_ulang + cycle_months, cycle_months)

    rules = PACKAGE_RULES[data.paket]["rules"]
    months_to_run = max(DEFAULT_SIMULATION_MONTHS, bulan_pencairan_terakhir + 1)
    rows: list[dict[str, Any]] = []
    processed_by_month: list[float] = []
    total_pendapatan = 0.0
    sisa_pool_sebelumnya = 0.0
    pajak_tertunda = 0.0

    for bulan in range(months_to_run + 1):
        tanggal = data.tanggal_mulai + timedelta(days=bulan * DATE_INTERVAL_DAYS)
        pajak_dibayar = 0.0

        if bulan == 0:
            pendapatan_diterima = 0.0
            penarikan_bulanan = 0.0
            pembelian_tambahan = 0.0
            pool_tersedia = 0.0
            beli_ulang_diproses = data.pembelian_awal if data.pembelian_awal >= MINIMUM_PURCHASE else 0.0
            sisa_pool = 0.0
            pencairan = 0.0
            keterangan = (
                "Nominal Pembelian Awal"
                if data.pembelian_awal >= MINIMUM_PURCHASE
                else "Pembelian awal belum memenuhi syarat minimum/Silakan tingkatkan pembelian awal sesuai nominal minimum"
            )
        else:
            pendapatan_diterima = 0.0
            for jarak_bulan, faktor in enumerate(rules, start=1):
                sumber_bulan = bulan - jarak_bulan
                if sumber_bulan >= 0:
                    pendapatan_diterima += processed_by_month[sumber_bulan] * faktor

            penarikan_bulanan = min(max(0.0, data.penarikan_bulanan), pendapatan_diterima)
            pembelian_tambahan = 0.0
            if processed_by_month[0] != 0:
                if 1 <= bulan <= data.durasi_pembelian_tambahan and bulan <= durasi_beli_ulang:
                    pembelian_tambahan = data.pembelian_tambahan_bulanan
            pool_tersedia = (
                sisa_pool_sebelumnya + pendapatan_diterima + pembelian_tambahan - penarikan_bulanan
            )
            if pajak_tertunda > 0 and pool_tersedia >= pajak_tertunda:
                pajak_dibayar = pajak_tertunda
                pool_tersedia -= pajak_dibayar
                pajak_tertunda = 0.0

            beli_ulang_diproses = 0.0
            if bulan <= durasi_beli_ulang and pool_tersedia >= MINIMUM_PURCHASE:
                if pool_tersedia >= MINIMUM_PURCHASE * TAX_MULTIPLIER:
                    beli_ulang_diproses = round_purchase_amount(pool_tersedia / TAX_MULTIPLIER)
                    biaya_beli_ulang = beli_ulang_diproses * TAX_MULTIPLIER
                    sisa_pool = pool_tersedia - biaya_beli_ulang
                    pajak_dibayar += beli_ulang_diproses * TAX_RATE
                else:
                    beli_ulang_diproses = round_purchase_amount(pool_tersedia)
                    sisa_pool = pool_tersedia - beli_ulang_diproses
                    pajak_tertunda += beli_ulang_diproses * TAX_RATE
            else:
                sisa_pool = pool_tersedia if bulan <= durasi_beli_ulang else 0.0

            if bulan > durasi_beli_ulang:
                pencairan = pool_tersedia
            else:
                pencairan = 0.0
            total_pendapatan += pencairan

            if bulan > bulan_pencairan_terakhir:
                keterangan = ""
            elif bulan <= durasi_beli_ulang:
                if beli_ulang_diproses > 0:
                    keterangan = "Beli Ulang Diproses"
                elif pembelian_tambahan > 0:
                    keterangan = "Pembelian Tambahan / Menunggu Minimum"
                elif pendapatan_diterima > 0:
                    keterangan = "Menunggu Minimum"
                else:
                    keterangan = ""
            elif bulan == durasi_beli_ulang + 1:
                keterangan = "Mulai Pencairan"
            elif bulan == bulan_pencairan_terakhir:
                keterangan = "Pencairan Terakhir"
            elif pencairan > 0:
                keterangan = "Pencairan Sisa"
            else:
                    keterangan = ""

        processed_by_month.append(beli_ulang_diproses)
        sisa_pool_sebelumnya = sisa_pool

        if bulan <= bulan_pencairan_terakhir:
            rows.append(
                {
                    "bulan": bulan,
                    "tanggal": tanggal.strftime("%Y-%m-%d"),
                    "pendapatan_diterima": pendapatan_diterima,
                    "penarikan_bulanan": penarikan_bulanan,
                    "pembelian_tambahan": pembelian_tambahan,
                    "beli_ulang_diproses": beli_ulang_diproses,
                    "pajak_dibayar": pajak_dibayar,
                    "pajak_tertunda": pajak_tertunda,
                    "total_pendapatan": total_pendapatan,
                    "keterangan": keterangan,
                }
            )

    total_pembelian_tambahan = sum(row["pembelian_tambahan"] for row in rows)
    total_beli_ulang_diproses = sum(row["beli_ulang_diproses"] for row in rows)
    total_pajak = total_beli_ulang_diproses * TAX_RATE
    total_pembelian = data.pembelian_awal + total_pembelian_tambahan + total_pajak
    kelipatan = total_pendapatan / total_pembelian if total_pembelian else 0.0
    tanggal_mulai_pencairan = data.tanggal_mulai + timedelta(
        days=(durasi_beli_ulang + 1) * DATE_INTERVAL_DAYS
    )
    tanggal_pencairan_terakhir = data.tanggal_mulai + timedelta(
        days=bulan_pencairan_terakhir * DATE_INTERVAL_DAYS
    )

    return {
        "status": "Perhitungan Berhasil" if data.pembelian_awal >= MINIMUM_PURCHASE else "Pembelian awal belum memenuhi syarat minimum/Silakan tingkatkan pembelian awal sesuai nominal minimum",
        "paket": package_label(data.paket),
        "durasi_siklus": cycle_months,
        "durasi_beli_ulang": durasi_beli_ulang,
        "bulan_pencairan_terakhir": bulan_pencairan_terakhir,
        "tanggal_mulai_pencairan": tanggal_mulai_pencairan.strftime("%Y-%m-%d"),
        "tanggal_pencairan_terakhir": tanggal_pencairan_terakhir.strftime("%Y-%m-%d"),
        "total_pembelian_tambahan": total_pembelian_tambahan,
        "total_beli_ulang_diproses": total_beli_ulang_diproses,
        "total_pajak": total_pajak,
        "total_pembelian": total_pembelian,
        "total_pendapatan": total_pendapatan,
        "kelipatan_pendapatan": kelipatan,
        "rentang_simulasi": "Berikut proyeksi pendapatan berdasarkan data yang dimasukkan",
        "rows": rows,
    }


def default_leader_members() -> list[dict[str, Any]]:
    members = []
    for index in range(1, MAX_LEADER_MEMBERS + 1):
        members.append(
            {
                "no": index,
                "name": f"Member {index}" if index <= 5 else "",
                "ranking": "trainee_creator" if index <= 5 else "active_user",
                "active_user": 1 if index <= 5 else 0,
            }
        )
    return members


def calculate_leader_commission(simulation: dict[str, Any], leader: LeaderInput) -> dict[str, Any]:
    leader_percent = ranking_percent(leader.ranking)
    active_limit = max(0, min(leader.jumlah_member_level_1, MAX_LEADER_MEMBERS))
    member_details: list[dict[str, Any]] = []
    commission_factor = 0.0
    total_active_user = 0
    needs_review = False

    for index, member in enumerate(leader.members[:MAX_LEADER_MEMBERS], start=1):
        is_active = index <= active_limit
        member_name = member.name.strip()
        member_active_user = max(0, member.active_user)
        member_percent = ranking_percent(member.ranking)
        selisih_percent = max(0.0, leader_percent - member_percent)

        if is_active:
            if not member_name or member_active_user <= 0:
                status = "Lengkapi Data"
                needs_review = True
            else:
                status = "OK"
                commission_factor += member_active_user * selisih_percent
                total_active_user += member_active_user
        else:
            status = "Tidak Aktif"

        member_details.append(
            {
                "no": index,
                "name": member_name,
                "ranking": ranking_label(member.ranking),
                "active_user": member_active_user,
                "rank_percent": member_percent,
                "selisih_percent": selisih_percent if is_active else 0.0,
                "total_pendapatan_team": 0.0,
                "komisi_leader": 0.0,
                "status": status,
            }
        )

    rows: list[dict[str, Any]] = []
    total_komisi = 0.0
    total_pendapatan_member = 0.0
    for row in simulation["rows"]:
        pendapatan_per_user = row["pendapatan_diterima"]
        pendapatan_member = pendapatan_per_user * total_active_user
        komisi = pendapatan_per_user * commission_factor
        total_pendapatan_member += pendapatan_member
        total_komisi += komisi
        for detail in member_details:
            if detail["status"] == "OK":
                detail["total_pendapatan_team"] += pendapatan_per_user * detail["active_user"]
                detail["komisi_leader"] += (
                    pendapatan_per_user * detail["active_user"] * detail["selisih_percent"]
                )
        rows.append(
            {
                "bulan": row["bulan"],
                "tanggal": row["tanggal"],
                "pendapatan_per_user": pendapatan_per_user,
                "total_active_user": total_active_user,
                "total_pendapatan_member": pendapatan_member,
                "komisi_leader": komisi,
                "keterangan": (
                    "Komisi Leader"
                    if komisi > 0
                    else "Tidak ada komisi / cek selisih rank"
                    if pendapatan_per_user > 0
                    else ""
                ),
            }
        )

    return {
        "leader_name": leader.leader_name,
        "leader_ranking": ranking_label(leader.ranking),
        "leader_percent": leader_percent,
        "jumlah_member_level_1": active_limit,
        "total_active_user": total_active_user,
        "total_pendapatan_member": total_pendapatan_member,
        "total_komisi_leader": total_komisi,
        "status": "Periksa Input Member" if needs_review else "OK",
        "member_details": member_details,
        "rows": rows,
    }
