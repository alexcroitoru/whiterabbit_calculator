"""
Investment Waterfall Calculator
Calculates investor returns based on fund-level ownership and investor's share of fund
"""

import streamlit as st
import numpy as np
import numpy_financial as npf

# Page configuration
st.set_page_config(
    page_title="Investment Waterfall Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Title and description
st.title("Investment Waterfall Calculator")
st.markdown("""
Calculate your expected returns on a venture investment through a fund structure.
The fund invests in the company, and you receive your proportional share of fund distributions.
""")

st.divider()

# Sidebar for fixed assumptions
with st.sidebar:
    st.header("Fixed Assumptions")
    st.markdown("""
    - **Fund Size:** $10M
    - **Post-Money Valuation:** $82M
    - **Fund Ownership:** ~12.2% of company
    - **Liquidation Preference:** 2x Non-Participating (on fund investment)
    - **Fund Profit Split:** 80% LP / 20% GP
    - **Management Fee:** 2% annual (of fund size)
    - **Management Carve Out:** Only applies if exit < $200M
    """)
    
    st.divider()
    st.markdown("### How It Works")
    st.markdown("""
    **Fund Level:**
    1. Fund owns (Fund Size / Post-Money) of the company
    2. At exit, Fund receives greater of 2x investment or pro-rata share
    3. Management fees deducted, then 80/20 LP/GP split on profits
    
    **Investor Level:**
    4. Your ownership of fund = Your Contribution / Fund Size
    5. You receive your % of all LP distributions
    """)

# Constants
FUND_SIZE = 10_000_000  # $10M fund
POST_MONEY_VALUATION = 82_000_000  # $82M valuation
FUND_OWNERSHIP_PCT = FUND_SIZE / POST_MONEY_VALUATION  # ~12.19%

# Main input section
st.header("Input Parameters")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Fund Size:** $10.00M")
    st.markdown(f"**Post-Money Valuation:** $82.00M")
    st.markdown(f"**Fund Ownership of Company:** {FUND_OWNERSHIP_PCT*100:.2f}%")
    
    st.divider()
    
    investor_contribution_mm = st.number_input(
        "Your Investment in Fund ($M)",
        min_value=0.01,
        max_value=7.0,
        value=2.0,
        step=0.1,
        format="%.2f",
        help="Your contribution to the $10M fund"
    )
    investor_contribution = investor_contribution_mm * 1_000_000
    investor_fund_pct = investor_contribution / FUND_SIZE
    
    st.markdown(f"**Your Ownership of Fund:** {investor_fund_pct*100:.2f}%")
    
    holding_period = st.number_input(
        "Holding Period (Years)",
        min_value=1,
        max_value=10,
        value=2,
        step=1,
        help="Expected time until exit event"
    )

with col2:
    sale_price_mm = st.slider(
        "Company Sale Price ($M)",
        min_value=20,
        max_value=1000,
        value=200,
        step=20,
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
        help="Percentage of sale price allocated to management team (only applies if sale price < $200M)"
    )

st.divider()

# Calculations
def calculate_waterfall(fund_size, investor_contribution, sale_price, carve_out_pct, holding_period, post_money_val):
    """Calculate the full investment waterfall at fund and investor level"""
    
    # Fund ownership of company
    fund_ownership_pct = fund_size / post_money_val
    
    # Investor ownership of fund
    investor_fund_pct = investor_contribution / fund_size
    
    # Management carve out (only applies if sale price < $200M)
    if sale_price < 200_000_000:
        carve_out_amount = sale_price * (carve_out_pct / 100)
    else:
        carve_out_amount = 0
    
    # Net proceeds from sale (available to all shareholders)
    net_proceeds = sale_price - carve_out_amount
    
    # Fund's liquidation preference (2x fund investment)
    fund_liq_pref = 2 * fund_size
    
    # Fund's pro-rata share
    fund_pro_rata = fund_ownership_pct * net_proceeds
    
    # Fund receives greater of liq pref or pro-rata (non-participating)
    liq_pref_applies = fund_liq_pref >= fund_pro_rata
    fund_gross_proceeds = max(fund_liq_pref, fund_pro_rata)
    
    # Cap at net proceeds (can't get more than what's available)
    fund_gross_proceeds = min(fund_gross_proceeds, net_proceeds)
    
    # Fund-level management fees (2% of fund size per year)
    total_management_fees = fund_size * 0.02 * holding_period
    
    # Fund net proceeds after fees
    fund_net_proceeds = fund_gross_proceeds - total_management_fees
    
    # Fund-level waterfall: return capital first, then split profits
    if fund_net_proceeds >= fund_size:
        fund_return_of_capital = fund_size
        fund_profit = fund_net_proceeds - fund_size
        total_lp_profit_share = fund_profit * 0.80
        total_gp_carry = fund_profit * 0.20
    else:
        fund_return_of_capital = max(fund_net_proceeds, 0)
        fund_profit = 0
        total_lp_profit_share = 0
        total_gp_carry = 0
    
    # Total LP distributions (return of capital + profit share)
    total_lp_distributions = fund_return_of_capital + total_lp_profit_share
    
    # Investor's share of LP distributions (proportional to their fund ownership)
    investor_return_of_capital = investor_fund_pct * fund_return_of_capital
    investor_profit_share = investor_fund_pct * total_lp_profit_share
    investor_total = investor_fund_pct * total_lp_distributions
    
    # Investor MOIC and IRR
    investor_moic = investor_total / investor_contribution if investor_contribution > 0 else 0
    
    cash_flows = [-investor_contribution] + [0] * (holding_period - 1) + [investor_total]
    try:
        irr = npf.irr(cash_flows)
        if np.isnan(irr):
            irr = None
    except:
        irr = None
    
    return {
        # Company-level
        'carve_out_amount': carve_out_amount,
        'net_proceeds': net_proceeds,
        # Fund-level
        'fund_ownership_pct': fund_ownership_pct,
        'fund_liq_pref': fund_liq_pref,
        'fund_pro_rata': fund_pro_rata,
        'liq_pref_applies': liq_pref_applies,
        'fund_gross_proceeds': fund_gross_proceeds,
        'total_management_fees': total_management_fees,
        'fund_net_proceeds': fund_net_proceeds,
        'fund_return_of_capital': fund_return_of_capital,
        'fund_profit': fund_profit,
        'total_lp_profit_share': total_lp_profit_share,
        'total_gp_carry': total_gp_carry,
        'total_lp_distributions': total_lp_distributions,
        # Investor-level
        'investor_fund_pct': investor_fund_pct,
        'investor_return_of_capital': investor_return_of_capital,
        'investor_profit_share': investor_profit_share,
        'investor_total': investor_total,
        'investor_moic': investor_moic,
        'irr': irr
    }

# Run calculations
results = calculate_waterfall(
    FUND_SIZE,
    investor_contribution, 
    sale_price, 
    carve_out_pct, 
    holding_period,
    POST_MONEY_VALUATION
)

# Display Results
st.header("Results Breakdown")

# Key Metrics Row - Investor Level
st.subheader("Your Investment Returns")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Net to You",
        value=f"${results['investor_total']/1e6:,.2f}M",
        delta=f"${(results['investor_total'] - investor_contribution)/1e6:,.2f}M"
    )

