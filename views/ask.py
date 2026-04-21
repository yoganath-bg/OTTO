import base64
import streamlit as st
import streamlit.components.v1 as components

# ── Page header: logo + title side by side ───────────────────────────────────
with open("Diagnostics_Lab_green.png", "rb") as _f:
    _logo_b64 = base64.b64encode(_f.read()).decode()

components.html(
    f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:#f4f6fb;font-family:Inter,Arial,sans-serif;padding:4px 0 8px;}}
    .header{{display:flex;align-items:center;gap:20px;}}
    .header img{{height:64px;width:auto;object-fit:contain;}}
    .header h1{{font-size:2.2rem;font-weight:300;color:#0f2067;
                letter-spacing:-0.01em;margin:0;}}
    .header h1 strong{{color:#85db9c;font-weight:800;}}
    </style></head><body>
    <div class="header">
        <img src="data:image/png;base64,{_logo_b64}" alt="DiagnostAIcs Lab logo"/>
        <h1>Diagnost<strong>AI</strong>cs Lab</h1>
    </div>
    </body></html>""",
    height=90,
    scrolling=False,
)

# ── Coming Soon banner ────────────────────────────────────────────────────────
components.html(
    """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#f4f6fb;font-family:Inter,Arial,sans-serif;padding:0;}
    .banner{
        background:linear-gradient(135deg,#0f2067 0%,#152880 60%,#1a3399 100%);
        border-radius:12px;padding:20px 28px;display:flex;
        align-items:center;gap:16px;
    }
    .pulse{width:12px;height:12px;border-radius:50%;background:#85db9c;
        flex-shrink:0;
        animation:pulse 1.8s ease-in-out infinite;}
    @keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(133,219,156,0.4);}
        50%{box-shadow:0 0 0 8px rgba(133,219,156,0);}}
    .txt{color:#fff;}
    .txt h2{font-size:1rem;font-weight:700;letter-spacing:0.05em;
        text-transform:uppercase;margin-bottom:4px;color:#85db9c;}
    .txt p{font-size:0.88rem;color:#c8d0e8;line-height:1.5;}
    </style></head><body>
    <div class="banner">
        <div class="pulse"></div>
        <div class="txt">
            <h2>&#x1F6A7;&nbsp; Coming Soon</h2>
            <p>We&rsquo;re building an AI-powered diagnostic workspace for pricing analysts.
               Expect natural language querying, automated segment analysis, and
               live what-if simulations — all in one place.</p>
        </div>
    </div>
    </body></html>""",
    height=120,
    scrolling=False,
)

st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)

# ── Section 1: What you'll be able to do ─────────────────────────────────────
components.html(
    """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#f4f6fb;font-family:Inter,Arial,sans-serif;padding:0 0 8px;}
    h3{font-size:0.78rem;font-weight:700;text-transform:uppercase;
        letter-spacing:0.1em;color:#6b7280;margin-bottom:14px;}
    .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}
    .card{background:#fff;border:1px solid #e0e6f0;border-left:4px solid #0f2067;
        border-radius:8px;padding:14px 16px;
        display:flex;align-items:flex-start;gap:12px;}
    .icon{font-size:1.3rem;flex-shrink:0;margin-top:1px;}
    .title{font-size:0.9rem;font-weight:700;color:#0f2067;margin-bottom:3px;}
    .desc{font-size:0.8rem;color:#6b7280;line-height:1.45;}
    </style></head><body>
    <h3>What you&rsquo;ll be able to do</h3>
    <div class="grid">
        <div class="card">
            <span class="icon">&#128202;</span>
            <div>
                <div class="title">Analyse Pricing Performance</div>
                <div class="desc">Drill into loss ratios, margins and yield across
                    pricing segments automatically.</div>
            </div>
        </div>
        <div class="card">
            <span class="icon">&#128269;</span>
            <div>
                <div class="title">Identify Profit Opportunities</div>
                <div class="desc">Surface underpriced or overpriced segments and
                    quantify the revenue impact.</div>
            </div>
        </div>
        <div class="card">
            <span class="icon">&#9881;&#65039;</span>
            <div>
                <div class="title">Run What-If Simulations</div>
                <div class="desc">Adjust price levers and see projected retention,
                    yield and loss ratio changes in real time.</div>
            </div>
        </div>
        <div class="card">
            <span class="icon">&#129503;</span>
            <div>
                <div class="title">AI-Driven Recommendations</div>
                <div class="desc">Get contextual suggestions from an LLM trained
                    on your book&rsquo;s pricing and risk data.</div>
            </div>
        </div>
    </div>
    </body></html>""",
    height=220,
    scrolling=False,
)

st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

# ── Section 2: Example prompts ────────────────────────────────────────────────
components.html(
    """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#f4f6fb;font-family:Inter,Arial,sans-serif;padding:0 0 8px;}
    h3{font-size:0.78rem;font-weight:700;text-transform:uppercase;
        letter-spacing:0.1em;color:#6b7280;margin-bottom:14px;}
    .chips{display:flex;flex-wrap:wrap;gap:10px;}
    .chip{background:#fff;border:1.5px solid #0f2067;border-radius:999px;
        padding:8px 18px;font-size:0.83rem;font-weight:600;color:#0f2067;
        cursor:default;display:flex;align-items:center;gap:7px;
        transition:background 0.15s,color 0.15s;}
    .chip:hover{background:#0f2067;color:#85db9c;}
    .chip .lbl{opacity:0.55;font-size:0.75rem;font-weight:400;
        margin-right:2px;}
    </style></head><body>
    <h3>Try asking questions like</h3>
    <div class="chips">
        <div class="chip"><span class="lbl">&#128161;</span>"How can I reduce loss ratio by 5%?"</div>
        <div class="chip"><span class="lbl">&#128161;</span>"What happens if I increase price by 3%?"</div>
        <div class="chip"><span class="lbl">&#128161;</span>"Which segments are underpriced?"</div>
        <div class="chip"><span class="lbl">&#128161;</span>"Show me the highest churn risk bundles."</div>
        <div class="chip"><span class="lbl">&#128161;</span>"What&rsquo;s driving the COR above threshold?"</div>
        <div class="chip"><span class="lbl">&#128161;</span>"Compare YoY price movement by pricing key."</div>
        <div class="chip"><span class="lbl">&#128161;</span>"Which pricing key has the best expected yield?"</div>
        <div class="chip"><span class="lbl">&#128161;</span>"Simulate a 2% price cut — what&rsquo;s the retention uplift?"</div>
    </div>
    </body></html>""",
    height=195,
    scrolling=False,
)

st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

# ── Tech stack teaser ─────────────────────────────────────────────────────────
components.html(
    """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#f4f6fb;font-family:Inter,Arial,sans-serif;padding:0 0 4px;}
    h3{font-size:0.78rem;font-weight:700;text-transform:uppercase;
        letter-spacing:0.1em;color:#6b7280;margin-bottom:14px;}
    .row{display:flex;gap:12px;flex-wrap:wrap;}
    .pill{background:#0f2067;color:#85db9c;border-radius:6px;
        padding:7px 16px;font-size:0.78rem;font-weight:700;
        letter-spacing:0.06em;text-transform:uppercase;}
    .pill.light{background:#e8f7ed;color:#1a7a4a;border:1px solid #85db9c;}
    </style></head><body>
    <h3>Powered by</h3>
    <div class="row">
        <div class="pill">Databricks LLM</div>
        <div class="pill">OpenAI</div>
        <div class="pill light">Claude</div>
        <div class="pill light">Gemini</div>
        <div class="pill light">LangChain</div>
    </div>
    </body></html>""",
    height=80,
    scrolling=False,
)

