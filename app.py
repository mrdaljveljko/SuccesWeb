from __future__ import annotations

import io
import random
from dataclasses import asdict, dataclass

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from sourceai_engine import (
    DEFAULT_SELLING_PRICE,
    DEFAULT_SHIPPING_RATE,
    build_summary,
    generate_supplier_analysis,
    rows_to_records,
)

app = Flask(__name__)


def _parse_positive_number(raw_value: object, field_name: str) -> tuple[float | None, str | None]:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid number."

    if value <= 0:
        return None, f"{field_name} must be greater than 0."

    return value, None


def rows_to_dataframes(rows: list, summary: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    analysis_df = pd.DataFrame(rows_to_records(rows)).rename(
        columns={
            "product": "Product",
            "supplier": "Supplier",
            "price_per_unit": "Price per unit",
            "moq": "MOQ",
            "production_location": "Production location",
            "cbm": "CBM",
            "shipping_cost": "Shipping cost",
            "landed_cost": "Landed cost",
            "profit_per_unit": "Profit per unit",
            "profit_margin_percent": "Profit margin %",
            "product_order_cost": "Product order cost",
            "total_investment": "Total investment",
            "score": "Score",
        }
    )

app = Flask(__name__)

DEFAULT_SHIPPING_RATE = 120
DEFAULT_SELLING_PRICE = 200

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
    return sum(ord(c) for c in product.strip().lower())


def generate_supplier_analysis(product: str) -> list[SupplierRow]:
    rng = random.Random(_seed_for_product(product))
    rows: list[SupplierRow] = []

    for idx in range(1, 6):
        price = round(rng.uniform(25, 120), 2)
        moq = rng.choice([100, 200, 300, 500, 1000])
        cbm = round(rng.uniform(0.08, 0.6), 3)
        shipping_cost = round(cbm * DEFAULT_SHIPPING_RATE, 2)
        landed_cost = round(price + shipping_cost, 2)
        profit_per_unit = round(DEFAULT_SELLING_PRICE - landed_cost, 2)
        profit_margin = round((profit_per_unit / DEFAULT_SELLING_PRICE) * 100, 2)
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
                profit_margin_percent=profit_margin,
                product_order_cost=product_order_cost,
                total_investment=total_investment,
                score=score,
            )
        )

    return rows


def build_summary(rows: list[SupplierRow]) -> dict[str, str]:
    best_price = min(rows, key=lambda r: r.price_per_unit)
    lowest_landed = min(rows, key=lambda r: r.landed_cost)
    best_overall = min(rows, key=lambda r: r.score)
    highest_profit_margin = max(rows, key=lambda r: r.profit_margin_percent)

    return {
        "recommended_supplier": best_overall.supplier,
        "lowest_landed_cost_supplier": lowest_landed.supplier,
        "highest_profit_margin_supplier": highest_profit_margin.supplier,
        "best_price_supplier": best_price.supplier,
    }


def rows_to_dataframes(rows: list[SupplierRow], summary: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    analysis_df = pd.DataFrame(asdict(r) for r in rows)
    summary_df = pd.DataFrame(
        {
            "Metric": [
                "Recommended Supplier",
                "Lowest Landed Cost Supplier",
                "Highest Profit Margin Supplier",
                "Best Price Supplier",
            ],
            "Value": [
                summary["recommended_supplier"],
                summary["lowest_landed_cost_supplier"],
                summary["highest_profit_margin_supplier"],
                summary["best_price_supplier"],
            ],
        }
    )
    return analysis_df, summary_df


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_selling_price=DEFAULT_SELLING_PRICE,
        default_shipping_rate=DEFAULT_SHIPPING_RATE,
    )
    return render_template("index.html")


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    product = str(payload.get("product", "")).strip()

    if not product:
        return jsonify({"error": "Product is required."}), 400

    selling_price, selling_price_error = _parse_positive_number(payload.get("selling_price"), "Selling price")
    if selling_price_error:
        return jsonify({"error": selling_price_error}), 400

    shipping_rate, shipping_rate_error = _parse_positive_number(payload.get("shipping_rate"), "Shipping rate per CBM")
    if shipping_rate_error:
        return jsonify({"error": shipping_rate_error}), 400

    rows = generate_supplier_analysis(product, selling_price=selling_price, shipping_rate=shipping_rate)
    rows = generate_supplier_analysis(product)
    summary = build_summary(rows)

    return jsonify(
        {
            "product": product,
            "shipping_rate": shipping_rate,
            "selling_price": selling_price,
            "summary": summary,
            "suppliers": rows_to_records(rows),
            "shipping_rate": DEFAULT_SHIPPING_RATE,
            "selling_price": DEFAULT_SELLING_PRICE,
            "summary": summary,
            "suppliers": [asdict(row) for row in rows],
        }
    )


@app.get("/api/export")
def export_excel():
    product = request.args.get("product", "").strip()
    if not product:
        return jsonify({"error": "Product query parameter is required."}), 400

    selling_price, selling_price_error = _parse_positive_number(request.args.get("selling_price"), "Selling price")
    if selling_price_error:
        return jsonify({"error": selling_price_error}), 400

    shipping_rate, shipping_rate_error = _parse_positive_number(request.args.get("shipping_rate"), "Shipping rate per CBM")
    if shipping_rate_error:
        return jsonify({"error": shipping_rate_error}), 400

    rows = generate_supplier_analysis(product, selling_price=selling_price, shipping_rate=shipping_rate)
    rows = generate_supplier_analysis(product)
    summary = build_summary(rows)
    analysis_df, summary_df = rows_to_dataframes(rows, summary)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        analysis_df.to_excel(writer, index=False, sheet_name="Supplier Analysis")
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="sourcing_catalog.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