with col2:
    st.metric(
        label="Your MOIC",
        value=f"{results['investor_moic']:.2f}x"
    )

with col3:
    if results['irr'] is not None:
        st.metric(
            label="Your IRR",
            value=f"{results['irr']*100:.1f}%"
        )
    else:
        st.metric(
            label="Your IRR",
            value="N/A"
        )

with col4:
    st.metric(
        label="Your Fund Ownership",
        value=f"{results['investor_fund_pct']*100:.2f}%"
    )

st.divider()

# Detailed Breakdown
col_left, col_mid, col_right = st.columns(3)

with col_left:
    st.subheader("Company-Level")
    
    st.write(f"**Sale Price:** ${sale_price/1e6:,.1f}M")
    if sale_price < 200_000_000:
        st.write(f"Management Carve Out ({carve_out_pct:.1f}%): (${results['carve_out_amount']/1e6:,.2f}M)")
    else:
        st.write(f"Management Carve Out: $0 (N/A above $200M)")
    st.write(f"**Net Proceeds: ${results['net_proceeds']/1e6:,.2f}M**")
    
    st.divider()
    
    st.subheader("Fund's Share")
    
    liq_pref_status = "Yes" if results['liq_pref_applies'] else "No (Pro-rata is higher)"
    
    st.write(f"Fund Ownership: {results['fund_ownership_pct']*100:.2f}%")
    st.write(f"2x Liquidation Preference: ${results['fund_liq_pref']/1e6:,.2f}M")
    st.write(f"Pro-Rata Share: ${results['fund_pro_rata']/1e6:,.2f}M")
    st.write(f"**Liq Pref Applies:** {liq_pref_status}")
    st.write(f"**Fund Receives: ${results['fund_gross_proceeds']/1e6:,.2f}M**")

