import streamlit as st
import sqlite3
import os
import time
from fpdf import FPDF
from pydantic import BaseModel

# --- 1. AUTHENTICATION SETUP (Cloud Compatible) ---
# Try to import the Google GenAI library
try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("⚠️ Library Error: `google-genai` not found. Please add it to requirements.txt")
    st.stop()

# --- 2. APP CONFIGURATION ---
st.set_page_config(
    page_title="Procurement Pro",
    layout="wide",
    page_icon="💼",
    initial_sidebar_state="expanded"
)

# --- 3. GLOBAL STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(time.time())

# --- 4. CONNECT TO AI (API Key Support) ---
@st.cache_resource
def get_client():
    # 1. Try getting key from Streamlit Secrets (Best for Cloud)
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        try:
            # Fallback for local testing (Secrets file)
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            return None

    try:
        # Initialize Client with API Key
        return genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

client = get_client()

# --- 5. DATA LAYER (20 SCENARIOS) ---
DB_FILE = 'procurement_ultimate.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS scenarios")
    c.execute('''CREATE TABLE scenarios (
        id INTEGER PRIMARY KEY, 
        title TEXT, 
        category TEXT, 
        difficulty TEXT, 
        user_brief TEXT, 
        system_persona TEXT
    )''')
    
    # THE MASTER LIST OF 20 SCENARIOS
    data = [
        # --- CONSTRUCTION & CAPEX ---
        ("EPC Steel Variation Claim", "Construction", "Hard", "**Role:** Project Director.\n**Situation:** Contractor claims $5M for steel price hikes on LSTK contract.\n**Goal:** Reject price increase. Protect schedule.", "**Role:** Contractor PM.\n**Motivation:** Facing liquidity issues. Need cash or will slow down."),
        ("Deepwater Rig Rate", "Drilling", "Medium", "**Role:** Wells Lead.\n**Situation:** Oil price drop. Rig rates down 30%.\n**Goal:** Renegotiate rate down 20%. Offer 1-yr extension.", "**Role:** Rig Contractor.\n**Motivation:** Terrified of stacking the rig. Act tough but need the deal."),
        ("FPSO Termination Threat", "Production", "Expert", "**Role:** Asset Mgr.\n**Situation:** FPSO uptime 85% (Target 95%).\n**Goal:** Get remedial plan or threaten Default Notice.", "**Role:** FPSO Operator.\n**Motivation:** Parts stuck in customs. Terrified of losing contract."),
        ("Camp Construction Delay", "Construction", "Medium", "**Role:** Site Mgr.\n**Situation:** Camp delivery delayed 2 months.\n**Goal:** Demand acceleration at contractor cost.", "**Role:** Construction Lead.\n**Motivation:** Weather caused delays (Force Majeure?). You won't pay for acceleration."),
        
        # --- IT & SOFTWARE ---
        ("SaaS Renewal Hike", "IT", "Medium", "**Role:** IT Buyer.\n**Situation:** Vendor demands 15% hike.\n**Goal:** Cap at 3% (CPI). Remove auto-renewal.", "**Role:** Sales VP.\n**Motivation:** Need to hit quarterly target. Can trade price for 3-year term."),
        ("Software License Audit", "IT", "Hard", "**Role:** CIO.\n**Situation:** Vendor claims $2M in unlicensed usage.\n**Goal:** Settle for <$200k. Prove usage data is wrong.", "**Role:** Compliance Auditor.\n**Motivation:** Your bonus depends on the penalty size. You have 'proof'."),
        ("Data Breach Compensation", "IT/Legal", "Expert", "**Role:** Legal Counsel.\n**Situation:** Cloud provider leaked employee data.\n**Goal:** Secure 1-year free service + Credit Monitoring.", "**Role:** Cloud Provider.\n**Motivation:** Deny negligence. Limit liability to 1 month fees (standard clause)."),
        
        # --- LOGISTICS & OPERATIONS ---
        ("Logistics Demurrage", "Logistics", "Easy", "**Role:** Logistics Supt.\n**Situation:** Vessel delayed 3 days. Owner claims $50k.\n**Goal:** Pay $0. Delay was crane breakdown.", "**Role:** Shipowner.\n**Motivation:** Blame 'Port Congestion'. Need cash for fuel."),
        ("Helicopter Fuel Surcharge", "Logistics", "Medium", "**Role:** Category Lead.\n**Situation:** Provider wants 10% fuel surcharge.\n**Goal:** Agree to floating mechanism, not fixed hike.", "**Role:** Heli Operator.\n**Motivation:** Fuel prices spiked. Margins are zero without this."),
        ("Warehousing Exclusivity", "Logistics", "Easy", "**Role:** Supply Base Mgr.\n**Situation:** Warehouse owner wants 5-year exclusive deal.\n**Goal:** Agree to 2 years, no exclusivity.", "**Role:** Warehouse Owner.\n**Motivation:** Need long lease to secure bank loan."),
        
        # --- CORPORATE & STRATEGY ---
        ("Consultancy Rate Hike", "Corporate", "Medium", "**Role:** HR Director.\n**Situation:** Strategy firm wants +10% rate increase.\n**Goal:** Hold rates flat. Offer more volume/projects.", "**Role:** Partner.\n**Motivation:** Salary inflation is high. Cannot keep staff without rate hike."),
        ("Office Lease Renewal", "Real Estate", "Hard", "**Role:** Facilities Mgr.\n**Situation:** Landlord wants 20% rent hike.\n**Goal:** Flat renewal or we move to suburbs.", "**Role:** Landlord.\n**Motivation:** Market is hot. Have another tenant lined up (bluff?)."),
        ("Travel Agency Rebate", "Corporate", "Easy", "**Role:** Procurement Lead.\n**Situation:** selecting new Travel Agency.\n**Goal:** Secure 3% rebate on all volume.", "**Role:** Agency Rep.\n**Motivation:** Margins are thin. Can offer 1% max."),
        
        # --- LEGAL & GOVERNANCE ---
        ("Pollution Liability Cap", "Legal", "Hard", "**Role:** Legal Counsel.\n**Situation:** Vessel owner wants $5M liability cap.\n**Goal:** Unlimited Liability or $50M min.", "**Role:** Owner.\n**Motivation:** Insurance only covers $10M. Cannot sign for more."),
        ("JV Partner Approval", "Governance", "Hard", "**Role:** Asset Mgr (Operator).\n**Situation:** Sole-source $2M repair.\n**Goal:** Get Partner approval. Skip tender.", "**Role:** Partner (NOP).\n**Motivation:** Suspect gold-plating. Demand full tender."),
        ("Force Majeure Claim", "Legal", "Expert", "**Role:** Contract Mgr.\n**Situation:** Supplier declares FM due to 'Storm'.\n**Goal:** Reject FM. Storm was predictable.", "**Role:** Supplier.\n**Motivation:** Factory damaged. Cannot deliver. Need relief."),
        ("IP Ownership Dispute", "R&D", "Hard", "**Role:** R&D Lead.\n**Situation:** Joint development with startup.\n**Goal:** We own the IP. They get license.", "**Role:** Startup CEO.\n**Motivation:** IP is our only asset. We must own it."),
        
        # --- ESG & HSE ---
        ("Local Content Quota", "ESG", "Medium", "**Role:** Local Content Mgr.\n**Situation:** Govt mandates 40% local spend.\n**Goal:** Enforce target without delay.", "**Role:** Tier 1 Supplier.\n**Motivation:** Locals are untrained. Will cause 6-month delay."),
        ("HSE Incident Reporting", "HSE", "Medium", "**Role:** HSE Mgr.\n**Situation:** Contractor hid Near Miss.\n**Goal:** Reset safety bonus to 0%.", "**Role:** Site Supervisor.\n**Motivation:** Crew loses bonus. Tried to protect them."),
        ("Green Energy Premium", "ESG", "Medium", "**Role:** Power Buyer.\n**Situation:** Buying renewable power.\n**Goal:** Pay <5% premium over grid price.", "**Role:** Solar Generator.\n**Motivation:** Demand is high. Can sell to others for +10%.")
    ]
    
    c.executemany('INSERT INTO scenarios (title, category, difficulty, user_brief, system_persona) VALUES (?,?,?,?,?)', data)
    conn.commit()

