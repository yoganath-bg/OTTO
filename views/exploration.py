import pandas as pd
import streamlit as st

from utils.theme import page_header, render_table

page_header(
    "MI Snapshot",
    icon="&#128300;",
    subtitle="Product and customer KPI scorecards · Conduct MI compliance monitoring",
)

if 'premium_file' not in st.session_state:
    st.info("Please calculate prices first (Calculate page) to explore results here.")
    st.stop()

premium_file       = st.session_state['premium_file']
premium_scored     = st.session_state.get('premium_scored')       # available after Get Retention
contracts_view     = st.session_state.get('contracts_view')       # available after Calculate
contracts_view_scored = st.session_state.get('contracts_view_scored')  # available after Get Retention

tab_product, tab_customer, tab_conduct = st.tabs(["Product", "Customer", "Conduct MI"])

# ──────────────────────────────────────────────────────────────────────────────
# PRODUCT TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_product:

    m1, m2, m3, m4, m5 = st.columns(5)

    # ── 1. Total Policies ──
    total_policies = len(premium_file)
    tbl1 = (
        premium_file.groupby("pricing_key", as_index=False)
        .size()
        .rename(columns={"size": "Count"})
    )
    with m1:
        st.metric("Total Policies", f"{total_policies:,}")
        render_table(tbl1, compact=True)

    # ── 2. Expiring Premium ──
    with m2:
        if "ly_customer_price" in premium_file.columns:
            expiring_premium = premium_file["ly_customer_price"].sum()
            tbl_exp = (
                premium_file.groupby("pricing_key", as_index=False)["ly_customer_price"]
                .sum()
                .rename(columns={"ly_customer_price": "Expiring_Premium"})
            )
            tbl_exp["Expiring_Premium"] = tbl_exp["Expiring_Premium"].apply(lambda x: f"£{x:,.0f}")
            st.metric("Expiring Premium", f"£{expiring_premium:,.0f}")
            render_table(tbl_exp, compact=True)
        else:
            st.metric("Expiring Premium", "—")
            st.caption("Column `ly_customer_price` not found in data.")

    # ── 3. Quoted Premium ──
    quoted_premium = premium_file["Final_Premium"].sum()
    tbl2 = (
        premium_file.groupby("pricing_key", as_index=False)["Final_Premium"]
        .sum()
        .rename(columns={"Final_Premium": "Quoted_Premium"})
    )
    tbl2["Quoted_Premium"] = tbl2["Quoted_Premium"].apply(lambda x: f"£{x:,.0f}")
    with m3:
        st.metric("Quoted Premium", f"£{quoted_premium:,.0f}")
        render_table(tbl2, compact=True)

    # ── 4. Expected Yield (before discounts) ──
    with m4:
        if premium_scored is not None:
            ps = premium_scored.copy()
            ps["_yield"] = ps["Final_Premium"] * ps["prob_retention"]
            yield_val = ps["_yield"].sum()
            tbl3 = (
                ps.groupby("pricing_key", as_index=False)["_yield"]
                .sum()
                .rename(columns={"_yield": "Expected_Yield"})
            )
            tbl3["Expected_Yield"] = tbl3["Expected_Yield"].apply(lambda x: f"£{x:,.0f}")
            st.metric("Expected Yield (before discounts)", f"£{yield_val:,.0f}")
            render_table(tbl3, compact=True)
        else:
            st.metric("Expected Yield (before discounts)", "—")
            st.caption("Run **Get Retention** on the Calculate page to see this metric.")

    # ── 5. Expected Loss ──
    with m5:
        if premium_scored is not None:
            loss_val = round(premium_scored["prob_churn"].sum())
            tbl4 = (
                premium_scored.groupby("pricing_key", as_index=False)["prob_churn"]
                .sum()
                .rename(columns={"prob_churn": "Expected_Loss"})
            )
            tbl4["Expected_Loss"] = tbl4["Expected_Loss"].round().astype(int)
            st.metric("Expected Loss", f"{loss_val:,}")
            render_table(tbl4, compact=True)
        else:
            st.metric("Expected Loss", "—")
            st.caption("Run **Get Retention** on the Calculate page to see this metric.")


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOMER TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_customer:

    if contracts_view is None:
        st.info("Calculate prices first to see Customer metrics.")
    else:
        BUNDLE_GROUP = ["product_bundle", "bundle_excess"]

        m1, m2, m3, m4, m5 = st.columns(5)

        # ── 1. Total Customers ──
        total_customers = len(contracts_view)
        tbl1 = (
            contracts_view.groupby(BUNDLE_GROUP, as_index=False)
            .size()
            .rename(columns={"size": "Count"})
        )
        with m1:
            st.metric("Total Customers", f"{total_customers:,}")
            render_table(tbl1, compact=True)

        # ── 2. Expiring Premium ──
        with m2:
            if "bundle_customer_price" in contracts_view.columns:
                expiring_premium = contracts_view["bundle_customer_price"].sum()
                tbl_exp = (
                    contracts_view.groupby(BUNDLE_GROUP, as_index=False)["bundle_customer_price"]
                    .sum()
                    .rename(columns={"bundle_customer_price": "Expiring_Premium"})
                )
                tbl_exp["Expiring_Premium"] = tbl_exp["Expiring_Premium"].apply(lambda x: f"£{x:,.0f}")
                st.metric("Expiring Premium", f"£{expiring_premium:,.0f}")
                render_table(tbl_exp, compact=True)
            else:
                st.metric("Expiring Premium", "—")
                st.caption("Column `bundle_customer_price` not found in data.")

        # ── 3. Quoted Premium ──
        quoted_premium = contracts_view["bundle_Final_Premium"].sum()
        tbl2 = (
            contracts_view.groupby(BUNDLE_GROUP, as_index=False)["bundle_Final_Premium"]
            .sum()
            .rename(columns={"bundle_Final_Premium": "Quoted_Premium"})
        )
        tbl2["Quoted_Premium"] = tbl2["Quoted_Premium"].apply(lambda x: f"£{x:,.0f}")
        with m3:
            st.metric("Quoted Premium", f"£{quoted_premium:,.0f}")
            render_table(tbl2, compact=True)

        # ── 4. Expected Yield (before discounts) ──
        with m4:
            if contracts_view_scored is not None:
                cvs = contracts_view_scored.copy()
                cvs["_yield"] = cvs["bundle_Final_Premium"] * cvs["prob_retention"]
                yield_val = cvs["_yield"].sum()
                tbl3 = (
                    cvs.groupby(BUNDLE_GROUP, as_index=False)["_yield"]
                    .sum()
                    .rename(columns={"_yield": "Expected_Yield"})
                )
                tbl3["Expected_Yield"] = tbl3["Expected_Yield"].apply(lambda x: f"£{x:,.0f}")
                st.metric("Expected Yield (before discounts)", f"£{yield_val:,.0f}")
                render_table(tbl3, compact=True)
            else:
                st.metric("Expected Yield (before discounts)", "—")
                st.caption("Run **Get Retention** on the Calculate page to see this metric.")

        # ── 5. Expected Loss ──
        with m5:
            if contracts_view_scored is not None:
                loss_val = round(contracts_view_scored["prob_churn"].sum())
                tbl4 = (
                    contracts_view_scored.groupby(BUNDLE_GROUP, as_index=False)["prob_churn"]
                    .sum()
                    .rename(columns={"prob_churn": "Expected_Loss"})
                )
                tbl4["Expected_Loss"] = tbl4["Expected_Loss"].round().astype(int)
                st.metric("Expected Loss", f"{loss_val:,}")
                render_table(tbl4, compact=True)
            else:
                st.metric("Expected Loss", "—")
                st.caption("Run **Get Retention** on the Calculate page to see this metric.")


