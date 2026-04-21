SET hive.tez.java.opts=-Xmx30214m;

SET hivevar:start_date=2024-11-01;
SET hivevar:end_date=2024-11-30;


drop table if exists analytics_pricingteam.HC_renewals_bundle_view;

create table analytics_pricingteam.HC_renewals_bundle_view
AS

WITH exposure AS
(SELECT *, 
         CAST(
            IF (
                HOUR(contract_start_timestamp) = 23,
                DATE_ADD(contract_start_timestamp, 1),
                IF (
                    HOUR(contract_start_timestamp) = 1,
                    DATE_ADD(contract_start_timestamp, -1),
                    DATE_ADD(contract_start_timestamp, 0)
                )
            ) AS DATE
        ) AS contract_start_date
from analytics_bgs_pc.new_exposure),

-- filtering only BCC policies
bcc_policies AS (
    SELECT
        contract_id, 
        business_agreement,
        pricing_key,
        contract_start_date,
        price_group,
        ch_boiler_combi_ind,
        manufactorcode_desc,
        manufactorcode,
        postal_sector,
        case when ch_no_of_radiators is null then 0 else ch_no_of_radiators end as no_of_radiators,
        round(datediff(contract_end_timestamp,install_year)/365) as appl_age_on_renewal,
        round(datediff(contract_end_timestamp, sap_orig_policy_start_timestamp)/365) as policy_tenure_at_renewal,
        contract_start_timestamp,
        contract_end_timestamp,
        policy_start_timestamp,
        policy_end_timestamp,
        tp_fy_zohp_opt_headline_price,
        fy_multi_prod_discount,
        tp_fy_ztpc_tech_product_charge,
        fy_relationship_discount,
        fy_campaign_discount,
        fy_policy_discount,
        actual_policy_discount,
        tp_fy_total_contract_disc,
        fy_gross_price,
        fy_gross_price_policy,
        financial_hardship_flag_optimisation,
        health_vulnerability_flag_optimisation
    FROM exposure
    WHERE contract_start_date >= '${start_date}'
      AND contract_start_date <= '${end_date}'
      AND policy_end_timestamp > current_date()
      AND pricing_key IN ("2SIS", "BNI1", "2FIS", "BNI2")
),

---filtering only CHC policies
chc_policies AS (
    SELECT 
        contract_id,
        business_agreement,
        pricing_key,
        contract_start_date,
        price_group,
        ch_boiler_combi_ind,
        manufactorcode_desc,
        manufactorcode,
        postal_sector,
        case when ch_no_of_radiators is null then 0 else ch_no_of_radiators end as no_of_radiators,
        round(datediff(contract_end_timestamp,install_year)/365) as appl_age_on_renewal,
        round(datediff(contract_end_timestamp, sap_orig_policy_start_timestamp)/365) as policy_tenure_at_renewal,
        contract_start_timestamp,
        contract_end_timestamp,
        policy_start_timestamp,
        policy_end_timestamp,
        tp_fy_zohp_opt_headline_price,
        fy_multi_prod_discount,
        tp_fy_ztpc_tech_product_charge,
        fy_relationship_discount,
        fy_campaign_discount,
        fy_policy_discount,
        actual_policy_discount,
        tp_fy_total_contract_disc,
        fy_gross_price,
        fy_gross_price_policy,
        financial_hardship_flag_optimisation,
        health_vulnerability_flag_optimisation
    FROM exposure
     WHERE contract_start_date >= '${start_date}'
      AND contract_start_date <= '${end_date}'
      AND policy_end_timestamp > current_date()
      AND pricing_key IN ("3SIS", "CNI1", "3FIS", "CNI2")
),


