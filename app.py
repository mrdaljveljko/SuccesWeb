from __future__ import annotations

import io

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
    summary = build_summary(rows)

    return jsonify(
        {
            "product": product,
            "shipping_rate": shipping_rate,
            "selling_price": selling_price,
            "summary": summary,
            "suppliers": rows_to_records(rows),
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
