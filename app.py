
import math
import pandas as pd
import streamlit as st

# ----------------- Core helpers -----------------
def american_to_implied_p(odds: float) -> float:
    if odds < 0:
        return (-odds) / ((-odds) + 100.0)
    return 100.0 / (odds + 100.0)

def american_to_decimal(odds: float) -> float:
    if odds < 0:
        return 1.0 + (100.0 / (-odds))
    return 1.0 + (odds / 100.0)

def logistic_win_prob(margin: float, k: float = 6.0) -> float:
    return 1.0 / (1.0 + math.exp(-(margin / k)))

def cover_prob(projected_margin: float, alt_line: float, k: float = 6.0) -> float:
    adj = projected_margin - alt_line
    return 1.0 / (1.0 + math.exp(-(adj / k)))

def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    z = (x - mu) / max(1e-9, sigma)
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def prop_over_prob(projection: float, stdev: float, line: float) -> float:
    return 1.0 - normal_cdf(line, mu=projection, sigma=stdev)

def prop_under_prob(projection: float, stdev: float, line: float) -> float:
    return normal_cdf(line, mu=projection, sigma=stdev)

def kelly_fraction_full(p: float, dec_odds: float) -> float:
    b = max(1e-12, dec_odds - 1.0)
    q = 1.0 - p
    f_full = (b * p - q) / b
    return max(0.0, f_full)

# ----------------- UI -----------------
st.set_page_config(page_title="NFL Betting Calculator + Google Sheets", page_icon="🏈", layout="centered")
st.title("🏈 NFL Betting Calculator + Google Sheets")
st.caption("Moneyline · Alt Spreads · 1st Half · Player Props · Kelly sizing")