--Filtering only PAD policies
pad_policies AS (
    SELECT 
        contract_id,
        business_agreement,
        pricing_key,
        contract_start_date,
        price_group,
        ch_boiler_combi_ind,
        manufactorcode_desc,
        manufactorcode,
        postal_sector,
        case when ch_no_of_radiators is null then 0 else ch_no_of_radiators end as no_of_radiators,
        round(datediff(contract_end_timestamp,install_year)/365) as appl_age_on_renewal,
        round(datediff(contract_end_timestamp, sap_orig_policy_start_timestamp)/365) as policy_tenure_at_renewal,
        contract_start_timestamp,
        contract_end_timestamp,
        policy_start_timestamp,
        policy_end_timestamp,
        tp_fy_zohp_opt_headline_price,
        fy_multi_prod_discount,
        tp_fy_ztpc_tech_product_charge,
        fy_relationship_discount,
        fy_campaign_discount,
        fy_policy_discount,
        actual_policy_discount,
        tp_fy_total_contract_disc,
        fy_gross_price,
        fy_gross_price_policy,
        financial_hardship_flag_optimisation,
        health_vulnerability_flag_optimisation
    FROM exposure
     WHERE contract_start_date >= '${start_date}'
      AND contract_start_date <= '${end_date}'
      AND policy_end_timestamp > current_date()
      AND pricing_key IN ("2PDI", "DNI1", "2PFI", "DNI2")
),

--Filtering only HEC policies
hec_policies AS (
    SELECT
        contract_id,
        business_agreement,
        pricing_key,
        contract_start_date,
        price_group,
        ch_boiler_combi_ind,
        manufactorcode_desc,
        manufactorcode,
        postal_sector,
        case when ch_no_of_radiators is null then 0 else ch_no_of_radiators end as no_of_radiators,
        round(datediff(contract_end_timestamp,install_year)/365) as appl_age_on_renewal,
        round(datediff(contract_end_timestamp, sap_orig_policy_start_timestamp)/365) as policy_tenure_at_renewal,
        contract_start_timestamp,
        contract_end_timestamp,
        policy_start_timestamp,
        policy_end_timestamp,
        tp_fy_zohp_opt_headline_price,
        fy_multi_prod_discount,
        tp_fy_ztpc_tech_product_charge,
        fy_relationship_discount,
        fy_campaign_discount,
        fy_policy_discount,
        actual_policy_discount,
        tp_fy_total_contract_disc,
        fy_gross_price,
        fy_gross_price_policy,
        financial_hardship_flag_optimisation,
        health_vulnerability_flag_optimisation
    FROM exposure
     WHERE contract_start_date >= '${start_date}'
      AND contract_start_date <= '${end_date}'
      AND policy_end_timestamp > current_date()
      AND pricing_key IN ("HEWI", "HNI1", "HEFI", "HNI2")
),

