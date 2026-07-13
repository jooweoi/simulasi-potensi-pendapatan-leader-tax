from __future__ import annotations

from flask import Flask, render_template, request

from simulator import (
    MAX_LEADER_MEMBERS,
    PACKAGE_RULES,
    RANKING_RULES,
    LeaderInput,
    LeaderMember,
    SimulationInput,
    calculate_leader_commission,
    default_leader_members,
    parse_date,
    simulate,
)


app = Flask(__name__)


def to_float(value: str, default: float = 0.0) -> float:
    cleaned = (value or "").replace(",", "").strip()
    return float(cleaned) if cleaned else default


def to_int(value: str, default: int = 0) -> int:
    cleaned = (value or "").replace(",", "").strip()
    return int(float(cleaned)) if cleaned else default


def simulation_input_from_form(form) -> SimulationInput:
    return SimulationInput(
        pembelian_awal=to_float(form.get("pembelian_awal", "")),
        paket=form.get("paket", "sprint"),
        metode_perhitungan=form.get("metode_perhitungan", "durasi_beli_ulang"),
        durasi_beli_ulang=to_int(form.get("durasi_beli_ulang", "")),
        bulan_pencairan_terakhir=to_int(form.get("bulan_pencairan_terakhir", "")),
        tanggal_mulai=parse_date(form.get("tanggal_mulai", "")),
        pembelian_tambahan_bulanan=to_float(form.get("pembelian_tambahan_bulanan", "")),
        durasi_pembelian_tambahan=to_int(form.get("durasi_pembelian_tambahan", "")),
        penarikan_bulanan=to_float(form.get("penarikan_bulanan", "")),
    )


def simulation_hidden_values(data: SimulationInput) -> dict[str, str]:
    return {
        "pembelian_awal": str(int(data.pembelian_awal)),
        "paket": data.paket,
        "metode_perhitungan": data.metode_perhitungan,
        "durasi_beli_ulang": str(data.durasi_beli_ulang),
        "bulan_pencairan_terakhir": str(data.bulan_pencairan_terakhir),
        "tanggal_mulai": data.tanggal_mulai.strftime("%Y-%m-%d"),
        "pembelian_tambahan_bulanan": str(int(data.pembelian_tambahan_bulanan)),
        "durasi_pembelian_tambahan": str(data.durasi_pembelian_tambahan),
        "penarikan_bulanan": str(int(data.penarikan_bulanan)),
    }


def leader_input_from_form(form) -> LeaderInput:
    members = []
    for index in range(1, MAX_LEADER_MEMBERS + 1):
        members.append(
            LeaderMember(
                name=form.get(f"member_name_{index}", ""),
                ranking=form.get(f"member_ranking_{index}", "active_user"),
                active_user=to_int(form.get(f"member_active_user_{index}", "")),
            )
        )
    return LeaderInput(
        leader_name=form.get("leader_name", "Leader A").strip() or "Leader A",
        ranking=form.get("leader_ranking", "creative_director"),
        jumlah_member_level_1=to_int(form.get("jumlah_member_level_1", "")),
        members=members,
    )


def leader_hidden_values(leader_data: LeaderInput) -> dict[str, str]:
    values = {
        "leader_name": leader_data.leader_name,
        "leader_ranking": leader_data.ranking,
        "jumlah_member_level_1": str(leader_data.jumlah_member_level_1),
    }
    for index, member in enumerate(leader_data.members, start=1):
        values[f"member_name_{index}"] = member.name
        values[f"member_ranking_{index}"] = member.ranking
        values[f"member_active_user_{index}"] = str(member.active_user)
    return values


@app.route("/", methods=["GET"])
def index():
    defaults = {
        "pembelian_awal": 300000,
        "paket": "sprint",
        "metode_perhitungan": "bulan_pencairan_terakhir",
        "durasi_beli_ulang": 1,
        "bulan_pencairan_terakhir": 12,
        "tanggal_mulai": "2026-07-01",
        "pembelian_tambahan_bulanan": 300000,
        "durasi_pembelian_tambahan": 0,
        "penarikan_bulanan": 0,
    }
    return render_template("index.html", packages=PACKAGE_RULES, defaults=defaults)


@app.route("/hasil", methods=["POST"])
def hasil():
    form = request.form
    data = simulation_input_from_form(form)
    result = simulate(data)
    return render_template("hasil.html", data=data, result=result, hidden=simulation_hidden_values(data))


@app.route("/leader", methods=["POST"])
def leader():
    form = request.form
    data = simulation_input_from_form(form)
    if "leader_name" in form:
        leader_data = leader_input_from_form(form)
        members = [
            {
                "no": index,
                "name": member.name,
                "ranking": member.ranking,
                "active_user": member.active_user,
            }
            for index, member in enumerate(leader_data.members, start=1)
        ]
        defaults = {
            "leader_name": leader_data.leader_name,
            "leader_ranking": leader_data.ranking,
            "jumlah_member_level_1": leader_data.jumlah_member_level_1,
        }
    else:
        members = default_leader_members()
        defaults = {
            "leader_name": "Leader A",
            "leader_ranking": "creative_director",
            "jumlah_member_level_1": 5,
        }
    return render_template(
        "leader.html",
        hidden=simulation_hidden_values(data),
        rankings=RANKING_RULES,
        members=members,
        defaults=defaults,
    )


@app.route("/komisi-leader", methods=["POST"])
def komisi_leader():
    data = simulation_input_from_form(request.form)
    simulation = simulate(data)
    leader_data = leader_input_from_form(request.form)
    result = calculate_leader_commission(simulation, leader_data)
    return render_template(
        "komisi_leader.html",
        simulation=simulation,
        leader=result,
        hidden=simulation_hidden_values(data),
        leader_hidden=leader_hidden_values(leader_data),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=False)