# ──────────────────────────────────────────────────────────────────────────────
# CONDUCT MI TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_conduct:

    cost_df = st.session_state.get('processed_data', {}).get('cost')
    summary_file = st.session_state.get('summary_file')

    if cost_df is None or not isinstance(cost_df, pd.DataFrame) or cost_df.empty:
        st.info("No 'cost' sheet found. Upload a rating table that includes a sheet named **cost** with columns: pricing_key, Burning, Variable, Fixed, LR_Threshold, COR_Threshold.")
    elif summary_file is None or summary_file.empty:
        st.info("Calculate prices first to see Conduct MI metrics.")
    else:
        # Compute avg renewal price per pricing_key from the raw summary_file
        avg_renewal = (
            summary_file.groupby("pricing_key", as_index=False)["Final_Premium"]
            .mean()
            .rename(columns={"Final_Premium": "avg_renewal_price"})
        )

        # Normalise cost column names defensively (already lowercased by upload processing)
        cost = cost_df.copy()
        cost.columns = [c.strip().lower() for c in cost.columns]

        required = {"pricing_key", "burning", "variable", "fixed"}
        missing = required - set(cost.columns)
        if missing:
            st.error(f"'cost' sheet is missing columns: {missing}")
        else:
            numeric_cols = ["burning", "variable", "fixed"]
            for c in ["lr_threshold", "cor_threshold"]:
                if c in cost.columns:
                    numeric_cols.append(c)

            cost[numeric_cols] = cost[numeric_cols].apply(pd.to_numeric, errors="coerce")

            keep_cols = ["pricing_key", "burning", "variable", "fixed"]
            if "lr_threshold" in cost.columns:
                keep_cols.append("lr_threshold")
            if "cor_threshold" in cost.columns:
                keep_cols.append("cor_threshold")

            merged = avg_renewal.merge(cost[keep_cols], on="pricing_key", how="inner")

            # Formulae (VAT divisor = 1.12)
            merged["net_price"]  = merged["avg_renewal_price"] / 1.12
            merged["loss_ratio"] = merged["burning"] / merged["net_price"]
            merged["cor"]        = (merged["variable"] + merged["fixed"]) / merged["net_price"]

            # ── colour-coded KPI card helper ──────────────────────────────────
            # Colours: green=#1a7a4a, amber=#b8860b, red=#c0392b (dark enough for white text)
            BAND = 0.01  # ±1 percentage point tolerance band

            def _lr_colour(val, threshold):
                """Loss Ratio: higher than threshold is good (more premium covering burning).
                   Green > threshold+1pp, Amber within ±1pp, Red < threshold-1pp."""
                if pd.isna(val) or pd.isna(threshold):
                    return "#888888"
                thr = threshold  # already a decimal e.g. 0.45
                if val > thr + BAND:
                    return "#1a7a4a"   # above threshold → good → Green
                if val < thr - BAND:
                    return "#c0392b"   # below threshold → bad → Red
                return "#b8860b"       # within band → Amber

            def _cor_colour(val, threshold):
                """COR: lower is better.
                   Green < threshold-1pp, Amber within ±1pp, Red > threshold+1pp."""
                if pd.isna(val) or pd.isna(threshold):
                    return "#888888"
                thr = threshold  # already a decimal e.g. 0.45
                if val > thr + BAND:
                    return "#c0392b"   # above threshold → bad → Red
                if val < thr - BAND:
                    return "#1a7a4a"   # below threshold → good → Green
                return "#b8860b"       # within band → Amber

            def _kpi_card(label, value_str, colour, help_text=""):
                st.markdown(
                    f"""
                    <div title="{help_text}" style="
                        background-color:{colour};
                        border-radius:8px;
                        padding:12px 16px;
                        margin-bottom:8px;
                        text-align:center;
                    ">
                        <div style="color:#ffffff;font-size:0.8rem;font-weight:600;letter-spacing:0.05em;">{label}</div>
                        <div style="color:#ffffff;font-size:1.6rem;font-weight:700;line-height:1.3;">{value_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ── render one column per pricing key ────────────────────────────
            st.markdown("#### Metrics per Pricing Key")

            has_lr_thr  = "lr_threshold"  in merged.columns
            has_cor_thr = "cor_threshold" in merged.columns

            keys = merged["pricing_key"].dropna().tolist()
            if keys:
                cols = st.columns(len(keys))
                for col, (_, row) in zip(cols, merged.iterrows()):
                    with col:
                        st.markdown(f"**{row['pricing_key']}**")
                        net = row["net_price"]
                        lr  = row["loss_ratio"]
                        cor = row["cor"]
                        lr_thr  = row.get("lr_threshold",  float("nan"))
                        cor_thr = row.get("cor_threshold", float("nan"))

                        lr_colour  = _lr_colour(lr,  lr_thr)  if has_lr_thr  else "#0f2067"
                        cor_colour = _cor_colour(cor, cor_thr) if has_cor_thr else "#0f2067"

                        lr_str  = f"{lr:.1%}"  if pd.notna(lr)  else "—"
                        cor_str = f"{cor:.1%}" if pd.notna(cor) else "—"

                        lr_help  = f"Burning / Net Price  |  Threshold: {lr_thr:.1%}"  if has_lr_thr  and pd.notna(lr_thr)  else "Burning / (Avg Renewal Price / 1.12)"
                        cor_help = f"(Variable+Fixed) / Net Price  |  Threshold: {cor_thr:.1%}" if has_cor_thr and pd.notna(cor_thr) else "(Variable + Fixed) / (Avg Renewal Price / 1.12)"

                        _kpi_card("Loss Ratio", lr_str,  lr_colour,  lr_help)
                        _kpi_card("COR",        cor_str, cor_colour, cor_help)
                        st.caption(f"Net Price: £{net:,.2f}" if pd.notna(net) else "Net Price: —")

                # Legend
                st.markdown(
                    """<div style="margin-top:8px;font-size:0.8rem;">
                    <span style="background:#1a7a4a;color:#fff;padding:2px 8px;border-radius:4px;margin-right:6px;">Green</span> Favourable &nbsp;
                    <span style="background:#b8860b;color:#fff;padding:2px 8px;border-radius:4px;margin-right:6px;">Amber</span> Within ±1pp of threshold &nbsp;
                    <span style="background:#c0392b;color:#fff;padding:2px 8px;border-radius:4px;">Red</span> Unfavourable
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.caption("**Abbreviations:** COR = Combined Operating Ratio  |  Net Price = Avg Renewal Price ÷ 1.12 (ex-VAT)  |  pp = percentage points")
            else:
                st.info("No matching pricing keys found between the cost sheet and the calculated prices.")

