# SourceAI

SourceAI is an AI-assisted sourcing and supplier analysis web application for products sourced from China.

## Features

- User input fields for:
  - Product name
  - Selling price
  - Shipping rate per CBM
- Auto-generated list of 5 suppliers (`Factory 1` to `Factory 5`)
- Core sourcing calculations:
  - Shipping cost (`CBM * user shipping rate`)
  - Landed cost (`price + shipping`)
  - Profit per unit and profit margin (`using user selling price`)
  - Product order cost and total investment
  - Supplier score (`price*0.4 + moq*0.002 + cbm*0.2`)
- Summary recommendations:
  - Recommended supplier (best score)
  - Lowest landed cost supplier
  - Highest profit margin supplier
  - Best price supplier
- Export to `sourcing_catalog.xlsx` with:
  - `Supplier Analysis` sheet
  - `Summary` sheet

## Tech

- Python
- Flask
- Pandas

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:8000`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