with col_mid:
    st.subheader("Fund-Level Waterfall")
    
    st.write(f"Gross Proceeds: ${results['fund_gross_proceeds']/1e6:,.2f}M")
    st.write(f"Management Fees (2% x {holding_period} yrs): (${results['total_management_fees']/1e6:,.2f}M)")
    st.write(f"**Net Fund Proceeds: ${results['fund_net_proceeds']/1e6:,.2f}M**")
    
    st.divider()
    
    st.write(f"Return of Capital: ${results['fund_return_of_capital']/1e6:,.2f}M")
    st.write(f"Fund Profit: ${results['fund_profit']/1e6:,.2f}M")
    st.write(f"LP Profit Share (80%): ${results['total_lp_profit_share']/1e6:,.2f}M")
    st.write(f"GP Carry (20%): ${results['total_gp_carry']/1e6:,.2f}M")
    st.write(f"**Total LP Distributions: ${results['total_lp_distributions']/1e6:,.2f}M**")

with col_right:
    st.subheader("Your Share (LP)")
    
    st.write(f"Your Fund Ownership: {results['investor_fund_pct']*100:.2f}%")
    
    st.divider()
    
    st.write(f"Your Return of Capital: ${results['investor_return_of_capital']/1e6:,.2f}M")
    st.write(f"Your Profit Share: ${results['investor_profit_share']/1e6:,.2f}M")
    st.write(f"**Total to You: ${results['investor_total']/1e6:,.2f}M**")
    
    st.divider()
    
    st.write(f"**Your MOIC: {results['investor_moic']:.2f}x**")
    if results['irr'] is not None:
        st.write(f"**Your IRR: {results['irr']*100:.1f}%**")

st.divider()

# Visualization
st.header("Visualizations")

tab1, tab2 = st.tabs(["Waterfall Breakdown", "Sensitivity Analysis"])