if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

def get_scenarios():
    conn = sqlite3.connect(DB_FILE)
    return conn.cursor().execute("SELECT id, title, category, difficulty FROM scenarios").fetchall()

def get_details(sid):
    conn = sqlite3.connect(DB_FILE)
    return conn.cursor().execute("SELECT user_brief, system_persona FROM scenarios WHERE id=?", (sid,)).fetchone()

# --- 6. PDF ENGINE ---
def create_pdf(title, brief, score_data, feedback, transcript):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Negotiation Performance Report', 0, 1, 'C')
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, f'Scenario: {title}', 0, 1, 'C')
            self.ln(5)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def clean(t): return t.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf = PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15)
    
    # Dashboard
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '1. Executive Scorecard', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(60, 10, f"Total Rating: {score_data['total']}/100", 1)
    pdf.cell(60, 10, f"Commercial: {score_data['comm']}/40", 1)
    pdf.cell(60, 10, f"Strategic: {score_data['strat']}/40", 1, 1)
    pdf.ln(5)
    
    # Feedback
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '2. AI Coach Assessment', 0, 1)
    pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 6, clean(feedback)); pdf.ln(5)
    
    # Transcript
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '3. Official Transcript', 0, 1)
    pdf.set_font('Courier', '', 9)
    for m in transcript:
        pdf.multi_cell(0, 5, f"{m['role'].upper()}: {clean(m['content'])}"); pdf.ln(1)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 7. PROFESSIONAL UI ---
