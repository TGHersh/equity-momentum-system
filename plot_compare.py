import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SUBJECT = "NKE"
BENCHMARKS = ["SPY", "XLY"]
NAMES = {"NKE": "Nike", "SPY": "S&P 500", "XLY": "Consumer disc."}
COLORS = {"NKE": "#2a78d6", "SPY": "#eb6834", "XLY": "#1baf7a"}
INK, MUTED = "#1a1a19", "#6b6b66"

df = pd.read_csv("data/prices_daily.csv", parse_dates=["date"])
df = df.sort_values(["ticker", "date"])

# Splits: ticker --> [(effective date, ratio)]. Ratio 2 = 2-for-1
SPLITS = {
    "XLY": [("2025-12-05", 2)],
}

for tkr, events in SPLITS.items():
    for eff_date, ratio in events:
        earlier = (df["ticker"] == tkr) & (df["date"] < pd.Timestamp(eff_date))
        df.loc[earlier, ["open", "high", "low", "close"]] /= ratio
        df.loc[earlier, "volume"] *= ratio





nke = df[df["ticker"] == SUBJECT].copy()
nke["ma20"] = nke["close"].rolling(20).mean()
nke["ma50"] = nke["close"].rolling(50).mean()

df["rebased"] = df.groupby("ticker")["close"].transform(lambda s: s / s.iloc[0] * 100)

fig, (ax1, ax2, ax3) = plt.subplots(
    3, 1, figsize=(13,11), sharex=True, 
    gridspec_kw={"height_ratios": [3, 3, 1], "hspace": 0.34},
)

# panel 1 - Nike's actual price, in dollars
ax1.plot(nke["date"], nke["close"], lw=2.0, color=COLORS["NKE"], label="Close")
ax1.plot(nke["date"], nke["ma20"], lw=1.4, color="#eb6834", label="20-day average")
ax1.plot(nke["date"], nke["ma50"], lw=1.4, color="#1baf7a", label="50-day average")
ax1.set_title(f"Nike (NKE) daily close, unadjusted   -   "
              f"{nke['date'].min():%d %b %Y} to {nke['date'].max():%d %b %Y}",
              fontsize=13, loc="left", color=INK, pad=12)
ax1.set_ylabel("Price (USD)", color=MUTED)
ax1.legend(frameon=False, loc="upper left", labelcolor=INK)

# panel 2, everything rebased to 100, so the scales are comparable
ends = []
for t in [SUBJECT] + BENCHMARKS:
    s = df[df["ticker"] == t]
    ax2.plot(s["date"], s["rebased"], lw=2.0, color=COLORS[t], label=NAMES[t])
    last = s.iloc[-1]
    ax2.plot(last["date"], last["rebased"], "o", ms=5, color=COLORS[t])
    ends.append([t, last["date"], last["rebased"], last["rebased"]])


span = df["rebased"].max() - df["rebased"].min()
gap = span * 0.045
ends.sort(key=lambda e: -e[2])
for i in range(1, len(ends)):
    if ends[i - 1][3] - ends[i][3] < gap:
        ends[i][3] = ends[i -1][3] - gap

for t, x, y, y_label in ends:
    ax2.annotate(f" {NAMES[t]} {y:.0f}", (x, y), xytext=(x, y_label),
                 color=INK, fontsize=9, va="center")

ax2.axhline(100, color=MUTED, lw=1, ls="--", alpha=0.6)
ax2.set_title("Relative performance - all series rebased to 100 at the start",
              fontsize=13, loc="left", color=INK, pad=12)
ax2.set_ylabel("Indexed (start = 100)", color=MUTED)
ax2.legend(frameon=False, loc="upper left", labelcolor=INK)

# panel 3 - Nike Volume
ax3.bar(nke["date"], nke["volume"] / 1e6, color="#c9c8c0", width=1.0)
ax3.set_ylabel("Volume (m)", color=MUTED)
ax3.set_xlabel("Date", color=MUTED)

for ax in (ax1, ax2, ax3):
    ax.grid(axis="y", alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#d8d7d0")
    ax.tick_params(colors=MUTED, labelsize=9)


ax2.set_xlim(right=nke["date"].max() + pd.Timedelta(days=120)) # room for labels

fig.savefig("nke_vs_benchmarks.png", dpi=150, bbox_inches="tight",
            facecolor= "#fcfcfb")
print("Saved nke_vs_benchmarks.png")