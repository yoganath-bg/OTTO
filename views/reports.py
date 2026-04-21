import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from utils.theme import page_header, section_divider

page_header(
    "Reports",
    icon="&#128202;",
    subtitle="Interactive price distribution, YoY movement and retention analysis",
)

premium_scored        = st.session_state.get('premium_scored')
contracts_view_scored = st.session_state.get('contracts_view_scored')

if premium_scored is None:
    st.info("Run **Get Retention** on the Retention page first to enable charts.")
    st.stop()


def _col(df, name):
    """Case-insensitive column lookup."""
    for c in df.columns:
        if c.lower() == name.lower():
            return c
    return None


PRODUCT_NUMERIC_FACTORS = {"radiators", "boiler_age", "boiler_size", "policy_tenure_at_renewal"}
PRODUCT_FACTORS = [
    "boiler_type", "price_group", "gack_kac", "installedby_bg",
    "radiators", "boiler_age", "boiler_size",
    "autoconsent_renewal_ind", "policy_tenure_at_renewal",
]
CUSTOMER_NUMERIC_FACTORS = {"boiler_age", "boiler_size", "rads", "bundle_tenure"}
CUSTOMER_FACTORS = [
    "product_bundle", "bundle_excess", "boiler_age", "manufacturer",
    "combi", "bg_installed", "boiler_size", "rads", "claims",
    "bundle_gack_kac", "autoconsent_renewal_ind", "bundle_tenure",
]

CHART_H = 360  # uniform chart height for horizontal alignment


def _hist(series, lo, hi, bk, name, color, opacity=1.0):
    return go.Histogram(
        x=series.clip(lo, hi),
        xbins=dict(start=lo, end=hi, size=bk),
        name=name, marker_color=color, opacity=opacity,
    )


def _clip_inputs(series, prefix, n_buckets=40):
    """Lower clip / upper clip / bucket size — used for histograms."""
    p1  = float(series.quantile(0.01))
    p99 = float(series.quantile(0.99))
    span = max(p99 - p1, 1.0)
    w1, w2, w3 = st.columns(3)
    lo = w1.number_input("Lower clip",  value=round(p1,  2), key=f"{prefix}_lo")
    hi = w2.number_input("Upper clip",  value=round(p99, 2), key=f"{prefix}_hi")
    bk = w3.number_input("Bucket size", value=round(span / n_buckets, 2),
                          min_value=0.01, key=f"{prefix}_bk")
    return lo, hi, bk


def _clip_only(series, prefix):
    """Lower clip / upper clip only — used for numeric factors in dual-line chart."""
    p1  = float(series.quantile(0.01))
    p99 = float(series.quantile(0.99))
    w1, w2 = st.columns(2)
    lo = w1.number_input("Lower clip", value=int(p1),  key=f"{prefix}_flo")
    hi = w2.number_input("Upper clip", value=int(p99), key=f"{prefix}_fhi")
    return lo, hi


def _clip_floor(df, col, prefix):
    """Clip numeric column and floor to integer (bucket=1) so groupby sorts correctly."""
    series = pd.to_numeric(df[col], errors='coerce')
    lo, hi = _clip_only(series.dropna(), prefix)
    df = df.copy()
    df[col] = series.clip(lo, hi).round().astype('Int64')
    return df


def _dual_line_chart(grp, x_col, x_label, fp_label, prem_label, height):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Count bars on primary y-axis (light, behind the lines)
    fig.add_trace(go.Bar(x=grp[x_col], y=grp['count'],
                         name="Count", marker_color='#b0c4e8',
                         opacity=0.5, yaxis='y'), secondary_y=False)
    # Avg premium line on primary y-axis
    fig.add_trace(go.Scatter(x=grp[x_col], y=grp['avg_premium'],
                             name=prem_label, mode='lines+markers',
                             line=dict(color='#0f2067')), secondary_y=False)
    # Retention line on secondary y-axis
    fig.add_trace(go.Scatter(x=grp[x_col], y=grp['avg_retention'],
                             name="Avg Prob Retention", mode='lines+markers',
                             line=dict(color='#a50091', dash='dash')), secondary_y=True)
    fig.update_yaxes(title_text=f"{fp_label} / Count", secondary_y=False)
    fig.update_yaxes(title_text="Avg Prob Retention", secondary_y=True, tickformat=".1%")
    fig.update_layout(xaxis_title=x_label, height=height,
                      barmode='overlay',
                      margin=dict(t=10, b=60),
                      legend=dict(orientation="h", y=1.08))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
