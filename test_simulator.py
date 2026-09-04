import unittest

from simulator import LeaderInput, LeaderMember, calculate_leader_commission, ranking_percent


class LeaderCommissionTests(unittest.TestCase):
    def test_new_ranking_percentages(self):
        self.assertEqual(ranking_percent("active_user"), 0.0)
        self.assertEqual(ranking_percent("rising_creator"), 0.05)
        self.assertEqual(ranking_percent("professional_creator"), 0.10)
        self.assertEqual(ranking_percent("senior_creator"), 0.15)
        self.assertEqual(ranking_percent("creator_leader"), 0.20)
        self.assertEqual(ranking_percent("agency_director"), 0.25)
        self.assertEqual(ranking_percent("executive_agency_director"), 0.30)


    def test_first_active_user_uses_full_leader_percent_and_rest_use_differential(self):
        simulation = {
        "rows": [
            {
                "bulan": 1,
                "tanggal": "2026-08-01",
                "pendapatan_diterima": 100_000.0,
            }
        ]
    }
        leader = LeaderInput(
            leader_name="Leader A",
            ranking="agency_director",
            jumlah_member_level_1=1,
            members=[LeaderMember("Member A", "senior_creator", 3)],
        )

        result = calculate_leader_commission(simulation, leader)

        # 1 × 25% + 2 × (25% - 15%) = 45%
        self.assertEqual(result["total_komisi_leader"], 45_000.0)
        self.assertEqual(result["member_details"][0]["komisi_leader"], 45_000.0)
        self.assertEqual(result["member_details"][0]["full_percent_active_user"], 1)
        self.assertEqual(result["member_details"][0]["differential_active_user"], 2)


    def test_formula_is_applied_separately_to_every_member(self):
        simulation = {
        "rows": [
            {
                "bulan": 1,
                "tanggal": "2026-08-01",
                "pendapatan_diterima": 100_000.0,
            }
        ]
    }
        leader = LeaderInput(
            leader_name="Leader A",
            ranking="agency_director",
            jumlah_member_level_1=2,
            members=[
                LeaderMember("Member A", "senior_creator", 1),
                LeaderMember("Member B", "professional_creator", 2),
            ],
        )

        result = calculate_leader_commission(simulation, leader)

        # Member A: 1 × 25% = 25%; Member B: 1 × 25% + 1 × 15% = 40%.
        self.assertEqual(result["total_komisi_leader"], 65_000.0)


if __name__ == "__main__":
    unittest.main()