with st.sidebar:
    st.header("Bankroll & Settings")
    bankroll = st.number_input("Current Bankroll ($)", min_value=0.0, value=100.0, step=1.0)
    base_unit = st.number_input("Base Unit ($)", min_value=0.1, value=1.5, step=0.1)
    kelly_mult = st.slider("Kelly Multiplier", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    st.markdown("---")
    st.subheader("Load from Google Sheets (CSV)")
    st.write("**In Google Sheets:** File → Share → Publish to web → Select a single tab (e.g., 'Models - Team'), choose **CSV**, copy the link.")
    csv_url = st.text_input("Paste CSV URL (published sheet)", value="", help="Looks like: https://docs.google.com/spreadsheets/d/..../export?format=csv&gid=...")
    df = None
    if csv_url:
        try:
            df = pd.read_csv(csv_url)
            st.success(f"Loaded {len(df)} rows.")
            if len(df.columns) <= 1:
                st.info("If the data appears in one wide column, ensure you published as CSV (not web page) and the tab has headers.")
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")

mode = st.radio("Pick a market:", ["Moneyline", "Alt Spread", "First Half", "Player Prop"], horizontal=True)

# --------- MONEYLINE ---------
if mode == "Moneyline":
    st.subheader("Moneyline")
    # Try to preload from Google Sheet based on standard header names in your tracker ("Models - Team" tab)
    preload = {}
    if df is not None:
        st.write("Select a row (from your 'Models - Team' CSV) to prefill:")
        show_cols = [c for c in df.columns if c in ["Game","Projected Margin","Logistic Slope (k)","Book Odds (American)","p_you (Win Prob)"] or "p_you" in c or "Book Odds" in c or "Game" in c]
        st.dataframe(df[show_cols] if show_cols else df.head(20))
        row_idx = st.number_input("Row index to load", min_value=0, max_value=max(0, len(df)-1), value=0, step=1)
        try:
            row = df.iloc[int(row_idx)]
            # Accept either explicit p_you or derive from Projected Margin
            if "p_you (Win Prob)" in df.columns and pd.notna(row.get("p_you (Win Prob)")):
                preload["p_you"] = float(row.get("p_you (Win Prob)", 0.55))
            elif "Projected Margin" in df.columns and "Logistic Slope (k)" in df.columns:
                pm = float(row.get("Projected Margin", 0))
                kk = float(row.get("Logistic Slope (k)", 6))
                preload["p_you"] = 1.0 / (1.0 + math.exp(-(pm / kk)))
            if "Book Odds (American)" in df.columns and pd.notna(row.get("Book Odds (American)")):
                preload["odds"] = float(row.get("Book Odds (American)", -110))
        except Exception:
            pass

    p_you = st.number_input("Your Win Probability (0–1)", min_value=0.0, max_value=1.0, value=float(preload.get("p_you", 0.57)), step=0.01, format="%.2f")
    american_odds = st.number_input("FanDuel Odds (American)", value=int(preload.get("odds", -105)), step=5)

    p_book = american_to_implied_p(american_odds)
    dec_odds = american_to_decimal(american_odds)
    edge = p_you - p_book
    f_full = kelly_fraction_full(p_you, dec_odds)
    f_scaled = kelly_mult * f_full
    stake = bankroll * f_scaled
    units = stake / base_unit if base_unit > 0 else 0.0

    st.metric("Your Probability", f"{p_you*100:.2f}%")
    st.metric("Book Implied", f"{p_book*100:.2f}%")
    st.metric("Edge", f"{edge*100:+.2f}%")
    st.metric("Decimal Odds", f"{dec_odds:.3f}")
    st.markdown("### Kelly Sizing")
    st.write(f"**Full Kelly f\\***: `{f_full:.4f}`  |  **Scaled (×{kelly_mult:.2f})**: `{f_scaled:.4f}`")
    st.write(f"**Stake**: `${stake:.2f}`  (**{units:.2f}u** @ ${base_unit:.2f}/u)")

# --------- ALT SPREAD ---------
elif mode == "Alt Spread":
    st.subheader("Alternative Spread")
    preload = {}
    if df is not None:
        st.write("Select a row (from your 'Models - Alt Spreads' CSV) to prefill:")
        show_cols = [c for c in df.columns if c in ["Game","Projected Margin","Alt Line (k)","Logistic Slope (k)","Alt Odds (American)"]]
        st.dataframe(df[show_cols] if show_cols else df.head(20))
        row_idx = st.number_input("Row index to load", min_value=0, max_value=max(0, len(df)-1), value=0, step=1)
        try:
            row = df.iloc[int(row_idx)]
            if "Projected Margin" in df.columns:
                preload["proj_margin"] = float(row.get("Projected Margin", 0.0))
            if "Alt Line (k)" in df.columns:
                preload["alt_line"] = float(row.get("Alt Line (k)", -2.5))
            if "Logistic Slope (k)" in df.columns:
                preload["k"] = float(row.get("Logistic Slope (k)", 6))
            if "Alt Odds (American)" in df.columns:
                preload["odds"] = float(row.get("Alt Odds (American)", -105))
        except Exception:
            pass

    proj_margin = st.number_input("Projected Margin (points)", value=float(preload.get("proj_margin", 3.2)), step=0.1, format="%.1f")
    alt_line = st.number_input("Alt Spread Line (fav negative)", value=float(preload.get("alt_line", -2.5)), step=0.5, format="%.1f")
    slope_k = st.number_input("Logistic Slope (k)", value=float(preload.get("k", 6.0)), step=0.5, format="%.1f")
    american_odds = st.number_input("FanDuel Odds (American)", value=int(preload.get("odds", -105)), step=5)

    p_you = cover_prob(proj_margin, alt_line, k=slope_k)
    p_book = american_to_implied_p(american_odds)
    dec_odds = american_to_decimal(american_odds)
    edge = p_you - p_book
    f_full = kelly_fraction_full(p_you, dec_odds)
    f_scaled = kelly_mult * f_full
    stake = bankroll * f_scaled
    units = stake / base_unit if base_unit > 0 else 0.0

    st.metric("Cover Probability (Model)", f"{p_you*100:.2f}%")
    st.metric("Book Implied", f"{p_book*100:.2f}%")
    st.metric("Edge", f"{edge*100:+.2f}%")
    st.metric("Decimal Odds", f"{dec_odds:.3f}")
    st.markdown("### Kelly Sizing")
    st.write(f"**Full Kelly f\\***: `{f_full:.4f}`  |  **Scaled (×{kelly_mult:.2f})**: `{f_scaled:.4f}`")
    st.write(f"**Stake**: `${stake:.2f}`  (**{units:.2f}u** @ ${base_unit:.2f}/u)")

# --------- FIRST HALF ---------
elif mode == "First Half":
    st.subheader("First Half Winner")
    preload = {}
    if df is not None:
        st.write("Select a row (from your 'Models - 1H' CSV) to prefill:")
        show_cols = [c for c in df.columns if c in ["Game","1H Rating","Logistic Slope (k1H)","Book 1H Odds (American)"]]
        st.dataframe(df[show_cols] if show_cols else df.head(20))
        row_idx = st.number_input("Row index to load", min_value=0, max_value=max(0, len(df)-1), value=0, step=1)
        try:
            row = df.iloc[int(row_idx)]
            # If "1H Rating" exists, use it directly; else try reconstruct from sub-components
            if "1H Rating" in df.columns and pd.notna(row.get("1H Rating")):
                preload["rating"] = float(row.get("1H Rating", 0.0))
            else:
                # If the sheet has the components:
                l3 = float(row.get("Team 1H PtDiff (L3)", 0.0)) if "Team 1H PtDiff (L3)" in df.columns else 0.0
                season = float(row.get("Team 1H PtDiff (Season)", 0.0)) if "Team 1H PtDiff (Season)" in df.columns else 0.0
                script = float(row.get("Script Edge (+/-)", 0.0)) if "Script Edge (+/-)" in df.columns else 0.0
                preload["rating"] = 0.5*l3 + 0.3*season + 0.2*script
            if "Logistic Slope (k1H)" in df.columns:
                preload["k"] = float(row.get("Logistic Slope (k1H)", 4.0))
            if "Book 1H Odds (American)" in df.columns:
                preload["odds"] = float(row.get("Book 1H Odds (American)", -115))
        except Exception:
            pass

    rating = st.number_input("1H Rating (from your model)", value=float(preload.get("rating", 2.0)), step=0.1, format="%.1f")
    slope_k = st.number_input("Logistic Slope (k1H)", value=float(preload.get("k", 4.0)), step=0.5, format="%.1f")
    american_odds = st.number_input("FanDuel Odds (American)", value=int(preload.get("odds", -115)), step=5)

    p_you = logistic_win_prob(rating, k=slope_k)
    p_book = american_to_implied_p(american_odds)
    dec_odds = american_to_decimal(american_odds)
    edge = p_you - p_book
    f_full = kelly_fraction_full(p_you, dec_odds)
    f_scaled = kelly_mult * f_full
    stake = bankroll * f_scaled
    units = stake / base_unit if base_unit > 0 else 0.0

    st.metric("1H Win Probability (Model)", f"{p_you*100:.2f}%")
    st.metric("Book Implied", f"{p_book*100:.2f}%")
    st.metric("Edge", f"{edge*100:+.2f}%")
    st.metric("Decimal Odds", f"{dec_odds:.3f}")
    st.markdown("### Kelly Sizing")
    st.write(f"**Full Kelly f\\***: `{f_full:.4f}`  |  **Scaled (×{kelly_mult:.2f})**: `{f_scaled:.4f}`")
    st.write(f"**Stake**: `${stake:.2f}`  (**{units:.2f}u** @ ${base_unit:.2f}/u)")

# --------- PLAYER PROP ---------
else:
    st.subheader("Player Prop")
    preload = {}
    if df is not None:
        st.write("Select a row (from your 'Models - Props' CSV) to prefill:")
        show_cols = [c for c in df.columns if c in ["Player","Final Projection","Last5 StDev","Book Line","Book Odds (American)","Bet Side (Over/Under)"]]
        st.dataframe(df[show_cols] if show_cols else df.head(20))
        row_idx = st.number_input("Row index to load", min_value=0, max_value=max(0, len(df)-1), value=0, step=1)
        try:
            row = df.iloc[int(row_idx)]
            if "Final Projection" in df.columns and pd.notna(row.get("Final Projection")):
                preload["proj"] = float(row.get("Final Projection", 95.0))
            if "Last5 StDev" in df.columns and pd.notna(row.get("Last5 StDev")):
                preload["stdev"] = float(row.get("Last5 StDev", 22.0))
            if "Book Line" in df.columns and pd.notna(row.get("Book Line")):
                preload["line"] = float(row.get("Book Line", 86.5))
            if "Book Odds (American)" in df.columns and pd.notna(row.get("Book Odds (American)")):
                preload["odds"] = float(row.get("Book Odds (American)", -120))
            if "Bet Side (Over/Under)" in df.columns and isinstance(row.get("Bet Side (Over/Under)"), str):
                preload["side"] = row.get("Bet Side (Over/Under)").strip().capitalize()
        except Exception:
            pass

    side = st.selectbox("Side", ["Over", "Under"], index=(0 if preload.get("side","Over")=="Over" else 1))
    proj = st.number_input("Your Projection", value=float(preload.get("proj", 95.0)), step=1.0)
    stdev = st.number_input("Std Dev (e.g., last 5 games)", value=float(preload.get("stdev", 22.0)), step=0.5)
    line = st.number_input("Book Line", value=float(preload.get("line", 86.5)), step=0.5)
    american_odds = st.number_input("FanDuel Odds (American)", value=int(preload.get("odds", -120)), step=5)

    if side.lower().startswith("o"):
        p_you = prop_over_prob(proj, stdev, line)
    else:
        p_you = prop_under_prob(proj, stdev, line)

    p_book = american_to_implied_p(american_odds)
    dec_odds = american_to_decimal(american_odds)
    edge = p_you - p_book
    f_full = kelly_fraction_full(p_you, dec_odds)
    f_scaled = kelly_mult * f_full
    stake = bankroll * f_scaled
    units = stake / base_unit if base_unit > 0 else 0.0

    st.metric("Your Probability (Model)", f"{p_you*100:.2f}%")
    st.metric("Book Implied", f"{p_book*100:.2f}%")
    st.metric("Edge", f"{edge*100:+.2f}%")
    st.metric("Decimal Odds", f"{dec_odds:.3f}")
    st.markdown("### Kelly Sizing")
    st.write(f"**Full Kelly f\\***: `{f_full:.4f}`  |  **Scaled (×{kelly_mult:.2f})**: `{f_scaled:.4f}`")
    st.write(f"**Stake**: `${stake:.2f}`  (**{units:.2f}u** @ ${base_unit:.2f}/u)")

st.markdown("---")
st.caption("For educational purposes only. Bet responsibly.")
