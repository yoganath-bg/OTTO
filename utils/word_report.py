"""
word_report.py - Generates a genuine .docx file with no external dependencies.
A .docx is a ZIP archive of WordprocessingML XML files, built here using
Python stdlib zipfile + io. Word opens it natively without any format errors.
"""

import io
import zipfile
from datetime import datetime

import pandas as pd


_NAVY  = "0f2067"
_MINT  = "85db9c"
_PINK  = "d03e9d"
_LGREY = "f4f6fb"
_GREEN = "1a7a4a"
_AMBER = "b8860b"
_RED   = "c0392b"
_GREY  = "888888"
_WHITE = "ffffff"
_DGREY = "6b7280"
_BLACK = "111111"

_STATUS = {
    _GREEN: "Favourable",
    _AMBER: "Within \u00b11pp",
    _RED:   "Unfavourable",
    _GREY:  "No Threshold",
}


def _lr_fill(val, thr):
    BAND = 0.01
    if pd.isna(val) or pd.isna(thr):
        return _GREY
    return _GREEN if val > thr + BAND else (_RED if val < thr - BAND else _AMBER)


def _cor_fill(val, thr):
    BAND = 0.01
    if pd.isna(val) or pd.isna(thr):
        return _GREY
    return _RED if val > thr + BAND else (_GREEN if val < thr - BAND else _AMBER)


def _x(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _run(text, bold=False, fg=None, sz=18):
    fg = fg or _BLACK
    b  = "<w:b/><w:bCs/>" if bold else ""
    return (
        f"<w:r><w:rPr>{b}"
        f'<w:color w:val="{fg}"/>'
        f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
        f"</w:rPr>"
        f'<w:t xml:space="preserve">{_x(text)}</w:t></w:r>'
    )


def _para(content, jc="left", before=60, after=60):
    return (
        f"<w:p><w:pPr>"
        f'<w:jc w:val="{jc}"/>'
        f'<w:spacing w:before="{before}" w:after="{after}"/>'
        f"</w:pPr>{content}</w:p>"
    )


def _tc(para_xml, fill=None, span=1, width=None):
    fill  = fill or _WHITE
    sp_el = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
    wd_el = f'<w:tcW w:w="{width}" w:type="dxa"/>' if width else ""
    return (
        f"<w:tc><w:tcPr>{sp_el}{wd_el}"
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
        f"<w:tcMar>"
        f'<w:top    w:w="80"  w:type="dxa"/>'
        f'<w:left   w:w="120" w:type="dxa"/>'
        f'<w:bottom w:w="80"  w:type="dxa"/>'
        f'<w:right  w:w="120" w:type="dxa"/>'
        f"</w:tcMar>"
        f"</w:tcPr>{para_xml}</w:tc>"
    )


def _tr(*tcs):
    return f"<w:tr>{''.join(tcs)}</w:tr>"


def _spacer_para():
    return "<w:p><w:pPr><w:spacing w:before='60' w:after='60'/></w:pPr></w:p>"


def _table(rows, col_widths):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)
    bdr = (
        "<w:tblBorders>"
        '<w:top    w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:left   w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:right  w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        "</w:tblBorders>"
    )
    return (
        f"<w:tbl>"
        f"<w:tblPr>"
        f'<w:tblW w:w="5000" w:type="pct"/>'
        f'<w:jc w:val="left"/>'
        f"{bdr}"
        f"</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{''.join(rows)}"
        f"</w:tbl>"
    )


_CT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml"  ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml"'
    ' ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

_PKG_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1"'
    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
    ' Target="word/document.xml"/>'
    "</Relationships>"
)

_WORD_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
)

_DOC_NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" '
    'mc:Ignorable="w14 w15"'
)


