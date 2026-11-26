# 💰 Personal Finance Dashboard

A Streamlit app that turns a bank-statement CSV into an interactive dashboard:
auto-categorized spending, budgets, income tracking, and spending insights.

## ✨ Features

- 📂 Upload a bank statement CSV (or try the built-in demo data)
- 🏷️ Keyword-based auto-categorization that **learns** when you re-categorize a transaction
- 📊 Charts: expenses by category, monthly income vs. expenses, category trends, top merchants, cumulative spend
- 🎯 Monthly budgets per category with progress bars and over-budget alerts
- 💡 Auto-generated insights (biggest category, month-over-month change, largest expense)
- ⬇️ Export categorized expenses to CSV

## 🚀 Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/advikaaasingh19-lgtm/personal-finance-dashboard.git
cd personal-finance-dashboard

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run finance_app.py
```

## 📄 CSV Format

| Column         | Example        | Notes                                                    |
|----------------|----------------|----------------------------------------------------------|
| `Date`         | `05 Nov 2026`  | `DD Mon YYYY` (falls back to flexible day-first parsing) |
| `Details`      | `SWIGGY ORDER` | Merchant / description                                   |
| `Amount`       | `1,250.00`     | Commas are handled                                       |
| `Debit/Credit` | `Debit`        | `Debit` or `Credit`                                      |

## 🏷️ Categories

Categories live in `categories.json` as `"Category": ["keyword1", "keyword2"]`.
Matching is case-insensitive and uses *contains* logic.

```json
{
  "Uncategorized": [],
  "travel": ["ETIHAD AIRWAYS"]
}
```

## 🗂️ Project Structure

```
finance_app.py     # Streamlit app
categories.json    # Category → keywords mapping
budgets.json       # Auto-generated when you save budgets (git-ignored)
requirements.txt   # Python dependencies
```

## 🛠️ Tech Stack

Python · Streamlit · Pandas · NumPy · Plotly

## 🔒 Privacy

All data is processed locally. Don't commit real bank statements.

## 📜 License

MIT
