# Investment Waterfall Calculator

A Streamlit web application that calculates investor returns for venture investments with liquidation preferences through a fund structure.

## Features

- **Interactive sliders** for company sale price ($0 - $1B) and management carve out (8-15%)
- **Full waterfall breakdown** from company sale to net investor proceeds
- **2x non-participating liquidation preference** with automatic comparison to pro-rata
- **Fund-level economics** with 80/20 LP/GP profit split and 2% annual management fee
- **IRR and MOIC calculations**
- **Visualizations:**
  - Waterfall chart showing how proceeds flow from sale to investor
  - Sensitivity analysis showing returns across different exit values
  - Key threshold table showing required exits for target MOICs

## Fixed Assumptions

- Post-money valuation: $80M
- Liquidation preference: 2x non-participating
- Fund profit split: 80% LP / 20% GP
- Management fee: 2% annual (of initial investment, deducted at exit)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## Usage

1. **Initial Investment**: Enter your investment amount (up to $80M)
2. **Holding Period**: Set the expected years until exit
3. **Company Sale Price**: Use the slider to model different exit scenarios
4. **Management Carve Out**: Adjust the management pool percentage (8-15%)

The calculator will automatically update all results, charts, and sensitivity analysis.

## Calculations Explained

### Company Level
1. Sale Price - Management Carve Out = Net Proceeds

### Your Share (Non-Participating Preference)
Your fund receives the **greater** of:
- **2x Liquidation Preference**: 2 × Initial Investment
- **Pro-Rata Share**: Ownership % × Net Proceeds

### Fund Waterfall
1. Gross proceeds from investment
2. Less: Management fees (2% × Initial Investment × Years)
3. Less: Return of LP capital
4. Remaining profit split 80% LP / 20% GP

### Returns
- **MOIC** = Total to Investor / Initial Investment
- **IRR** = Internal Rate of Return based on cash flow timing