def build_run_summary_docx(
    premium_file,
    premium_scored,
    processed_data,
    endpoint_name,
    prepared_by,
    prepared_at,
):
    """Return bytes of a genuine .docx file. Use .docx extension when downloading."""

    total_policies = len(premium_file)
    quoted_premium = (
        premium_file["Final_Premium"].sum()
        if "Final_Premium" in premium_file.columns else 0.0
    )
    exp_loss = None
    if premium_scored is not None and "prob_churn" in premium_scored.columns:
        exp_loss = round(premium_scored["prob_churn"].sum())

    src = (
        premium_scored
        if premium_scored is not None and "pricing_key" in premium_scored.columns
        else premium_file
    )

    W  = 9026
    C1 = int(W * 0.30)
    C2 = W - C1
    body = []

    # Cover + Meta
    cover = []
    cover.append(_tr(_tc(
        _para(_run("OTTO  \u00b7  Pricing Run Summary", bold=True, fg=_WHITE, sz=40), before=100, after=100),
        fill=_NAVY, span=2, width=W,
    )))
    cover.append(_tr(_tc(
        _para(_run("BG S&S Pricing Engine  |  Home Care 3.0  |  Internal use only", fg=_NAVY, sz=18)),
        fill=_MINT, span=2, width=W,
    )))
    cover.append(_tr(_tc(_para(_run(" ", sz=8)), fill=_WHITE, span=2, width=W)))
    for lbl, val in [
        ("Prepared By",        prepared_by),
        ("Prepared At",        prepared_at.strftime("%d %B %Y  %H:%M:%S")),
        ("Retention Endpoint", endpoint_name),
    ]:
        cover.append(_tr(
            _tc(_para(_run(lbl, bold=True, fg=_NAVY,  sz=18)), fill=_LGREY, width=C1),
            _tc(_para(_run(val, bold=False, fg=_BLACK, sz=18)), fill=_WHITE, width=C2),
        ))
    body.append(_table(cover, [C1, C2]))
    body.append(_spacer_para())

    # Portfolio Overview
    port = []
    port.append(_tr(_tc(
        _para(_run("1  \u00b7  Portfolio Overview", bold=True, fg=_WHITE, sz=22)),
        fill=_PINK, span=2, width=W,
    )))
    for lbl, val in [
        ("Total Policies",                f"{total_policies:,}"),
        ("Quoted Premium",                f"\u00a3{quoted_premium:,.2f}"),
        ("Expected Loss (Product Total)", f"{exp_loss:,}" if exp_loss is not None else "Run Retention model first"),
    ]:
        port.append(_tr(
            _tc(_para(_run(lbl, bold=True, fg=_NAVY,  sz=18)), fill=_LGREY, width=C1),
            _tc(_para(_run(val, bold=False, fg=_BLACK, sz=18)), fill=_WHITE, width=C2),
        ))
    body.append(_table(port, [C1, C2]))
    body.append(_spacer_para())

    # Price Summary
    if src is not None and "pricing_key" in src.columns and "Final_Premium" in src.columns:
        has_ret = premium_scored is not None and "prob_retention" in (premium_scored.columns if premium_scored is not None else [])
        agg_d = {"Final_Premium": ["count", "mean", "min", "max"]}
        if has_ret:
            agg_d["prob_retention"] = "mean"
        pk = src.groupby("pricing_key").agg(agg_d).reset_index()
        pk.columns = (
            ["Pricing Key", "# Policies", "Avg Premium", "Min Premium", "Max Premium"]
            + (["Avg Retention"] if has_ret else [])
        )
        hdrs2 = ["Pricing Key", "# Policies", "Avg Premium", "Min Premium", "Max Premium"]
        if has_ret:
            hdrs2.append("Avg Retention")
        nc2   = len(hdrs2)
        cw2   = [W // nc2] * nc2
        cw2[-1] = W - sum(cw2[:-1])
        prows = []
        prows.append(_tr(_tc(
            _para(_run("2  \u00b7  Policy & Price Summary by Pricing Key", bold=True, fg=_WHITE, sz=22)),
            fill=_PINK, span=nc2, width=W,
        )))
        prows.append(_tr(*[
            _tc(_para(_run(h, bold=True, fg=_WHITE, sz=18)), fill=_NAVY, width=cw2[i])
            for i, h in enumerate(hdrs2)
        ]))
        for _, row in pk.iterrows():
            v = [
                str(row["Pricing Key"]),
                f"{int(row['# Policies']):,}",
                f"\u00a3{row['Avg Premium']:,.2f}",
                f"\u00a3{row['Min Premium']:,.2f}",
                f"\u00a3{row['Max Premium']:,.2f}",
            ]
            if has_ret:
                v.append(f"{row['Avg Retention']:.1%}")
            prows.append(_tr(
                _tc(_para(_run(v[0], bold=True, fg=_NAVY, sz=18)), fill=_LGREY, width=cw2[0]),
                *[_tc(_para(_run(v[i], sz=18), jc="right"), fill=_WHITE, width=cw2[i]) for i in range(1, nc2)],
            ))
        body.append(_table(prows, cw2))
        body.append(_spacer_para())

    # Conduct MI
    cost_df = (processed_data or {}).get("cost")
    if cost_df is not None and isinstance(cost_df, pd.DataFrame) and not cost_df.empty:
        cost = cost_df.copy()
        cost.columns = cost.columns.astype(str).str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
        req = {"pricing_key", "burning", "variable", "fixed"}
        if req.issubset(set(cost.columns)) and src is not None and "Final_Premium" in src.columns:
            avg_rp = (
                src.groupby("pricing_key", as_index=False)["Final_Premium"]
                .mean().rename(columns={"Final_Premium": "avg_renewal_price"})
            )
            keep = ["pricing_key", "burning", "variable", "fixed"]
            has_lr  = "lr_threshold"  in cost.columns
            has_cor = "cor_threshold" in cost.columns
            if has_lr:  keep.append("lr_threshold")
            if has_cor: keep.append("cor_threshold")
            m = avg_rp.merge(cost[keep], on="pricing_key", how="inner")
            m["net_price"]  = m["avg_renewal_price"] / 1.12
            m["loss_ratio"] = m["burning"] / m["net_price"]
            m["cor"]        = (m["variable"] + m["fixed"]) / m["net_price"]
            hdrs3 = ["Pricing Key", "Net Price", "Loss Ratio", "COR"]
            if has_lr:  hdrs3.append("LR Threshold")
            if has_cor: hdrs3.append("COR Threshold")
            hdrs3 += ["LR Status", "COR Status"]
            nc3   = len(hdrs3)
            pk_w3 = int(W * 0.20)
            rw    = (W - pk_w3) // (nc3 - 1)
            cw3   = [pk_w3] + [rw] * (nc3 - 2) + [W - pk_w3 - rw * (nc3 - 2)]
            mrows = []
            mrows.append(_tr(_tc(
                _para(_run("3  \u00b7  Conduct MI \u2014 Loss Ratio & COR by Pricing Key", bold=True, fg=_WHITE, sz=22)),
                fill=_PINK, span=nc3, width=W,
            )))
            mrows.append(_tr(*[
                _tc(_para(_run(h, bold=True, fg=_WHITE, sz=18)), fill=_NAVY, width=cw3[i])
                for i, h in enumerate(hdrs3)
            ]))
            nd = nc3 - 2
            for _, row in m.iterrows():
                lr     = row["loss_ratio"]
                cv     = row["cor"]
                lrt    = row.get("lr_threshold",  float("nan"))
                cort   = row.get("cor_threshold", float("nan"))
                lr_bg  = _lr_fill(lr, lrt)  if has_lr  else _GREY
                cor_bg = _cor_fill(cv, cort) if has_cor else _GREY
                v3 = [
                    str(row["pricing_key"]),
                    f"\u00a3{row['net_price']:,.2f}",
                    f"{lr:.1%}"  if pd.notna(lr) else "\u2014",
                    f"{cv:.1%}"  if pd.notna(cv) else "\u2014",
                ]
                if has_lr:  v3.append(f"{lrt:.1%}"  if pd.notna(lrt)  else "\u2014")
                if has_cor: v3.append(f"{cort:.1%}" if pd.notna(cort) else "\u2014")
                v3 += [_STATUS[lr_bg], _STATUS[cor_bg]]
                dcells = [
                    _tc(_para(_run(v3[0], bold=True, fg=_NAVY, sz=18)), fill=_LGREY, width=cw3[0])
                ] + [
                    _tc(_para(_run(v3[i], sz=18), jc="right"), fill=_WHITE, width=cw3[i])
                    for i in range(1, nd)
                ]
                scells = [
                    _tc(_para(_run(v3[nc3-2], bold=True, fg=_WHITE, sz=18), jc="center"), fill=lr_bg,  width=cw3[nc3-2]),
                    _tc(_para(_run(v3[nc3-1], bold=True, fg=_WHITE, sz=18), jc="center"), fill=cor_bg, width=cw3[nc3-1]),
                ]
                mrows.append(_tr(*dcells, *scells))
            mrows.append(_tr(_tc(
                _para(_run(
                    "Colour key:  Green = Favourable  |  Amber = Within \u00b11pp  |  Red = Unfavourable"
                    "   \u2014   Net Price = Avg Renewal Price \u00f7 1.12 (ex-VAT)",
                    fg=_DGREY, sz=15,
                )),
                fill=_WHITE, span=nc3, width=W,
            )))
            body.append(_table(mrows, cw3))
            body.append(_spacer_para())

    body.append(_para(
        _run("Generated by OTTO  |  BG S&S Pricing Engine HC3.0  |  Internal use only", fg=_DGREY, sz=15),
        jc="center",
    ))

    sect = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>'
        "</w:sectPr>"
    )
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_DOC_NS}>"
        f"<w:body>{''.join(body)}{sect}</w:body>"
        "</w:document>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",          _CT.encode("utf-8"))
        zf.writestr("_rels/.rels",                  _PKG_RELS.encode("utf-8"))
        zf.writestr("word/document.xml",            doc_xml.encode("utf-8"))
        zf.writestr("word/_rels/document.xml.rels", _WORD_RELS.encode("utf-8"))
    return buf.getvalue()
