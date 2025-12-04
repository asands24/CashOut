# 🏈 README: NFL Betting Calculator + Google Sheets

This is a **Streamlit** application designed to serve as an **NFL Betting Calculator** that integrates with your personal **Google Sheets** betting models.

It allows you to calculate the **edge** (difference between your model's probability and the book's implied probability) and determine the optimal **Kelly Criterion stake size** for four main betting markets: Moneyline, Alt Spreads, First Half Winner, and Player Props.

https://cashout-nfm6kkvsukc8mgbbeubnom.streamlit.app/
---

## ✨ Features

* **Market-Specific Calculations:** Supports Moneyline, Alternative Spreads, First Half Winner, and Player Prop bets.
* **Google Sheets Integration:** Load CSV data directly from a publicly-published Google Sheet to pre-fill inputs based on your existing models.
* **Odds Conversion:** Converts American odds to Decimal odds and calculates the Book's Implied Probability.
* **Probability Modeling:**
    * Uses a **Logistic function** for Moneyline, Alt Spread, and First Half probabilities based on projected margins/ratings.
    * Uses a **Normal CDF** (Standard Normal Distribution) for Player Prop over/under probabilities based on projection and standard deviation.
* **Kelly Sizing:** Calculates the **Full Kelly Criterion fraction ($f^{*}$)** and a **Scaled Kelly Stake** (using a customizable multiplier) to determine the optimal bet size in both dollars and units.

---

## 🛠️ Core Calculations

The application relies on several core helper functions for its logic:

* **Odds Conversion:**
    * `american_to_implied_p`: Converts American odds to the implied win probability for the sportsbook.
    * `american_to_decimal`: Converts American odds to Decimal odds.
* **Win/Cover Probability:**
    * `logistic_win_prob`: Calculates win probability using a **logistic function** $P = \frac{1}{1 + e^{-(margin/k)}}$ (used for Moneyline and First Half).
    * `cover_prob`: Calculates the probability of covering a spread using a logistic function based on the projected margin relative to the line.
    * `prop_over_prob` / `prop_under_prob`: Calculates player prop probabilities (Over/Under) using the **Normal Cumulative Distribution Function ($CDF$)**: $P = \int_{-\infty}^{x} \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{1}{2}(\frac{t-\mu}{\sigma})^2} dt$ (where $\mu$ is the projection and $\sigma$ is the standard deviation). 

[Image of Normal Distribution Bell Curve]

* **Bankroll Management:**
    * `kelly_fraction_full`: Calculates the **Full Kelly Criterion fraction ($f^{*}$)** using the formula: $$f^* = \frac{b p - q}{b}$$ where $p$ is your win probability, $q = 1-p$ is your loss probability, and $b$ is the decimal odds minus 1 (net odds).

---

## 🖥️ UI (Streamlit Layout)

The application features a simple, single-page layout:

* **Sidebar:**
    * **Bankroll & Settings:** Input for **Current Bankroll**, **Base Unit** value, and a **Kelly Multiplier** (e.g., 0.5 for Half Kelly).
    * **Google Sheets Loader:** An input field for pasting a **published CSV URL** from Google Sheets.
* **Main Body:**
    * A **radio button** to select the market: **Moneyline**, **Alt Spread**, **First Half**, or **Player Prop**.
    * **Data Preloading:** If a CSV is loaded, a dataframe is displayed, and you can select a row index to automatically prefill the inputs.
    * **Input Fields:** Market-specific inputs (e.g., *Your Win Probability*, *Projected Margin*, *Book Line*, *Std Dev*, etc.)
    * **Output Metrics:** Displays key metrics:
        * Your Model Probability
        * Book Implied Probability
        * **Edge** (in percent)
        * Decimal Odds
    * **Kelly Sizing Output:** Displays the Full and Scaled Kelly fractions, the final calculated **Stake** (in $), and the equivalent **Units**.

---

## 🔗 Google Sheets Integration Guide

To use the pre-fill feature:

1.  In your Google Sheet containing your betting model data (e.g., a tab named "Models - Team" or "Models - Props").
2.  Go to **File** → **Share** → **Publish to web**.
3.  Select the **single tab** you want to load.
4.  Choose the format **Comma-separated values (.csv)**.
5.  Copy the generated URL and paste it into the **"Paste CSV URL (published sheet)"** field in the Streamlit app's sidebar.

**Note:** The app looks for specific column headers (like `Projected Margin`, `Book Odds (American)`, `Final Projection`, etc.) to automatically match and load data.

---

Would you like a more detailed explanation of the **Kelly Criterion** or one of the **probability models** (Logistic or Normal CDF)?