tab_product, tab_customer = st.tabs(["Product", "Customer"])

# ──────────────────────────────────────────────────────────────────────────────
# PRODUCT TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_product:

    pk_col  = _col(premium_scored, 'pricing_key') or 'pricing_key'
    all_keys = sorted(premium_scored[pk_col].dropna().unique().tolist())
    sel_keys = st.multiselect("Filter by Pricing Key", all_keys, default=all_keys, key="rep_prod_pk")
    df = premium_scored[premium_scored[pk_col].isin(sel_keys)].copy() if sel_keys else premium_scored.copy()

    fp_col  = _col(df, 'final_premium') or 'Final_Premium'
    lyc_col = _col(df, 'ly_customer_price')
    lyu_col = _col(df, 'ly_undiscounted_price')

    ly_options_avail = [c for c in [lyc_col, lyu_col] if c is not None]

    st.markdown("""<hr style="border: 0.5px solid #ccc; margin:12px 0;">""", unsafe_allow_html=True)

    # ── Row 1: Price Distribution | YoY Price Distribution ────────────────────

    # Denominator selector sits outside columns so both charts start at the same height
    if ly_options_avail:
        denom_sel = st.radio("Denominator (for YoY chart)", ly_options_avail,
                             horizontal=True, key="rep_prod_yoy_denom")
    else:
        denom_sel = None

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Price Distribution")
        series = df[fp_col].dropna()
        if not series.empty:
            lo, hi, bk = _clip_inputs(series, "rep_prod_hist")
            fig1 = go.Figure(_hist(series, lo, hi, bk, "Final Premium", '#0f2067'))
            fig1.update_layout(xaxis_title="Final Premium (£)", yaxis_title="Count",
                               bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
            st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown("##### YoY Price Distribution")
        if not ly_options_avail:
            st.info("LY price columns not found in scored data.")
        else:
            valid = df[[fp_col, denom_sel]].dropna()
            if not valid.empty:
                yoy_pct = ((valid[fp_col] / valid[denom_sel]) - 1) * 100
                lo2, hi2, bk2 = _clip_inputs(yoy_pct, "rep_prod_yoy", n_buckets=40)
                fig2 = go.Figure(_hist(yoy_pct, lo2, hi2, bk2, "YoY %", '#85db9c'))
                fig2.update_layout(xaxis_title="YoY Price Change (%)", yaxis_title="Count",
                                   bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
                st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""<hr style="border: 0.5px solid #ccc; margin:12px 0;">""", unsafe_allow_html=True)

    # ── Row 2: Price Movement | Avg Premium & Avg Retention ───────────────────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("##### Price Movement")
        if not ly_options_avail:
            st.info("LY price columns not found in scored data.")
        else:
            ly_mov = st.radio("Compare Renewal against", ly_options_avail,
                              horizontal=True, key="rep_prod_mov_toggle")
            combined = pd.concat([df[fp_col], df[ly_mov]]).dropna()
            if not combined.empty:
                lo3, hi3, bk3 = _clip_inputs(combined, "rep_prod_mov")
                fig3 = go.Figure()
                fig3.add_trace(_hist(df[fp_col], lo3, hi3, bk3, "Renewal Price", '#0f2067', 0.75))
                fig3.add_trace(_hist(df[ly_mov],  lo3, hi3, bk3, ly_mov,         '#b999f6', 0.60))
                fig3.update_layout(barmode='overlay', xaxis_title="Price (£)", yaxis_title="Count",
                                   bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
                st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown("##### Avg Premium & Avg Retention by Factor")
        factor_map = {f: _col(df, f) for f in PRODUCT_FACTORS if _col(df, f)}
        if not factor_map:
            st.info("No matching factor columns found.")
        else:
            x_label = st.selectbox("X-axis factor", list(factor_map.keys()), key="rep_prod_factor")
            x_col   = factor_map[x_label]
            df_f    = df[[x_col, fp_col, 'prob_retention']].copy()

            if x_label in PRODUCT_NUMERIC_FACTORS:
                df_f = _clip_floor(df_f, x_col, "rep_prod_fl")

            df_f['prob_retention'] = pd.to_numeric(df_f['prob_retention'], errors='coerce')
            df_f[fp_col]           = pd.to_numeric(df_f[fp_col],           errors='coerce')

            grp = (df_f.groupby(x_col, as_index=False, observed=True)
                   .agg(avg_premium=(fp_col, 'mean'), avg_retention=('prob_retention', 'mean'),
                        count=(fp_col, 'count')))

            # Numeric factors: sort as numbers; categorical: sort as strings
            if x_label in PRODUCT_NUMERIC_FACTORS:
                grp[x_col] = pd.to_numeric(grp[x_col], errors='coerce')
                grp = grp.sort_values(x_col)
            else:
                grp = grp.sort_values(x_col)

            fig4 = _dual_line_chart(grp, x_col, x_label, "Avg Final Premium (£)", "Avg Final Premium", CHART_H + 40)
            st.plotly_chart(fig4, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOMER TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_customer:
    if contracts_view_scored is None:
        st.info("Run **Get Retention** on the Retention page to see Customer charts.")
    else:
        cdf     = contracts_view_scored.copy()
        bfp_col = _col(cdf, 'bundle_final_premium') or 'bundle_Final_Premium'
        bcp_col = _col(cdf, 'bundle_customer_price') or 'bundle_customer_price'
        pb_col  = _col(cdf, 'product_bundle') or 'product_bundle'
        be_col  = _col(cdf, 'bundle_excess') or 'bundle_excess'

        # Filters
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            all_bundles = sorted(cdf[pb_col].dropna().unique().tolist())
            sel_bundles = st.multiselect("Filter by Product Bundle", all_bundles,
                                         default=all_bundles, key="rep_cust_pb")
        with fcol2:
            all_excess = sorted(cdf[be_col].dropna().unique().tolist()) if be_col in cdf.columns else []
            sel_excess = st.multiselect("Filter by Bundle Excess", all_excess,
                                        default=all_excess, key="rep_cust_be")

        mask = pd.Series(True, index=cdf.index)
        if sel_bundles:
            mask &= cdf[pb_col].isin(sel_bundles)
        if sel_excess and be_col in cdf.columns:
            mask &= cdf[be_col].isin(sel_excess)
        cdf = cdf[mask].copy()

        cly_options = [c for c in [bcp_col] if c is not None and c in cdf.columns]

        st.markdown("""<hr style="border: 0.5px solid #ccc; margin:12px 0;">""", unsafe_allow_html=True)

        # ── Row 1: Bundle Price Distribution | YoY Price Distribution ─────────

        # Denominator selector sits outside columns so both charts start at the same height
        if cly_options:
            cdenom_sel = st.radio("Denominator (for YoY chart)", cly_options,
                                  horizontal=True, key="rep_cust_yoy_denom")
        else:
            cdenom_sel = None

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### Bundle Premium Distribution")
            cseries = cdf[bfp_col].dropna()
            if not cseries.empty:
                clo, chi, cbk = _clip_inputs(cseries, "rep_cust_hist")
                cfig1 = go.Figure(_hist(cseries, clo, chi, cbk, "Bundle Final Premium", '#0f2067'))
                cfig1.update_layout(xaxis_title="Bundle Final Premium (£)", yaxis_title="Count",
                                    bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
                st.plotly_chart(cfig1, use_container_width=True)

        with c2:
            st.markdown("##### YoY Price Distribution")
            if not cly_options:
                st.info("Bundle LY price column not found.")
            else:
                cvalid = cdf[[bfp_col, cdenom_sel]].dropna()
                if not cvalid.empty:
                    cyoy_pct = ((cvalid[bfp_col] / cvalid[cdenom_sel]) - 1) * 100
                    clo2, chi2, cbk2 = _clip_inputs(cyoy_pct, "rep_cust_yoy", n_buckets=40)
                    cfig2 = go.Figure(_hist(cyoy_pct, clo2, chi2, cbk2, "YoY %", '#85db9c'))
                    cfig2.update_layout(xaxis_title="YoY Price Change (%)", yaxis_title="Count",
                                        bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
                    st.plotly_chart(cfig2, use_container_width=True)

        st.markdown("""<hr style="border: 0.5px solid #ccc; margin:12px 0;">""", unsafe_allow_html=True)

        # ── Row 2: Price Movement | Avg Bundle Premium & Avg Retention ─────────
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("##### Price Movement")
            if not cly_options:
                st.info("Bundle LY price column not found.")
            else:
                cly_mov = cly_options[0]
                ccombined = pd.concat([cdf[bfp_col], cdf[cly_mov]]).dropna()
                if not ccombined.empty:
                    clo3, chi3, cbk3 = _clip_inputs(ccombined, "rep_cust_mov")
                    cfig3 = go.Figure()
                    cfig3.add_trace(_hist(cdf[bfp_col], clo3, chi3, cbk3, "Renewal Premium", '#0f2067', 0.75))
                    cfig3.add_trace(_hist(cdf[cly_mov],  clo3, chi3, cbk3, "LY Customer Price", '#b999f6', 0.60))
                    cfig3.update_layout(barmode='overlay', xaxis_title="Price (£)", yaxis_title="Count",
                                        bargap=0.05, height=CHART_H, margin=dict(t=10, b=40))
                    st.plotly_chart(cfig3, use_container_width=True)

        with c4:
            st.markdown("##### Avg Bundle Premium & Avg Retention by Factor")
            cfactor_map = {f: _col(cdf, f) for f in CUSTOMER_FACTORS if _col(cdf, f)}
            if not cfactor_map:
                st.info("No matching factor columns found.")
            else:
                cx_label = st.selectbox("X-axis factor", list(cfactor_map.keys()), key="rep_cust_factor")
                cx_col   = cfactor_map[cx_label]
                cdf_f    = cdf[[cx_col, bfp_col, 'prob_retention']].copy()

                if cx_label in CUSTOMER_NUMERIC_FACTORS:
                    cdf_f = _clip_floor(cdf_f, cx_col, "rep_cust_fl")

                cdf_f['prob_retention'] = pd.to_numeric(cdf_f['prob_retention'], errors='coerce')
                cdf_f[bfp_col]          = pd.to_numeric(cdf_f[bfp_col],          errors='coerce')

                cgrp = (cdf_f.groupby(cx_col, as_index=False, observed=True)
                        .agg(avg_premium=(bfp_col, 'mean'), avg_retention=('prob_retention', 'mean'),
                             count=(bfp_col, 'count')))

                if cx_label in CUSTOMER_NUMERIC_FACTORS:
                    cgrp[cx_col] = pd.to_numeric(cgrp[cx_col], errors='coerce')
                    cgrp = cgrp.sort_values(cx_col)
                else:
                    cgrp = cgrp.sort_values(cx_col)

                cfig4 = _dual_line_chart(cgrp, cx_col, cx_label, "Avg Bundle Premium (£)", "Avg Bundle Premium", CHART_H + 40)
                st.plotly_chart(cfig4, use_container_width=True)


