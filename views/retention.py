import pandas as pd
import streamlit as st

from utils.bundle_view import build_contracts_view
from utils.constants import DEFAULT_MODEL, MODEL_REGISTRY
from utils.feature_engineering import engineer_features_for_scoring
from utils.scoring import score_via_endpoint
from utils.theme import page_header, section_divider, render_table

page_header(
    "Retention Scoring",
    icon="&#128200;",
    subtitle="Score your book against the Databricks retention model endpoint",
)

if 'premium_file' not in st.session_state:
    st.info("Calculate prices first (Price page) before running retention scoring.")
    st.stop()

# ── Model selector ────────────────────────────────────────────────────────────
selected_model = st.selectbox(
    "Retention Model",
    options=list(MODEL_REGISTRY.keys()),
    index=list(MODEL_REGISTRY.keys()).index(DEFAULT_MODEL),
    help="Select the retention model version to score against.",
)
selected_endpoint = MODEL_REGISTRY[selected_model]

if st.button("Get Retention", type="primary"):
    premium_file = st.session_state['premium_file']

    with st.spinner("Fetching retention scores from model endpoint..."):
        df_for_model = build_contracts_view(premium_file)
        df_feat = engineer_features_for_scoring(df_for_model)

        assert "yoy" in df_feat.columns, "yoy was not created — check premium/price column names"

        df_scored = score_via_endpoint(df_feat, chunk_size=2000, endpoint_name=selected_endpoint)

        premium_file["business_agreement"] = premium_file["business_agreement"].astype(str)
        df_scored["business_agreement"] = df_scored["business_agreement"].astype(str)

        premium_scored = premium_file.merge(
            df_scored[["business_agreement", "prob_retention", "prob_churn"]],
            on="business_agreement",
            how="inner"
        )

        retention_summary = (
            premium_scored
            .groupby("pricing_key", as_index=False)
            .agg(
                mean_prob_retention=("prob_retention", "mean"),
                n_policies=("prob_retention", "size")
            )
            .sort_values("mean_prob_retention", ascending=False)
        )
        retention_summary["mean_prob_retention"] = (
            (retention_summary["mean_prob_retention"] * 100).round(2).astype(str) + "%"
        )
        retention_summary = retention_summary.rename(columns={
            "mean_prob_retention": "Retention",
            "n_policies":          "Volume",
        })

        df_for_model["business_agreement"] = df_for_model["business_agreement"].astype(str)
        contracts_view_scored = df_for_model.merge(
            df_scored[["business_agreement", "prob_retention", "prob_churn"]],
            on="business_agreement",
            how="inner"
        )

        customer_retention_summary = (
            contracts_view_scored
            .groupby(["product_bundle", "bundle_excess"], as_index=False)
            .agg(
                mean_prob_retention=("prob_retention", "mean"),
                n_customers=("prob_retention", "size")
            )
            .sort_values("mean_prob_retention", ascending=False)
        )
        customer_retention_summary["mean_prob_retention"] = (
            (customer_retention_summary["mean_prob_retention"] * 100).round(2).astype(str) + "%"
        )
        customer_retention_summary = customer_retention_summary.rename(columns={
            "mean_prob_retention": "Retention",
            "n_customers":         "Volume",
        })

        st.session_state['retention_summary'] = retention_summary
        st.session_state['customer_retention_summary'] = customer_retention_summary
        st.session_state['premium_scored'] = premium_scored
        st.session_state['contracts_view_scored'] = contracts_view_scored

        st.success("Retention scores fetched successfully!")

# Display results if available (persisted across reruns)
if 'retention_summary' in st.session_state:
    tab_product, tab_customer = st.tabs(["Product", "Customer"])

    with tab_product:
        st.markdown("**Retention Summary by Pricing Key**")
        render_table(st.session_state['retention_summary'])

    with tab_customer:
        st.markdown("**Retention Summary by Product Bundle**")
        render_table(st.session_state['customer_retention_summary'])