with tab1:
    st.subheader("Investment Waterfall: Sale to Your Net Proceeds")
    
    # Create a text-based waterfall visualization
    waterfall_data = [
        ("Company Sale Price", sale_price, sale_price),
        ("Management Carve Out", -results['carve_out_amount'], results['net_proceeds']),
        ("To Other Shareholders", -(results['net_proceeds'] - results['fund_gross_proceeds']), results['fund_gross_proceeds']),
        ("Fund Management Fees", -results['total_management_fees'], results['fund_net_proceeds']),
        ("GP Carry", -results['total_gp_carry'], results['total_lp_distributions']),
        ("To Other LPs", -(results['total_lp_distributions'] - results['investor_total']), results['investor_total']),
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
        st.write("**Net to You**")
    with col2:
        st.write("")
    with col3:
        st.write(f"**:blue[${results['investor_total']/1e6:,.2f}M]**")
    
    # Bar chart representation
    st.subheader("Visual Breakdown")
    
    # Create ordered data for the chart
    categories = [
        "1. Sale Price", 
        "2. After Carve Out", 
        "3. Fund's Share", 
        "4. After Fees",
        "5. LP Distributions",
        "6. Your Share"
    ]
    amounts = [
        sale_price / 1e6,
        results['net_proceeds'] / 1e6,
        results['fund_gross_proceeds'] / 1e6,
        results['fund_net_proceeds'] / 1e6,
        results['total_lp_distributions'] / 1e6,
        results['investor_total'] / 1e6
    ]
    
    # Display as horizontal metrics for cleaner ordered view
    for cat, amt in zip(categories, amounts):
        col_label, col_bar = st.columns([1, 3])
        with col_label:
            st.write(cat)
        with col_bar:
            st.progress(min(amt / (sale_price / 1e6), 1.0))
            st.caption(f"${amt:,.2f}M")
    
    st.caption("Amount in millions ($M)")

with tab2:
    st.subheader("Returns at Different Exit Values")
    
    # Sensitivity analysis across different exit values
    exit_values = list(range(25_000_000, 1_050_000_000, 25_000_000))
    moics = []
    irrs = []
    net_proceeds_list = []
    
    for exit_val in exit_values:
        r = calculate_waterfall(FUND_SIZE, investor_contribution, exit_val, carve_out_pct, holding_period, POST_MONEY_VALUATION)
        moics.append(r['investor_moic'])
        irrs.append(r['irr'] * 100 if r['irr'] is not None else 0)
        net_proceeds_list.append(r['investor_total'])
    
    # Net Proceeds Chart
    st.write("**Your Net Proceeds by Exit Value**")
    net_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "Your Net Proceeds ($M)": [v / 1e6 for v in net_proceeds_list]
    }
    st.line_chart(net_chart_data, x="Exit Value ($M)", y="Your Net Proceeds ($M)")
    
    # MOIC Chart
    st.write("**Your MOIC by Exit Value**")
    moic_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "MOIC": moics
    }
    st.line_chart(moic_chart_data, x="Exit Value ($M)", y="MOIC")
    
    # IRR Chart
    st.write("**Your IRR by Exit Value**")
    irr_chart_data = {
        "Exit Value ($M)": [v / 1e6 for v in exit_values],
        "IRR (%)": irrs
    }
    st.line_chart(irr_chart_data, x="Exit Value ($M)", y="IRR (%)")
    
    # Current position indicator
    st.info(f"**Current selection:** ${sale_price/1e6:.0f}M exit → {results['investor_moic']:.2f}x MOIC, {results['irr']*100:.1f}% IRR" if results['irr'] else f"**Current selection:** ${sale_price/1e6:.0f}M exit → {results['investor_moic']:.2f}x MOIC")
    
    # Table showing key thresholds
    st.subheader("Key Return Thresholds")
    
    # Find breakeven and target MOICs
    thresholds = [1.0, 1.5, 2.0, 3.0, 5.0]
    threshold_results = []
    
    for target_moic in thresholds:
        found = False
        for exit_val in range(5_000_000, 1_100_000_000, 5_000_000):
            r = calculate_waterfall(FUND_SIZE, investor_contribution, exit_val, carve_out_pct, holding_period, POST_MONEY_VALUATION)
            if r['investor_moic'] >= target_moic:
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
                'Exit Multiple': ">12.2x"
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
st.caption("$10M fund | $82M post-money | Fund owns 12.19% of company | 2x non-participating liquidation preference | Management carve out applies only below $200M exit")

st.divider()
st.markdown("""
**Disclaimer**

This calculator is provided for informational and illustrative purposes only and does not constitute investment, financial, legal, or tax advice. The projections and calculations presented are based on hypothetical assumptions and simplified models that may not reflect actual investment outcomes.

Past performance is not indicative of future results. Actual returns may vary materially due to factors including but not limited to: market conditions, deal terms, timing of exits, tax implications, and other variables not accounted for in this model.

This tool should not be relied upon as the sole basis for any investment decision. Users are strongly encouraged to consult with qualified financial, legal, and tax advisors before making any investment decisions. The creators and providers of this calculator assume no liability for any losses or damages arising from the use of this tool.

By using this calculator, you acknowledge that you understand these limitations and assume all risks associated with any decisions made based on the information provided.
""", help=None)
