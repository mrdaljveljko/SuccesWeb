from __future__ import annotations

import random
from dataclasses import asdict, dataclass

DEFAULT_SHIPPING_RATE = 120.0
DEFAULT_SELLING_PRICE = 200.0
LOCATIONS = ["Shenzhen", "Guangzhou", "Ningbo", "Yiwu", "Dongguan", "Foshan"]


@dataclass
class SupplierRow:
    product: str
    supplier: str
    price_per_unit: float
    moq: int
    production_location: str
    cbm: float
    shipping_cost: float
    landed_cost: float
    profit_per_unit: float
    profit_margin_percent: float
    product_order_cost: float
    total_investment: float
    score: float


def _seed_for_product(product: str) -> int:
    return sum(ord(char) for char in product.strip().lower())


def generate_supplier_analysis(
    product: str,
    *,
    selling_price: float = DEFAULT_SELLING_PRICE,
    shipping_rate: float = DEFAULT_SHIPPING_RATE,
) -> list[SupplierRow]:
    rng = random.Random(_seed_for_product(product))
    rows: list[SupplierRow] = []

    for idx in range(1, 6):
        price = round(rng.uniform(25, 120), 2)
        moq = rng.choice([100, 200, 300, 500, 1000])
        cbm = round(rng.uniform(0.08, 0.6), 3)

        shipping_cost = round(cbm * shipping_rate, 2)
        landed_cost = round(price + shipping_cost, 2)
        profit_per_unit = round(selling_price - landed_cost, 2)
        profit_margin_percent = round((profit_per_unit / selling_price) * 100, 2)
        product_order_cost = round(price * moq, 2)
        total_investment = round(product_order_cost + shipping_cost, 2)
        score = round(price * 0.4 + moq * 0.002 + cbm * 0.2, 4)

        rows.append(
            SupplierRow(
                product=product,
                supplier=f"Factory {idx}",
                price_per_unit=price,
                moq=moq,
                production_location=rng.choice(LOCATIONS),
                cbm=cbm,
                shipping_cost=shipping_cost,
                landed_cost=landed_cost,
                profit_per_unit=profit_per_unit,
                profit_margin_percent=profit_margin_percent,
                product_order_cost=product_order_cost,
                total_investment=total_investment,
                score=score,
            )
        )

    return rows


def build_summary(rows: list[SupplierRow]) -> dict[str, str]:
    best_price = min(rows, key=lambda row: row.price_per_unit)
    lowest_landed_cost = min(rows, key=lambda row: row.landed_cost)
    best_overall = min(rows, key=lambda row: row.score)
    highest_profit_margin = max(rows, key=lambda row: row.profit_margin_percent)

    return {
        "recommended_supplier": best_overall.supplier,
        "lowest_landed_cost_supplier": lowest_landed_cost.supplier,
        "highest_profit_margin_supplier": highest_profit_margin.supplier,
        "best_price_supplier": best_price.supplier,
    }


def rows_to_records(rows: list[SupplierRow]) -> list[dict[str, float | int | str]]:
    return [asdict(row) for row in rows]
