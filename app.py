import pandas as pd
import streamlit as st
from models import Order
from orderbook import OrderBook

ASK_PRICES = (10000, 10100, 10300, 10600)


def simulate(quantity, depth, limit_cents):
    book = OrderBook()
    for i, price in enumerate(ASK_PRICES):
        book.submit(Order(f"S{i}", "sell", price, depth))
    fills = book.submit(Order("B", "buy", limit_cents, quantity))
    filled = sum(trade.quantity for trade in fills)
    spent = sum(trade.price_cents * trade.quantity for trade in fills)
    slippage = spent - filled * ASK_PRICES[0]
    return fills, filled, spent, slippage


st.set_page_config(page_title="Market Execution Lab", page_icon="📈", layout="wide")
st.title("Market Execution Lab")
st.caption("Limit-order simulation · Synthetic liquidity · No live trading")

with st.sidebar:
    st.header("Trade controls")
    quantity = st.slider("Buy quantity", 1, 100, 20)
    depth = st.slider("Units available at each price", 1, 25, 5)
    limit = st.select_slider(
        "Maximum buy price",
        options=(100, 101, 103, 106),
        value=106,
        format_func=lambda p: f"${p:.2f}",
    )
    st.caption("Ask prices: $100, $101, $103, $106")

fills, filled, spent, slippage = simulate(quantity, depth, limit * 100)
mean_price = spent / filled / 100 if filled else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Filled", f"{filled}/{quantity}")
m2.metric("Average fill price", f"${mean_price:,.2f}" if filled else "—")
m3.metric("Total execution cost", f"${spent / 100:,.2f}")
m4.metric("Extra cost vs. best ask", f"${slippage / 100:,.2f}")

if filled < quantity:
    st.warning(f"Only {filled} of {quantity} units filled at or below ${limit:.2f}.")
else:
    st.success("Buy order fully filled in the simulation.")

rows = []
for size in range(1, depth * len(ASK_PRICES) + 1):
    _, count, cost, extra = simulate(size, depth, limit * 100)
    if count == size:
        rows.append({
            "Order size": size,
            "Simulated execution": cost / 100,
            "Best-ask estimate": size * ASK_PRICES[0] / 100,
            "Extra cost": extra / 100,
        })

chart_data = pd.DataFrame(rows).set_index("Order size")
left, right = st.columns(2)
with left:
    st.subheader("Execution cost vs. order size")
    st.line_chart(chart_data[["Simulated execution", "Best-ask estimate"]])
with right:
    st.subheader("Slippage vs. order size")
    st.line_chart(chart_data[["Extra cost"]])

st.caption("Charts include only orders that can be fully filled at your selected price limit.")

left, right = st.columns(2)
with left:
    st.subheader("Available liquidity before buying")
    st.dataframe(pd.DataFrame([
        {"Ask price": f"${price / 100:.2f}", "Units": depth,
         "Allowed by limit": "Yes" if price <= limit * 100 else "No"}
        for price in ASK_PRICES
    ]), hide_index=True, use_container_width=True)
with right:
    st.subheader("Executed trades")
    if fills:
        st.dataframe(pd.DataFrame([
            {"Price": f"${trade.price_cents / 100:.2f}",
             "Units": trade.quantity,
             "Cost": f"${trade.price_cents * trade.quantity / 100:.2f}"}
            for trade in fills
        ]), hide_index=True, use_container_width=True)
    else:
        st.info("No trades executed.")

st.download_button(
    "Download scenarios CSV",
    chart_data.reset_index().to_csv(index=False),
    file_name="execution_scenarios.csv",
    mime="text/csv",
)
st.caption("Slippage = simulated spend − filled units × $100. Fees and market impact are excluded.")
