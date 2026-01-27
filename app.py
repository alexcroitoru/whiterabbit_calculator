"""
Investment Waterfall Calculator
Calculates investor returns based on liquidation preferences and fund economics
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

# Page configuration
st.set_page_config(
    page_title="Investment Waterfall Calculator",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("Investment Waterfall Calculator")
st.markdown("""
Calculate your expected returns on a venture investment with **2x non-participating liquidation preference** 
through a fund structure with 80/20 profit split.
""")

st.divider()

# Sidebar for fixed assumptions
with st.sidebar:
    st.header("Fixed Assumptions")
    st.markdown("""
    - **Fund Size:** $10M
    - **Post-Money Valuation:** $80M
    - **Liquidation Preference:** 2x Non-Participating
    - **Fund Profit Split:** 80% LP / 20% GP
    - **Management Fee:** 2% annual (of initial investment)
    """)
    
    st.divider()
    st.markdown("### How It Works")
    st.markdown("""
    1. **Exit Proceeds** = Sale Price - Management Carve Out
    2. **Your Share** = Greater of:
       - 2x your investment (Liq Pref), OR
       - Your pro-rata ownership %
    3. **Fund Waterfall:**
       - Deduct management fees
       - Return your capital
       - Split remaining profits 80/20
    """)

# Constants
POST_MONEY_VALUATION = 80_000_000  # $80M

# Main input section
st.header("Input Parameters")

col1, col2 = st.columns(2)

with col1:
    initial_investment_mm = st.number_input(
        "Initial Investment ($M)",
        min_value=0.01,
        max_value=10.0,
        value=2.0,
        step=0.1,
        format="%.2f",
        help="Your investment amount in millions at the $80M post-money valuation (max $10M fund size)"
    )
    initial_investment = initial_investment_mm * 1_000_000
    
    holding_period = st.number_input(
        "Holding Period (Years)",
        min_value=1,
        max_value=15,
        value=2,
        step=1,
        help="Expected time until exit event"
    )

with col2:
    sale_price_mm = st.slider(
        "Company Sale Price ($M)",
        min_value=25,
        max_value=1000,
        value=200,
        step=25,
        format="%dM",
        help="Total exit/sale price of the company in millions"
    )
    sale_price = sale_price_mm * 1_000_000
    
    carve_out_pct = st.slider(
        "Management Carve Out (%)",
        min_value=8.0,
        max_value=15.0,
        value=10.0,
        step=0.5,
        format="%.1f%%",
        help="Percentage of sale price allocated to management team"
    )

st.divider()

# Calculations
def calculate_waterfall(initial_investment, sale_price, carve_out_pct, holding_period, post_money_val):
    """Calculate the full investment waterfall"""
    
    # Ownership percentage
    ownership_pct = initial_investment / post_money_val
    
    # Management carve out
    carve_out_amount = sale_price * (carve_out_pct / 100)
    
    # Net proceeds after carve out
    net_proceeds = sale_price - carve_out_amount
    
    # Liquidation preference (2x)
    liquidation_preference = 2 * initial_investment
    
    # Pro-rata share
    pro_rata_share = ownership_pct * net_proceeds
    
    # Fund receives the greater of liq pref or pro-rata (non-participating)
    liq_pref_applies = liquidation_preference >= pro_rata_share
    fund_gross_proceeds = max(liquidation_preference, pro_rata_share)
    
    # Cap at net proceeds (can't get more than what's available)
    fund_gross_proceeds = min(fund_gross_proceeds, net_proceeds)
    
    # Fund-level waterfall
    management_fees = initial_investment * 0.02 * holding_period
    
    # Net to fund after fees
    fund_net_proceeds = fund_gross_proceeds - management_fees
    
    # Return of capital first
    if fund_net_proceeds >= initial_investment:
        return_of_capital = initial_investment
        profit = fund_net_proceeds - initial_investment
        lp_profit_share = profit * 0.80
        gp_carry = profit * 0.20
    else:
        return_of_capital = max(fund_net_proceeds, 0)
        profit = 0
        lp_profit_share = 0
        gp_carry = 0
    
    # Total to investor (LP)
    total_to_investor = return_of_capital + lp_profit_share
    
    # MOIC calculation
    moic = total_to_investor / initial_investment if initial_investment > 0 else 0
    
    # IRR calculation
    cash_flows = [-initial_investment] + [0] * (holding_period - 1) + [total_to_investor]
    try:
        irr = npf.irr(cash_flows)
        if np.isnan(irr):
            irr = None
    except:
        irr = None
    
    return {
        'ownership_pct': ownership_pct,
        'carve_out_amount': carve_out_amount,
        'net_proceeds': net_proceeds,
        'liquidation_preference': liquidation_preference,
        'pro_rata_share': pro_rata_share,
        'liq_pref_applies': liq_pref_applies,
        'fund_gross_proceeds': fund_gross_proceeds,
        'management_fees': management_fees,
        'fund_net_proceeds': fund_net_proceeds,
        'return_of_capital': return_of_capital,
        'profit': profit,
        'lp_profit_share': lp_profit_share,
        'gp_carry': gp_carry,
        'total_to_investor': total_to_investor,
        'moic': moic,
        'irr': irr
    }

# Run calculations
results = calculate_waterfall(
    initial_investment, 
    sale_price, 
    carve_out_pct, 
    holding_period,
    POST_MONEY_VALUATION
)

# Display Results
st.header("Results Breakdown")

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Net to Investor",
        value=f"${results['total_to_investor']/1e6:,.2f}M",
        delta=f"${(results['total_to_investor'] - initial_investment)/1e6:,.2f}M"
    )

with col2:
    st.metric(
        label="MOIC",
        value=f"{results['moic']:.2f}x"
    )

with col3:
    if results['irr'] is not None:
        st.metric(
            label="IRR",
            value=f"{results['irr']*100:.1f}%"
        )
    else:
        st.metric(
            label="IRR",
            value="N/A"
        )

with col4:
    st.metric(
        label="Ownership",
        value=f"{results['ownership_pct']*100:.2f}%"
    )

st.divider()

# Detailed Breakdown
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Company-Level")
    
    st.write(f"**Sale Price:** ${sale_price/1e6:,.1f}M")
    st.write(f"Management Carve Out ({carve_out_pct:.1f}%): (${results['carve_out_amount']/1e6:,.2f}M)")
    st.write(f"**Net Proceeds: ${results['net_proceeds']/1e6:,.2f}M**")
    
    st.subheader("Liquidation Analysis")
    
    liq_pref_status = "Yes" if results['liq_pref_applies'] else "No (Pro-rata is higher)"
    
    st.write(f"2x Liquidation Preference: ${results['liquidation_preference']/1e6:,.2f}M")
    st.write(f"Pro-Rata Share ({results['ownership_pct']*100:.2f}%): ${results['pro_rata_share']/1e6:,.2f}M")
    st.write(f"**Liquidation Preference Applies:** {liq_pref_status}")
    st.write(f"**Fund Receives: ${results['fund_gross_proceeds']/1e6:,.2f}M**")

with col_right:
    st.subheader("Fund-Level Waterfall")
    
    st.write(f"Gross Proceeds to Fund: ${results['fund_gross_proceeds']/1e6:,.2f}M")
    st.write(f"Management Fees (2% x {holding_period} yrs): (${results['management_fees']/1e6:,.3f}M)")
    st.write(f"**Net Fund Proceeds: ${results['fund_net_proceeds']/1e6:,.2f}M**")
    
    st.subheader("Investor (LP) Waterfall")
    
    st.write(f"Return of Capital: ${results['return_of_capital']/1e6:,.2f}M")
    st.write(f"Profit to Split: ${results['profit']/1e6:,.2f}M")
    st.write(f"LP Share (80%): ${results['lp_profit_share']/1e6:,.2f}M")
    st.write(f"GP Carry (20%): ${results['gp_carry']/1e6:,.2f}M")
    st.write(f"**Total to Investor: ${results['total_to_investor']/1e6:,.2f}M**")

st.divider()

# Visualization
st.header("Visualizations")

tab1, tab2 = st.tabs(["Waterfall Breakdown", "Sensitivity Analysis"])

with tab1:
    st.subheader("Investment Waterfall: Sale to Net Investor Proceeds")
    
    # Create a text-based waterfall visualization
    waterfall_data = [
        ("Sale Price", sale_price, sale_price),
        ("Management Carve Out", -results['carve_out_amount'], results['net_proceeds']),
        ("To Other Shareholders", -(results['net_proceeds'] - results['fund_gross_proceeds']), results['fund_gross_proceeds']),
        ("Management Fees", -results['management_fees'], results['fund_gross_proceeds'] - results['management_fees']),
        ("GP Carry", -results['gp_carry'], results['total_to_investor']),
    ]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Step**")
    with col2:
        st.write("**Change**")
    with col3:
        st.write("**Running Total**")
    
    for label, change, running in waterfall_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(label)
        with col2:
            if change >= 0:
                st.write(f":green[+${change/1e6:,.2f}M]")
            else:
                st.write(f":red[-${abs(change)/1e6:,.2f}M]")
        with col3:
            st.write(f"${running/1e6:,.2f}M")
    
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Net to Investor**")
    with col2:
        st.write("")
    with col3:
        st.write(f"**:blue[${results['total_to_investor']/1e6:,.2f}M]**")
    
    # Bar chart representation
    st.subheader("Visual Breakdown")
    
    # Create ordered data for the chart
    categories = ["1. Sale Price", "2. After Carve Out", "3. Your Share", "4. After Fees", "5. Net to Investor"]
    amounts = [
        sale_price / 1e6,
        results['net_proceeds'] / 1e6,
        results['fund_gross_proceeds'] / 1e6,
        (results['fund_gross_proceeds'] - results['management_fees']) / 1e6,
        results['total_to_investor'] / 1e6
    ]
    
    # Display as horizontal metrics for cleaner ordered view
    for cat, amt in zip(categories, amounts):
        col_label, col_bar = st.columns([1, 3])
        with col_label:
            st.write(cat)
        with col_bar:
            st.progress(min(amt / (sale_price / 1e6), 1.0))
            st.caption(f"${amt:,.1f}M")
    
    st.caption("Amount in millions ($M)")

with tab2:
    st.subheader("Returns at Different Exit Values")
    
    # Sensitivity analysis across different exit values
    exit_values = list(range(25_000_000, 1_050_000_000, 25_000_000))
    moics = []
    irrs = []
    net_proceeds_list = []
    
    for exit_val in exit_values:
        r = calculate_waterfall(initial_investment, exit_val, carve_out_pct, holding_period, POST_MONEY_VALUATION)
        moics.append(r['moic'])
        irrs.append(r['irr'] * 100 if r['irr'] is not None else 0)
        net_proceeds_list.append(r['total_to_investor'])
  
    # Net Proceeds Chart
    st.write("**Net Proceeds to Investor by Exit Value**")
    net_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "Net Proceeds ($M)": [v / 1e6 for v in net_proceeds_list]
    }
    st.line_chart(net_chart_data, x="Exit Value ($M)", y="Net Proceeds ($M)")
    
    # MOIC Chart
    st.write("**MOIC by Exit Value**")
    moic_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "MOIC": moics
    }
    st.line_chart(moic_chart_data, x="Exit Value ($M)", y="MOIC")
    
    # IRR Chart
    st.write("**IRR by Exit Value**")
    irr_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "IRR (%)": irrs
    }
    st.line_chart(irr_chart_data, x="Exit Value ($M)", y="IRR (%)")
    
    # Current position indicator
    st.info(f"**Current selection:** ${sale_price/1e6:.0f}M exit → {results['moic']:.2f}x MOIC, {results['irr']*100:.1f}% IRR" if results['irr'] else f"**Current selection:** ${sale_price/1e6:.0f}M exit → {results['moic']:.2f}x MOIC")
    
    # Table showing key thresholds
    st.subheader("Key Return Thresholds")
    
    # Find breakeven and target MOICs
    thresholds = [0.5, 1.0, 2.0, 3.0, 5.0]
    threshold_results = []
    
    for target_moic in thresholds:
        found = False
        for exit_val in range(25_000_000, 1_100_000_000, 5_000_000):
            r = calculate_waterfall(initial_investment, exit_val, carve_out_pct, holding_period, POST_MONEY_VALUATION)
            if r['moic'] >= target_moic:
                threshold_results.append({
                    'Target MOIC': f"{target_moic}x",
                    'Required Exit': f"${exit_val/1e6:.0f}M",
                    'Exit Multiple': f"{exit_val/POST_MONEY_VALUATION:.1f}x"
                })
                found = True
                break
        if not found:
            threshold_results.append({
                'Target MOIC': f"{target_moic}x",
                'Required Exit': ">$1B",
                'Exit Multiple': ">12.5x"
            })
    
    # Display as columns
    cols = st.columns(5)
    for i, result in enumerate(threshold_results):
        with cols[i]:
            st.metric(
                label=f"For {result['Target MOIC']}",
                value=result['Required Exit'],
                delta=result['Exit Multiple']
            )


# Footer
st.divider()
st.caption("$10M fund size | $80M post-money valuation | 2x non-participating liquidation preference")

st.divider()
st.markdown("""
**Disclaimer**

This calculator is provided for informational and illustrative purposes only and does not constitute investment, financial, legal, or tax advice. The projections and calculations presented are based on hypothetical assumptions and simplified models that may not reflect actual investment outcomes.

Past performance is not indicative of future results. Actual returns may vary materially due to factors including but not limited to: market conditions, deal terms, timing of exits, tax implications, and other variables not accounted for in this model.

This tool should not be relied upon as the sole basis for any investment decision. Users are strongly encouraged to consult with qualified financial, legal, and tax advisors before making any investment decisions. The creators and providers of this calculator assume no liability for any losses or damages arising from the use of this tool.

By using this calculator, you acknowledge that you understand these limitations and assume all risks associated with any decisions made based on the information provided.
""", help=None)
