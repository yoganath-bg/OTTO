# ---------------------------------------------------------------------------
# constants.py
# Central store for all app-wide constants.
# ---------------------------------------------------------------------------

# --- Rating table column rename maps -------------------------------------------
RENAME_MAPS = {
    "Base_Price":      {"price": "f_base_price"},
    "ASV_Price":       {"price": "f_asv_price"},
    "Boiler_Type":     {"value": "f_boiler_type"},
    "Manufacturer":    {"value": "f_manufacturer"},
    "Postal_Sector":   {"value": "f_postal_sector"},
    "Radiators":       {"value": "f_radiators"},
    "Boiler_age":      {"value": "f_boiler_age"},
    "Tenure_Discount": {"value": "f_tenure_discount"},
    "Caps_Collar":     {"collar": "f_collar", "cap": "f_cap"},
    "Min_Max":         {"maximum_premium": "f_max", "minimum_premium": "f_min"},
}

# --- Bundle view join keys -------------------------------------------------------
KEY_COLS  = ["business_agreement", "contract_id", "contract_start_date"]
KEYS_PLUS = ["business_agreement", "contract_id", "contract_start_date", "contract_end_date"]

# --- Retention model: bundles where boiler/rad features are not applicable -------
BUNDLES_NOT_APPLICABLE = ["PAD+HEC", "PAD Standalone", "HEC Standalone"]

# --- Retention model: fixed top-10 manufacturer categories ----------------------
FIXED_TOP10_MANUFACTURERS = {
    "Alpha Therm Ltd",
    "Baxi Heating Ltd",
    "Default",
    "Glow Worm",
    "Ideal Boilers",
    "MAIN GAS APPLIANCES LTD",
    "Potterton Myson Ltd",
    "Vaillant",
    "Vokera",
    "Worcester Heat Systems Ltd",
}

# --- Retention model serving endpoint -------------------------------------------
ENDPOINT_NAME = "retention_calibrated"

# --- Retention model registry ---------------------------------------------------
# Maps user-facing model display names to Databricks serving endpoint names.
# To add a new model version: add an entry below with its endpoint name.
# To retire a version: remove or comment-out its entry.
MODEL_REGISTRY: dict[str, str] = {
    "Retention.pricing.1.0.GLM": "retention_calibrated",
    "Retention.pricing.1.1.XGB": "retention_calibrated",
    "Retention.pricing.1.2.lightGBM": "retention_calibrated",
    "Retention.CDAO.1.0":    "retention_calibrated",
    "Retention.CDAO.1.1":    "retention_calibrated",
}

# Default model shown in the dropdown (must be a key in MODEL_REGISTRY)
DEFAULT_MODEL = "Retention.pricing.1.2.lightGBM"

# --- Retention model feature lists ----------------------------------------------
FEATURE_COLS = [
    "product_bundle",
    "manufacturer_cat",
    "combi",
    "bg_installed",
    "bundle_excess",
    "autoconsent_renewal_ind",
    "bundle_gack_kac",
    "campaign_discounted",
    "retention_discounted",
    "bundle_tenure",
    "boiler_age",
    "boiler_size",
    "rads",
    "claims",
    "boiler_age_applicable",
    "manufacturer_applicable",
    "combi_applicable",
    "bg_installed_applicable",
    "boiler_size_applicable",
    "rads_applicable",
    "boiler_age_is_missing",
    "boiler_size_is_missing",
    "rads_is_missing",
    "yoy",
    "yoy_is_missing",
    "contract_start_month_sin",
    "contract_start_month_cos",
]

CATEGORICAL_COLS = [
    "product_bundle",
    "bundle_excess",
    "autoconsent_renewal_ind",
    "bundle_gack_kac",
    "campaign_discounted",
    "retention_discounted",
    "combi",
    "bg_installed",
    "manufacturer_cat",
]

NUMERIC_COLS = [
    "bundle_tenure",
    "boiler_age", "boiler_size", "rads", "claims", "yoy",
    "boiler_age_applicable", "manufacturer_applicable", "combi_applicable",
    "bg_installed_applicable", "boiler_size_applicable", "rads_applicable",
    "boiler_age_is_missing", "boiler_size_is_missing", "rads_is_missing",
    "contract_start_month_sin", "contract_start_month_cos",
]

# Sentinel values used to fill NaN numerics before JSON serialisation to endpoint
SENTINELS = {
    "boiler_age":  1.0,
    "boiler_size": 10.0,
    "rads":        0.0,
    "yoy":         1.0,
}

# --- Summary / analysis column selection ----------------------------------------
COLUMNS_FOR_ANALYSIS = [
    "Business Agreement", "Renewal Date", "pricing_key", "price_group",
    "combi_boiler", "manufacturer", "postal_sector", "radiators", "boiler_age",
    "tenure_for_discount", "bundle", "ly_customer_price",
    "c_tenure_discount", "Discounted_Premium", "Final_Premium",
]