-- Combine all 4 products into one table where each corresponds to 1 business agreement
all_combined AS (
SELECT 
    -- Join keys
    bcc.business_agreement AS bcc_business_agreement,
    chc.business_agreement AS chc_business_agreement,
    pad.business_agreement AS pad_business_agreement,
    hec.business_agreement AS hec_business_agreement,

    bcc.contract_start_date AS bcc_contract_start_date,
    chc.contract_start_date AS chc_contract_start_date,
    pad.contract_start_date AS pad_contract_start_date,
    hec.contract_start_date AS hec_contract_start_date,

    -- Common fields with aliases
    bcc.pricing_key AS bcc_pricing_key,
    chc.pricing_key AS chc_pricing_key,
    pad.pricing_key AS pad_pricing_key,
    hec.pricing_key AS hec_pricing_key,

    bcc.price_group AS bcc_price_group,
    chc.price_group AS chc_price_group,
    pad.price_group AS pad_price_group,
    hec.price_group AS hec_price_group,

    bcc.ch_boiler_combi_ind AS bcc_ch_boiler_combi_ind,
    chc.ch_boiler_combi_ind AS chc_ch_boiler_combi_ind,
    pad.ch_boiler_combi_ind AS pad_ch_boiler_combi_ind,
    hec.ch_boiler_combi_ind AS hec_ch_boiler_combi_ind,

    bcc.manufactorcode_desc AS bcc_manufactorcode_desc,
    chc.manufactorcode_desc AS chc_manufactorcode_desc,
    pad.manufactorcode_desc AS pad_manufactorcode_desc,
    hec.manufactorcode_desc AS hec_manufactorcode_desc,

    bcc.manufactorcode AS bcc_manufactorcode,
    chc.manufactorcode AS chc_manufactorcode,
    pad.manufactorcode AS pad_manufactorcode,
    hec.manufactorcode AS hec_manufactorcode,

    bcc.postal_sector AS bcc_postal_sector,
    chc.postal_sector AS chc_postal_sector,
    pad.postal_sector AS pad_postal_sector,
    hec.postal_sector AS hec_postal_sector,

    bcc.no_of_radiators AS bcc_no_of_radiators,
    chc.no_of_radiators AS chc_no_of_radiators,
    pad.no_of_radiators AS pad_no_of_radiators,
    hec.no_of_radiators AS hec_no_of_radiators,

    bcc.appl_age_on_renewal AS bcc_appl_age_on_renewal,
    chc.appl_age_on_renewal AS chc_appl_age_on_renewal,
    pad.appl_age_on_renewal AS pad_appl_age_on_renewal,
    hec.appl_age_on_renewal AS hec_appl_age_on_renewal,

    bcc.policy_tenure_at_renewal AS bcc_policy_tenure,
    chc.policy_tenure_at_renewal AS chc_policy_tenure,
    pad.policy_tenure_at_renewal AS pad_policy_tenure,
    hec.policy_tenure_at_renewal AS hec_policy_tenure,

    bcc.contract_start_timestamp AS bcc_contract_start_timestamp,
    chc.contract_start_timestamp AS chc_contract_start_timestamp,
    pad.contract_start_timestamp AS pad_contract_start_timestamp,
    hec.contract_start_timestamp AS hec_contract_start_timestamp,

    bcc.contract_end_timestamp AS bcc_contract_end_timestamp,
    chc.contract_end_timestamp AS chc_contract_end_timestamp,
    pad.contract_end_timestamp AS pad_contract_end_timestamp,
    hec.contract_end_timestamp AS hec_contract_end_timestamp,

    bcc.policy_start_timestamp AS bcc_policy_start_timestamp,
    chc.policy_start_timestamp AS chc_policy_start_timestamp,
    pad.policy_start_timestamp AS pad_policy_start_timestamp,
    hec.policy_start_timestamp AS hec_policy_start_timestamp,

    bcc.policy_end_timestamp AS bcc_policy_end_timestamp,
    chc.policy_end_timestamp AS chc_policy_end_timestamp,
    pad.policy_end_timestamp AS pad_policy_end_timestamp,
    hec.policy_end_timestamp AS hec_policy_end_timestamp,

    bcc.tp_fy_zohp_opt_headline_price AS bcc_tp_fy_zohp_opt_headline_price,
    chc.tp_fy_zohp_opt_headline_price AS chc_tp_fy_zohp_opt_headline_price,
    pad.tp_fy_zohp_opt_headline_price AS pad_tp_fy_zohp_opt_headline_price,
    hec.tp_fy_zohp_opt_headline_price AS hec_tp_fy_zohp_opt_headline_price,

    
    bcc.fy_multi_prod_discount AS bcc_fy_multi_prod_discount,
    chc.fy_multi_prod_discount AS chc_fy_multi_prod_discount,
    pad.fy_multi_prod_discount AS pad_fy_multi_prod_discount,
    hec.fy_multi_prod_discount AS hec_fy_multi_prod_discount,

    bcc.tp_fy_ztpc_tech_product_charge AS bcc_tp_fy_ztpc_tech_product_charge,
    chc.tp_fy_ztpc_tech_product_charge AS chc_tp_fy_ztpc_tech_product_charge,
    pad.tp_fy_ztpc_tech_product_charge AS pad_tp_fy_ztpc_tech_product_charge,
    hec.tp_fy_ztpc_tech_product_charge AS hec_tp_fy_ztpc_tech_product_charge,

    bcc.fy_relationship_discount AS bcc_fy_relationship_discount,
    chc.fy_relationship_discount AS chc_fy_relationship_discount,
    pad.fy_relationship_discount AS pad_fy_relationship_discount,
    hec.fy_relationship_discount AS hec_fy_relationship_discount,

    bcc.fy_campaign_discount AS bcc_fy_campaign_discount,
    chc.fy_campaign_discount AS chc_fy_campaign_discount,
    pad.fy_campaign_discount AS pad_fy_campaign_discount,
    hec.fy_campaign_discount AS hec_fy_campaign_discount,

    bcc.fy_policy_discount AS bcc_fy_policy_discount,
    chc.fy_policy_discount AS chc_fy_policy_discount,
    pad.fy_policy_discount AS pad_fy_policy_discount,
    hec.fy_policy_discount AS hec_fy_policy_discount,

    bcc.actual_policy_discount AS bcc_actual_policy_discount,
    chc.actual_policy_discount AS chc_actual_policy_discount,
    pad.actual_policy_discount AS pad_actual_policy_discount,
    hec.actual_policy_discount AS hec_actual_policy_discount,

    bcc.tp_fy_total_contract_disc AS bcc_tp_fy_total_contract_disc,
    chc.tp_fy_total_contract_disc AS chc_tp_fy_total_contract_disc,
    pad.tp_fy_total_contract_disc AS pad_tp_fy_total_contract_disc,
    hec.tp_fy_total_contract_disc AS hec_tp_fy_total_contract_disc,

    bcc.fy_gross_price AS bcc_fy_gross_price,
    chc.fy_gross_price AS chc_fy_gross_price,
    pad.fy_gross_price AS pad_fy_gross_price,
    hec.fy_gross_price AS hec_fy_gross_price,

    bcc.fy_gross_price_policy AS bcc_fy_gross_price_policy,
    chc.fy_gross_price_policy AS chc_fy_gross_price_policy,
    pad.fy_gross_price_policy AS pad_fy_gross_price_policy,
    hec.fy_gross_price_policy AS hec_fy_gross_price_policy,

    bcc.financial_hardship_flag_optimisation AS bcc_financial_hardship_flag_optimisation,
    chc.financial_hardship_flag_optimisation AS chc_financial_hardship_flag_optimisation,
    pad.financial_hardship_flag_optimisation AS pad_financial_hardship_flag_optimisation,
    hec.financial_hardship_flag_optimisation AS hec_financial_hardship_flag_optimisation,

    bcc.health_vulnerability_flag_optimisation AS bcc_health_vulnerability_flag_optimisation,
    chc.health_vulnerability_flag_optimisation AS chc_health_vulnerability_flag_optimisation,
    pad.health_vulnerability_flag_optimisation AS pad_health_vulnerability_flag_optimisation,
    hec.health_vulnerability_flag_optimisation AS hec_health_vulnerability_flag_optimisation

    FROM bcc_policies bcc

    
FULL OUTER JOIN chc_policies chc 
  ON bcc.business_agreement = chc.business_agreement
  AND bcc.contract_id = chc.contract_id
  AND bcc.contract_start_date = chc.contract_start_date
FULL OUTER JOIN pad_policies pad
  ON COALESCE(bcc.business_agreement, chc.business_agreement) = pad.business_agreement
  AND COALESCE(bcc.contract_id, chc.contract_id) = pad.contract_id
  AND COALESCE(bcc.contract_start_date, chc.contract_start_date) = pad.contract_start_date
FULL OUTER JOIN hec_policies hec
  ON COALESCE(bcc.business_agreement, chc.business_agreement, pad.business_agreement) = hec.business_agreement
  AND COALESCE(bcc.contract_id, chc.contract_id, pad.contract_id) = hec.contract_id
  AND COALESCE(bcc.contract_start_date, chc.contract_start_date, pad.contract_start_date) = hec.contract_start_date),


