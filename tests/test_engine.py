import unittest

from sourceai_engine import build_summary, generate_supplier_analysis


class SourceAIEngineTests(unittest.TestCase):
    def test_generates_five_suppliers(self):
        rows = generate_supplier_analysis("LED lamp")
        self.assertEqual(len(rows), 5)
        self.assertEqual([row.supplier for row in rows], [f"Factory {i}" for i in range(1, 6)])

    def test_is_deterministic_by_product(self):
        first = generate_supplier_analysis("LED lamp", selling_price=250, shipping_rate=140)
        second = generate_supplier_analysis("LED lamp", selling_price=250, shipping_rate=140)
        self.assertEqual(first, second)

    def test_calculation_formulas_use_input_values(self):
        selling_price = 280
        shipping_rate = 95
        row = generate_supplier_analysis("Desk fan", selling_price=selling_price, shipping_rate=shipping_rate)[0]

        self.assertEqual(row.shipping_cost, round(row.cbm * shipping_rate, 2))
        self.assertEqual(row.landed_cost, round(row.price_per_unit + row.shipping_cost, 2))
        self.assertEqual(row.profit_per_unit, round(selling_price - row.landed_cost, 2))
        self.assertEqual(row.profit_margin_percent, round((row.profit_per_unit / selling_price) * 100, 2))
        self.assertEqual(row.product_order_cost, round(row.price_per_unit * row.moq, 2))
        self.assertEqual(row.total_investment, round(row.product_order_cost + row.shipping_cost, 2))
        self.assertEqual(row.score, round(row.price_per_unit * 0.4 + row.moq * 0.002 + row.cbm * 0.2, 4))

    def test_summary_picks_valid_suppliers(self):
        rows = generate_supplier_analysis("Coffee grinder", selling_price=200, shipping_rate=120)
        summary = build_summary(rows)

        supplier_names = {row.supplier for row in rows}
        self.assertIn(summary["recommended_supplier"], supplier_names)
        self.assertIn(summary["lowest_landed_cost_supplier"], supplier_names)
        self.assertIn(summary["highest_profit_margin_supplier"], supplier_names)
        self.assertIn(summary["best_price_supplier"], supplier_names)


if __name__ == "__main__":
    unittest.main()
