import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt 
import pandas as pd 

df = pd.read_csv("data/prices_daily.csv", parse_dates=["date"])
df = df[df["ticker"] == "NKE"].copy()

# Moving averages: each point is the mean of the N previous closes.
df["ma20"] = df["close"].rolling(20).mean()
df["ma50"] = df["close"].rolling(50).mean()

fig, (ax1, ax2) = plt.subplots(     
    2, 1, figsize=(13, 8), sharex=True,
    gridspec_kw={"height_ratios": [3, 1 ]},
)

ax1.plot(df["date"], df["close"], linewidth=1.8, color="#3b6ef6", label="Close")
ax1.plot(df["date"], df["ma20"], linewidth=1.2, color="#e08a1e", label="20-day MA")
ax1.plot(df["date"], df["ma50"], linewidth=1.2, color="#8b5cf6", label="50-day MA")
ax1.set_title(f"Nike (NKE) daily close · {df['date'].min():%d %b %Y } - {df['date'].max():%d %b %Y}",
              fontsize=14, loc="left")
ax1.set_ylabel("Price(USD, unadjusted)")
ax1.legend(frameon=False)
ax1.grid(alpha=0.25)
ax1.spines[["top", "right"]].set_visible(False)

ax2.bar(df["date"], df["volume"] / 1e6, color="#9aa4b2", width=1.0)
ax2.set_ylabel("Volume (m)")
ax2.set_xlabel("Date")
ax2.grid(alpha=0.25)
ax2.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig("nke_chart.png", dpi=150)
print("Saved nke_chart.png")