--create flags for each products
all_combined_product_ind AS (
SELECT *,
       CASE WHEN bcc_business_agreement IS NOT NULL THEN 1 ELSE 0 END AS bcc,
       CASE WHEN chc_business_agreement IS NOT NULL THEN 1 ELSE 0 END AS chc,
       CASE WHEN pad_business_agreement IS NOT NULL THEN 1 ELSE 0 END AS pnd,
       CASE WHEN hec_business_agreement IS NOT NULL THEN 1 ELSE 0 END AS hec
FROM all_combined
),


--create product bundle from above product flags
all_combined_with_bundle AS (
SELECT *,
       CASE 
           WHEN bcc = 1 AND chc = 0 AND pnd = 0 AND hec = 0 THEN 'HC1'
           WHEN bcc = 0 AND chc = 1 AND pnd = 0 AND hec = 0 THEN 'HC2'
           WHEN bcc = 0 AND chc = 1 AND pnd = 1 AND hec = 0 THEN 'HC3'
           WHEN bcc = 0 AND chc = 1 AND pnd = 1 AND hec = 1 THEN 'HC4'
           WHEN bcc = 1 AND chc = 0 AND pnd = 1 AND hec = 0 THEN 'BCC+PAD'
           WHEN bcc = 1 AND chc = 0 AND pnd = 0 AND hec = 1 THEN 'BCC+HEC'
           WHEN bcc = 1 AND chc = 0 AND pnd = 1 AND hec = 1 THEN 'BCC+PAD+HEC'
           WHEN bcc = 0 AND chc = 0 AND pnd = 1 AND hec = 1 THEN 'PAD+HEC'
           WHEN bcc = 0 AND chc = 1 AND pnd = 0 AND hec = 1 THEN 'CHC+HEC'
           WHEN bcc = 0 AND chc = 0 AND pnd = 1 AND hec = 0 THEN 'PAD Standalone'
           WHEN bcc = 0 AND chc = 0 AND pnd = 0 AND hec = 1 THEN 'HEC Standalone'
           ELSE 'Others'
       END AS product_bundle
FROM all_combined_product_ind
)

