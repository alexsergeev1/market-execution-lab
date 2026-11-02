from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from models import Order
from orderbook import OrderBook

asks = [(10000, 5), (10100, 5), (10300, 5), (10600, 5)]
rows = []
for qty in range(1, 21):
    book = OrderBook()
    for i, (price, amount) in enumerate(asks):
        book.submit(Order(f"S{i}", "sell", price, amount))
    fills = book.submit(Order("B", "buy", 10600, qty))
    actual = sum(t.price_cents * t.quantity for t in fills) / 100
    naive = qty * asks[0][0] / 100
    rows.append((qty, actual, naive, actual - naive))

df = pd.DataFrame(rows, columns=["quantity", "actual_usd", "naive_usd", "extra_usd"])
Path("results").mkdir(exist_ok=True)
df.to_csv("results/execution_cost.csv", index=False)
plt.figure(figsize=(9, 5))
plt.plot(df.quantity, df.actual_usd, label="Real execution", linewidth=2)
plt.plot(df.quantity, df.naive_usd, "--", label="Best-price estimate")
plt.fill_between(df.quantity, df.naive_usd, df.actual_usd, alpha=0.2)
plt.xlabel("Order size (units)")
plt.ylabel("Total cost ($)")
plt.title("Execution Cost vs. Order Size")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig("results/execution_cost.png", dpi=180)
plt.show()
plt.figure(figsize=(9, 5))
plt.plot(df.quantity, df.extra_usd, marker="o")
plt.xlabel("Order Size")
plt.ylabel("Extra Cost ($)")
plt.title("Trading Slippage vs. Order Size")
plt.grid(alpha=0.3)
plt.savefig("results/slippage.png", dpi=200)
plt.show()