with st.sidebar:
    # 🎨 CUSTOM BRANDING
    st.markdown("""
        <style>
        .big-font { font-size: 26px !important; font-weight: 800; color: #154360; margin-bottom: 10px; }
        .stButton button { width: 100%; border-radius: 5px; }
        </style>
        <div class="big-font">Procurement Pro</div>
        """, unsafe_allow_html=True)
    
    st.caption("Advanced Negotiation Simulator v3.0")
    st.markdown("---")
    
    # SCENARIO SELECTOR
    scenarios = get_scenarios()
    options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
    selected_label = st.selectbox("Select Mission", list(options.keys()))
    selected_id = options[selected_label]
    brief, persona = get_details(selected_id)
    
    with st.expander("📋 Mission Briefing", expanded=True):
        st.markdown(brief)
    
    st.markdown("---")
    st.subheader("🛠️ Tactical Support")
    
    # AI WHISPER BUTTON
    if st.button("💡 Strategic Whisper"):
        if not st.session_state.messages:
            st.warning("Initiate negotiation first.")
        elif not client:
            st.error("AI Offline. Check API Key.")
        else:
            with st.spinner("Analyzing leverage points..."):
                t = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                p = f"Context: {brief}\nTranscript: {t}\nTask: Give ONE short, high-leverage tactical move."
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=p)
                    st.info(f"**Coach:** {r.text}")
                except: st.error("Coach unavailable.")
    
    if st.button("🔄 Reset Session", type="primary"):
        st.session_state.messages = []
        st.rerun()

# MAIN AREA
st.markdown(f"### {selected_label.split('|')[1].strip()}") 

# CHAT INTERFACE
if not client: 
    st.error("⚠️ AI Service Offline. Please add `GEMINI_API_KEY` to your Environment Variables.")
    st.info("You can get a free key at **aistudio.google.com**")
    st.stop()

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "👔"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# LOGIC ENGINE
if user_input := st.chat_input("Enter your position..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.markdown(user_input)

    sys_prompt = f"Sim: {selected_label}\nRole: {persona}\nAct as professional counterparty. Concise. Tough."
    gemini_hist = [types.Content(role="user" if m["role"]=="user" else "model", parts=[types.Part(text=m["content"])]) for m in st.session_state.messages]
    
    with st.chat_message("assistant", avatar="👔"):
        with st.spinner("Counterparty responding..."):
            try:
                resp = client.models.generate_content(model='gemini-2.0-flash', contents=gemini_hist, config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.6))
                st.markdown(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            except: st.error("Connection Error.")

# ANALYTICS & PDF
class Scorecard(BaseModel):
    total_score: int; commercial: int; strategy: int; feedback: str

st.markdown("---")
with st.expander("📊 End Session & Generate Report", expanded=False):
    if st.button("Analyze Performance"):
        if len(st.session_state.messages) < 2: st.warning("Insufficient data.")
        else:
            with st.spinner("Generating Assessment..."):
                t = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                p = f"Context: {brief}\nTranscript: {t}\nTask: Grade (0-100). Comm(0-40), Strat(0-40). JSON."
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=p, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard, temperature=0.1)).parsed
                    
                    safe_total = min(max(r.total_score, 0), 100)
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1: st.metric("Total Score", f"{safe_total}/100"); st.progress(safe_total/100)
                    with c2: st.metric("Commercial", f"{r.commercial}/40"); st.metric("Strategy", f"{r.strategy}/40")
                    with c3: st.info(f"**Feedback:** {r.feedback}")
                    
                    pdf_data = create_pdf(selected_label, brief, {"total": safe_total, "comm": r.commercial, "strat": r.strategy}, r.feedback, st.session_state.messages)
                    st.download_button("📄 Download Professional AAR (PDF)", pdf_data, "AAR_Report.pdf", "application/pdf")
                except Exception as e: st.error(f"Error: {e}")