--calculate overall tenure based on CHC> BCC> PAD> HEC in order of precedence. writing everything to table back
SELECT *,
    CASE 
        WHEN chc = 1 THEN chc_policy_tenure
        WHEN bcc = 1 THEN bcc_policy_tenure
        WHEN pnd = 1 THEN pad_policy_tenure
        WHEN hec = 1 THEN hec_policy_tenure
        ELSE NULL
     END AS selected_policy_tenure_at_renewal
FROM all_combined_with_bundle;



-- pivot everything back to product view

drop table if exists analytics_pricingteam.HC_renewals_product_view;
CREATE TABLE analytics_pricingteam.HC_renewals_product_view AS


WITH unified AS (
SELECT
  'BCC' AS product,
  bcc_business_agreement AS business_agreement,
  bcc_pricing_key AS pricing_key,
  bcc_price_group AS price_group,
  bcc_contract_start_date AS contract_start_date,
  bcc_contract_end_timestamp AS contract_end_timestamp,
  bcc_policy_start_timestamp AS policy_start_timestamp,
  bcc_policy_end_timestamp AS policy_end_timestamp,
  date_add(bcc_contract_end_timestamp,1) AS Renewal_date,
  bcc,
  chc,
  pnd,
  hec,
  product_bundle,
  COALESCE(bcc_ch_boiler_combi_ind, 'Default') AS combi_boiler,
  COALESCE(bcc_manufactorcode_desc,'Default') AS manufactorcode_desc,
  COALESCE(bcc_manufactorcode,'Default') AS manufactorcode,
  COALESCE(bcc_postal_sector,'Default') AS postal_sector,
  COALESCE(bcc_no_of_radiators,99) AS no_of_radiators,
  COALESCE(bcc_appl_age_on_renewal,99) AS appl_age_at_renewal,
  bcc_policy_tenure AS policy_tenure_at_renewal,
  COALESCE(selected_policy_tenure_at_renewal,0) AS tenure_for_discount,
  bcc_tp_fy_zohp_opt_headline_price AS opt_headline_price,
  bcc_fy_multi_prod_discount AS multi_prod_discount,
  bcc_tp_fy_ztpc_tech_product_charge AS tech_product_charge,
  bcc_fy_relationship_discount AS relationship_discount,
  bcc_fy_campaign_discount AS campaign_discount,
  bcc_fy_policy_discount AS fy_policy_discount,
  bcc_actual_policy_discount AS actual_policy_discount,
  bcc_tp_fy_total_contract_disc AS total_contract_disc,
  bcc_fy_gross_price AS fy_gross_price,
  bcc_fy_gross_price_policy AS fy_gross_price_policy,
  bcc_financial_hardship_flag_optimisation AS financial_hardship_flag_optimisation,
  bcc_health_vulnerability_flag_optimisation AS health_vulnerability_flag_optimisation
FROM analytics_pricingteam.HC_renewals_bundle_view
WHERE bcc_business_agreement IS NOT NULL

UNION ALL

SELECT
  'CHC' AS product,
  chc_business_agreement,
  chc_pricing_key,
  chc_price_group,
  chc_contract_start_date,
  chc_contract_end_timestamp,
  chc_policy_start_timestamp,
  chc_policy_end_timestamp,
  date_add(chc_contract_end_timestamp,1),
  bcc,
  chc,
  pnd,
  hec,
  product_bundle,
  COALESCE(chc_ch_boiler_combi_ind, 'Default') AS combi_boiler,
  COALESCE(chc_manufactorcode_desc,'Default') AS manufactorcode_desc,
  COALESCE(chc_manufactorcode,'Default') AS manufactorcode,
  COALESCE(chc_postal_sector,'Default') AS postal_sector,
  COALESCE(chc_no_of_radiators,99) AS no_of_radiators,
  COALESCE(chc_appl_age_on_renewal,99) AS appl_age_at_renewal,
  chc_policy_tenure AS policy_tenure_at_renewal,
  COALESCE(selected_policy_tenure_at_renewal,0) AS tenure_for_discount,
  chc_tp_fy_zohp_opt_headline_price,
  chc_fy_multi_prod_discount,
  chc_tp_fy_ztpc_tech_product_charge,
  chc_fy_relationship_discount,
  chc_fy_campaign_discount,
  chc_fy_policy_discount,
  chc_actual_policy_discount,
  chc_tp_fy_total_contract_disc,
  chc_fy_gross_price,
  chc_fy_gross_price_policy,
  chc_financial_hardship_flag_optimisation AS financial_hardship_flag_optimisation,
  chc_health_vulnerability_flag_optimisation AS health_vulnerability_flag_optimisation
FROM analytics_pricingteam.HC_renewals_bundle_view
WHERE chc_business_agreement IS NOT NULL

UNION ALL

SELECT
  'PAD' AS product,
  pad_business_agreement,
  pad_pricing_key,
  pad_price_group,
  pad_contract_start_date,
  pad_contract_end_timestamp,
  pad_policy_start_timestamp,
  pad_policy_end_timestamp,
  date_add(pad_contract_end_timestamp,1),
  bcc,
  chc,
  pnd,
  hec,
  product_bundle,
  COALESCE(pad_ch_boiler_combi_ind, 'Default') AS combi_boiler,
  COALESCE(pad_manufactorcode_desc,'Default') AS manufactorcode_desc,
  COALESCE(pad_manufactorcode,'Default') AS manufactorcode,
  COALESCE(pad_postal_sector,'Default') AS postal_sector,
  COALESCE(pad_no_of_radiators,99) AS no_of_radiators,
  COALESCE(pad_appl_age_on_renewal,99) AS appl_age_at_renewal,
  pad_policy_tenure AS policy_tenure_at_renewal,
  COALESCE(selected_policy_tenure_at_renewal,0) AS tenure_for_discount,
  pad_tp_fy_zohp_opt_headline_price,
  pad_fy_multi_prod_discount,
  pad_tp_fy_ztpc_tech_product_charge,
  pad_fy_relationship_discount,
  pad_fy_campaign_discount,
  pad_fy_policy_discount,
  pad_actual_policy_discount,
  pad_tp_fy_total_contract_disc,
  pad_fy_gross_price,
  pad_fy_gross_price_policy,
  pad_financial_hardship_flag_optimisation AS financial_hardship_flag_optimisation,
  pad_health_vulnerability_flag_optimisation AS health_vulnerability_flag_optimisation
FROM analytics_pricingteam.HC_renewals_bundle_view
WHERE pad_business_agreement IS NOT NULL

UNION ALL

SELECT
  'HEC' AS product,
  hec_business_agreement,
  hec_pricing_key,
  hec_price_group,
  hec_contract_start_date,
  hec_contract_end_timestamp,
  hec_policy_start_timestamp,
  hec_policy_end_timestamp,
  date_add(hec_contract_end_timestamp,1),
  bcc,
  chc,
  pnd,
  hec,
  product_bundle,
  COALESCE(hec_ch_boiler_combi_ind, 'Default') AS combi_boiler,
  COALESCE(hec_manufactorcode_desc,'Default') AS manufactorcode_desc,
  COALESCE(hec_manufactorcode,'Default') AS manufactorcode,
  COALESCE(hec_postal_sector,'Default') AS postal_sector,
  COALESCE(hec_no_of_radiators,99) AS no_of_radiators,
  COALESCE(hec_appl_age_on_renewal,99) AS appl_age_at_renewal,
  hec_policy_tenure AS policy_tenure_at_renewal,
  COALESCE(selected_policy_tenure_at_renewal,0) AS tenure_for_discount,
  hec_tp_fy_zohp_opt_headline_price,
  hec_fy_multi_prod_discount,
  hec_tp_fy_ztpc_tech_product_charge,
  hec_fy_relationship_discount,
  hec_fy_campaign_discount,
  hec_fy_policy_discount,
  hec_actual_policy_discount,
  hec_tp_fy_total_contract_disc,
  hec_fy_gross_price,
  hec_fy_gross_price_policy,
  hec_financial_hardship_flag_optimisation AS financial_hardship_flag_optimisation,
  hec_health_vulnerability_flag_optimisation AS health_vulnerability_flag_optimisation
FROM analytics_pricingteam.HC_renewals_bundle_view
WHERE hec_business_agreement IS NOT NULL)

      
SELECT *,
       CASE 
           WHEN bcc = 1 OR chc = 1 THEN 'Bundle'
           ELSE 'Standalone'
       END AS bundle_for_score,
	   fy_gross_price_policy - actual_policy_discount - campaign_discount - relationship_discount as lastyear_undiscounted_price,
       case when financial_hardship_flag_optimisation = 0 and health_vulnerability_flag_optimisation = 0 then 0 else 1 end as vulnerable
FROM (
     SELECT *,
         ROW_NUMBER() OVER (
             PARTITION BY business_agreement, pricing_key 
             ORDER BY contract_start_date DESC, contract_end_timestamp DESC
         ) AS rn
     FROM unified
) deduped
WHERE rn = 1;

select 
business_agreement,
pricing_key,
price_group,
product_bundle,
renewal_date as renewal_Date,
combi_boiler,
manufactorcode_desc as manufacturer,
postal_sector,
no_of_radiators as radiators,
appl_age_at_renewal as boiler_age,
tenure_for_discount,
fy_gross_price_policy as ly_customer_price,
bundle_for_score as bundle,
lastyear_undiscounted_price as ly_undiscounted_price
from analytics_pricingteam.HC_renewals_product_view