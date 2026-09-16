"""The web app. Reads the prepared JSON ans renders it. Does no data work"""

import json
from pathlib import Path

from flask import Flask, abort, redirect, render_template, url_for

app = Flask(__name__)
DATA = Path("data/dashboard.json")


def load_dashboard():
    with DATA.open() as f:
        return json.load(f)

NEWS = Path("data/news.json")

def load_news():
    try:
        with NEWS.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
            

        
@app.template_filter("pct")
def pct(value, dp=1):
    """-1.8126 -> '-1.8%'. None -> '--'"""
    if value is None:
        return "--"
    return f"{value:+.{dp}f}%"



@app.template_filter("arrow")
def arrow(value):
    if value is None:
        return ""
    return "▲" if value > 0 else ("▼" if value < 0 else "-")


@app.template_filter("dir")
def direction(value):
    if value is None:
        return "flat"
    return "up" if value > 0 else ("down" if value < 0 else "flat")


def build_chart(relative, width=300, height=60, pad=3):
    """Scale every series on ONE shared range, so the lines stay comparable.

    Scaling each series to its own min and max would make thema all fill the box
    and silently destroy the comparison - the same mistake as a second y-axis
    """
    everything = [v for r in relative for v in r["spark"]]
    if not everything:
        return[]
    lo, hi = min(everything), max(everything)
    span = (hi - lo) or 1 
    inner = height - 2 * pad

    out = []
    for r in relative:
        vals = r["spark"]
        step = width / max(len(vals) - 1, 1)
        pts = " ".join(
            f"{i * step:.1f}, {pad + inner - (v - lo) / span * inner:.1f}"
            for i, v in enumerate(vals)
        )
        out.append({**r, "points": pts})
    return out


@app.route("/")
def home():
    """The bare URL sends you to the first ticker in ticker.json."""
    d = load_dashboard()
    return redirect(url_for("stock", ticker=d["tickers"][0]))

@app.route("/stock/<ticker>")
def stock(ticker):
    d = load_dashboard()
    ticker = ticker.upper()
    if ticker not in d["subjects"]:
        abort(404)
    s = d["subjects"][ticker]
    return render_template("dashboard.html", d=d, s=s,
                           chart=build_chart(s["relative"]), news=load_news())
    

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    

