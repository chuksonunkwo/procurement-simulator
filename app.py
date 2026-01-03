# ======================================================
# 🔒 PROCUREMENT SIMULATOR PRO: GOLDEN MASTER
# ======================================================
import os
import time
import subprocess

# --- 1. INSTALL DEPENDENCIES ---
print("🛠️ Installing Enterprise Libraries...")
subprocess.run(["pip", "install", "-q", "-U", "streamlit", "google-genai", "sqlalchemy", "fpdf", "requests", "pydantic"], check=True)

# --- 2. DOWNLOAD NETWORK TUNNEL ---
if not os.path.exists("cloudflared-linux-amd64"):
    print("☁️ Downloading Network Tunnel...")
    subprocess.run(["wget", "-q", "-O", "cloudflared-linux-amd64", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"], check=True)
    subprocess.run(["chmod", "+x", "cloudflared-linux-amd64"], check=True)

# --- 3. REQUIREMENTS ---
with open("requirements.txt", "w") as f:
    f.write("streamlit\ngoogle-genai\nsqlalchemy\nfpdf\nrequests\npydantic\n")

# --- 4. APP CODE ---
print("📝 Writing Application Code...")

app_code = r'''
import streamlit as st
import sqlite3
import os
import time
import requests
from fpdf import FPDF
from pydantic import BaseModel

# --- CONFIGURATION ---
st.set_page_config(page_title="Procurement Simulator Pro", layout="wide", page_icon="💼", initial_sidebar_state="expanded")

# --- 🔒 LICENSE GATEKEEPER ---
GUMROAD_PRODUCT_ID = "MFZpNGyCplKf9iTHq2f2xg==" 

def check_gumroad_license(license_key):
    try:
        r = requests.post("https://api.gumroad.com/v2/licenses/verify", 
                         data={
                             "product_id": GUMROAD_PRODUCT_ID, 
                             "license_key": license_key.strip()
                         })
        data = r.json()
        is_valid = data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
        return is_valid
    except Exception as e:
        return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- LOCK SCREEN UI ---
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .lock-box { 
            text-align: center; margin-top: 80px; padding: 50px; 
            border: 1px solid #e0e0e0; border-radius: 12px; background-color: #ffffff;
            max-width: 550px; margin-left: auto; margin-right: auto; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h1 { color: #154360; font-family: 'Helvetica', sans-serif; }
        </style>
        <div class="lock-box">
            <h1>🔒 Procurement Simulator Pro</h1>
            <p style="color: #666;">Enterprise Negotiation Training Environment</p>
            <hr style="margin: 20px 0;">
            <p style="font-size: 14px;">Please enter your license key to proceed.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        license_input = st.text_input("License Key", placeholder="", type="password")
        
        if st.button("Validate & Login", type="primary", use_container_width=True):
            with st.spinner("Verifying License..."):
                if check_gumroad_license(license_input):
                    st.session_state.authenticated = True
                    st.success("✅ License Verified.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid License Key. Access Denied.")
    st.stop()

# --- MAIN APP ---
if "messages" not in st.session_state: st.session_state.messages = []

try:
    from google import genai
    from google.genai import types
except ImportError: st.error("AI Library Error"); st.stop()

@st.cache_resource
def get_client():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try: key = st.secrets["GEMINI_API_KEY"]
        except: return None
    try: return genai.Client(api_key=key, http_options={'api_version': 'v1alpha'})
    except: return None

client = get_client()

# DATABASE
DB_FILE = 'procurement_sim_final.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY, title TEXT, category TEXT, difficulty TEXT, user_brief TEXT, system_persona TEXT)")
    c.execute("SELECT count(*) FROM scenarios")
    if c.fetchone()[0] == 0:
        # 22 SCENARIOS
        data = [
            ("EPC Steel Variation Claim", "Construction", "Hard", "**Role:** Project Director (Owner)\n**Context:** Your EPC contractor has submitted a $5M variation order citing global steel price hikes. The contract is Lump Sum Turnkey (LSTK).\n**Goal:** Firmly reject the price increase. Ensure schedule adherence.", "**Role:** Contractor PM.\n**Motivation:** Needs cash for liquidity."),
            ("Camp Construction Delay", "Construction", "Medium", "**Role:** Site Manager\n**Context:** Camp units are 2 months late. Contractor blames 'weather' (Force Majeure), but weather was mild.\n**Goal:** Reject Force Majeure. Demand acceleration at their cost.", "**Role:** Construction Lead.\n**Motivation:** Mismanaged project. Needs client to pay for overtime."),
            ("Deepwater Rig Rate", "Drilling", "Medium", "**Role:** Wells Category Lead\n**Context:** Market is soft. Current rig rate is 30% above market.\n**Goal:** Renegotiate rate down 20%. Offer 1-year extension as leverage.", "**Role:** Rig Contractor.\n**Motivation:** Terrified of stacking the rig. Needs the extension."),
            ("FPSO Termination Threat", "Production", "Expert", "**Role:** Asset Manager\n**Context:** FPSO uptime dropped to 85% (Target 95%).\n**Goal:** Issue notice for Remedial Plan or threaten Default.", "**Role:** FPSO Operator.\n**Motivation:** Parts stuck in customs. Terrified of losing contract."),
            ("SaaS Renewal Hike", "IT", "Medium", "**Role:** IT Procurement Mgr\n**Context:** Vendor proposes 15% hike. Cites 'inflation'.\n**Goal:** Cap increase at 3% (CPI). Remove Auto-Renewal.", "**Role:** Sales VP.\n**Motivation:** Needs quarterly revenue. Can trade price for 3-year term."),
            ("Software License Audit", "IT", "Hard", "**Role:** CIO\n**Context:** Audit claims $2M penalty for 'unlicensed usage'. Methodology is flawed.\n**Goal:** Settle <$200k. Disprove data.", "**Role:** Auditor.\n**Motivation:** Bonus tied to penalty size."),
            ("Data Breach Compensation", "IT", "Expert", "**Role:** Legal Counsel\n**Context:** Vendor data breach leaked employee info.\n**Goal:** Secure 1-yr free service + Identity Monitoring.", "**Role:** Cloud Provider.\n**Motivation:** Contract limits liability to 1 month fees."),
            ("Logistics Demurrage", "Logistics", "Easy", "**Role:** Logistics Supt\n**Context:** Vessel delayed 3 days. Owner claims $50k. Delay was vessel crane failure.\n**Goal:** Pay $0.", "**Role:** Shipowner.\n**Motivation:** Needs cash for fuel. Blaming 'port congestion'."),
            ("Helicopter Fuel Surcharge", "Logistics", "Medium", "**Role:** Category Lead\n**Context:** Provider wants fixed 10% hike for fuel.\n**Goal:** Reject fixed hike. Agree only to floating Fuel Index mechanism.", "**Role:** Heli Operator.\n**Motivation:** Margins are zero. Wants fixed profit."),
            ("Warehousing Exclusivity", "Logistics", "Easy", "**Role:** Supply Base Mgr\n**Context:** Warehouse owner demands 5-year exclusive deal.\n**Goal:** 2-year lease. Non-exclusive.", "**Role:** Warehouse Owner.\n**Motivation:** Needs long lease for bank loan."),
            ("Consultancy Rate Hike", "Corporate", "Medium", "**Role:** HR Director\n**Context:** Strategy firm wants +10% rate hike.\n**Goal:** Flat rates. Offer volume/scope expansion instead.", "**Role:** Partner.\n**Motivation:** High salary inflation. Needs utilization."),
            ("Office Lease Renewal", "Real Estate", "Hard", "**Role:** Facilities Mgr\n**Context:** Landlord wants +20% rent. Market is soft.\n**Goal:** Flat renewal. Threaten to move.", "**Role:** Landlord.\n**Motivation:** Bluffing about other tenant. Cannot afford vacancy."),
            ("Travel Agency Rebate", "Corporate", "Easy", "**Role:** Procurement Lead\n**Context:** Selecting new Global Agency. $10M spend.\n**Goal:** 3% rebate on volume.", "**Role:** Agency Rep.\n**Motivation:** Thin margins. 1% max."),
            ("FX & Inflation Indexing", "Commercial", "Medium", "**Role:** Category Manager\n**Context:** Supplier wants to switch currency to USD and index to US PPI.\n**Goal:** Keep local currency. Cap inflation index at 2%.", "**Role:** Manufacturer.\n**Motivation:** Raw materials in USD. Losing margin on FX."),
            ("MSA Liability Negotiation", "Contracting", "Hard", "**Role:** Contracts Lead\n**Context:** Vendor insists on mutual waiver of Consequential Damages.\n**Goal:** Retain right to claim lost profits for Gross Negligence.", "**Role:** Sales VP.\n**Motivation:** Legal says no. Can move on price/rates."),
            ("Pollution Liability Cap", "Legal", "Hard", "**Role:** General Counsel\n**Context:** Tug owner wants $5M cap. Risk is $50M.\n**Goal:** Unlimited Liability or $50M min.", "**Role:** Vessel Owner.\n**Motivation:** Insurance limit is $10M."),
            ("JV Partner Approval", "Governance", "Hard", "**Role:** Asset Mgr (Operator)\n**Context:** Need sole-source $2M repair. Partner wants tender.\n**Goal:** Get approval to bypass tender.", "**Role:** Partner (NOP).\n**Motivation:** Suspects gold-plating. Demands tender."),
            ("Force Majeure Claim", "Legal", "Expert", "**Role:** Contract Mgr\n**Context:** Supplier declares FM (Storm). Weather was mild.\n**Goal:** Reject FM. Enforce penalties.", "**Role:** Supplier.\n**Motivation:** Factory damaged by poor maintenance, not storm."),
            ("IP Ownership Dispute", "R&D", "Hard", "**Role:** R&D Lead\n**Context:** Co-developing sensor. Startup wants IP ownership.\n**Goal:** We own IP. They get license.", "**Role:** Startup CEO.\n**Motivation:** IP is only asset."),
            ("Local Content Quota", "ESG", "Medium", "**Role:** Content Mgr\n**Context:** Govt mandates 40% local spend. Contractor at 15%.\n**Goal:** Enforce 40% target plan.", "**Role:** Prime Contractor.\n**Motivation:** Locals are expensive/untrained."),
            ("HSE Incident Reporting", "HSE", "Medium", "**Role:** HSE Mgr\n**Context:** Supervisor hid 'Near Miss'.\n**Goal:** Reset safety bonus to 0%.", "**Role:** Supervisor.\n**Motivation:** Protecting crew bonus."),
            ("Green Energy Premium", "ESG", "Medium", "**Role:** Power Buyer\n**Context:** Buying renewable power. Generator wants 15% premium.\n**Goal:** <5% premium.", "**Role:** Solar Generator.\n**Motivation:** High demand.")
        ]
        c.executemany('INSERT INTO scenarios (title, category, difficulty, user_brief, system_persona) VALUES (?,?,?,?,?)', data)
        conn.commit()
init_db()

def get_scenarios():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.cursor().execute("SELECT id, title, category, difficulty FROM scenarios ORDER BY category, title").fetchall()
    # ADD CUSTOM OPTION TO TOP OF LIST
    rows.insert(0, (999, "🛠️ Create Custom Scenario", "Custom", "Manual"))
    return rows

def get_details(sid):
    conn = sqlite3.connect(DB_FILE)
    return conn.cursor().execute("SELECT user_brief, system_persona FROM scenarios WHERE id=?", (sid,)).fetchone()

# PDF
def create_pdf(title, brief, score_data, feedback, transcript):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15); self.cell(0, 10, 'Negotiation AAR Report', 0, 1, 'C')
            self.set_font('Arial', 'I', 10); self.cell(0, 10, f'Scenario: {title}', 0, 1, 'C'); self.ln(5)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def clean(t): return t.encode('latin-1', 'ignore').decode('latin-1')
    pdf = PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '1. Scorecard', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(60, 10, f"Total: {score_data['total']}/100", 1)
    pdf.cell(60, 10, f"Commercial: {score_data['comm']}/40", 1)
    pdf.cell(60, 10, f"Strategic: {score_data['strat']}/40", 1, 1); pdf.ln(5)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '2. Feedback', 0, 1)
    pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 6, clean(feedback)); pdf.ln(5)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '3. Transcript', 0, 1)
    pdf.set_font('Courier', '', 9)
    for m in transcript: pdf.multi_cell(0, 5, f"{m['role'].upper()}: {clean(m['content'])}"); pdf.ln(1)
    return pdf.output(dest='S').encode('latin-1')

# UI
with st.sidebar:
    st.markdown("""
        <style>
        .big-font { font-size: 26px !important; font-weight: 800; color: #154360; margin-bottom: 5px; }
        .version-font { font-size: 12px; color: #888; margin-bottom: 15px; }
        .stButton button { width: 100%; border-radius: 5px; }
        </style>
        <div class="big-font">Procurement Simulator Pro</div>
        <div class="version-font">Version 1.0 | Enterprise Edition</div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # SCENARIO SELECTION LOGIC
    scenarios = get_scenarios()
    options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
    selected_label = st.selectbox("Select Mission", list(options.keys()))
    selected_id = options[selected_label]
    
    brief_text = ""
    persona_text = ""
    
    # CUSTOM SCENARIO MODE
    if selected_id == 999:
        st.info("🛠️ Define Your Own Scenario")
        with st.form("custom_form"):
            c_role = st.text_input("My Role", "Freelance Consultant")
            c_context = st.text_area("Situation", "Client wants to expand scope by 50% without increasing budget.")
            c_goal = st.text_input("My Goal", "Get $5k extra or cut scope.")
            c_opp_role = st.text_input("Counterparty Role", "Project Manager")
            c_opp_motiv = st.text_input("Counterparty Motivation", "Over budget already. Under pressure from VP.")
            submitted = st.form_submit_button("Launch Simulation")
            
            if submitted:
                st.session_state['custom_brief'] = f"**Role:** {c_role}\n**Context:** {c_context}\n**Goal:** {c_goal}"
                st.session_state['custom_persona'] = f"**Role:** {c_opp_role}\n**Motivation:** {c_opp_motiv}"
                st.session_state.messages = []
                st.rerun()
        
        brief_text = st.session_state.get('custom_brief', "Fill out the form above to start.")
        persona_text = st.session_state.get('custom_persona', "Waiting for input...")
    else:
        brief_text, persona_text = get_details(selected_id)

    with st.expander("📋 Mission Briefing", expanded=True): st.markdown(brief_text)
    
    st.markdown("---"); st.subheader("🛠️ Tactical Support")
    if st.button("💡 Strategic Whisper"):
        if not st.session_state.messages: st.warning("Start negotiating first.")
        elif not client: st.error("AI Offline.")
        else:
            with st.spinner("Analyzing..."):
                t = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=f"Context: {brief_text}\nTranscript: {t}\nTask: Give ONE short tactical move.")
                    st.info(f"**Coach:** {r.text}")
                except: st.error("Coach unavailable.")
    if st.button("🔄 Reset Session", type="primary"): 
        st.session_state.messages = []
        st.rerun()
    st.markdown("---"); st.caption("**Disclaimer:** Training simulation. Fictional scenarios. Not professional advice.")

# CHAT
st.markdown(f"### {selected_label.split('|')[1].strip()}") 
if not client: st.error("⚠️ AI Key Missing. Please set GEMINI_API_KEY env var."); st.stop()

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "👔"
    with st.chat_message(msg["role"], avatar=avatar): st.markdown(msg["content"])

if user_input := st.chat_input("Enter your position..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.markdown(user_input)
    
    # DYNAMIC PROMPT (Works for both Custom and Preset)
    sys_prompt = f"Sim: {selected_label}\n{persona_text}\nAct as professional counterparty. Concise. Tough."
    
    gemini_hist = [types.Content(role="user" if m["role"]=="user" else "model", parts=[types.Part(text=m["content"])]) for m in st.session_state.messages]
    with st.chat_message("assistant", avatar="👔"):
        with st.spinner("Counterparty responding..."):
            try:
                resp = client.models.generate_content(model='gemini-2.0-flash', contents=gemini_hist, config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.6))
                st.markdown(resp.text); st.session_state.messages.append({"role": "assistant", "content": resp.text})
            except: st.error("Connection Error.")

class Scorecard(BaseModel): total_score: int; commercial: int; strategy: int; feedback: str
st.markdown("---")
with st.expander("📊 End Session & Generate Report", expanded=False):
    if st.button("Analyze Performance"):
        if len(st.session_state.messages) < 2: st.warning("Insufficient data.")
        else:
            with st.spinner("Generating Assessment..."):
                t = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                score_prompt = f"""
                Context: {brief_text}
                Transcript: {t}
                Task: Grade performance. Returns JSON.
                Rules: 
                - total_score (0-100)
                - commercial (0-40) [MAX IS 40]
                - strategy (0-40) [MAX IS 40]
                """
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=score_prompt, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard, temperature=0.1)).parsed
                    safe_total = min(max(r.total_score, 0), 100)
                    safe_comm = min(max(r.commercial, 0), 40)
                    safe_strat = min(max(r.strategy, 0), 40)
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1: st.metric("Total Score", f"{safe_total}/100"); st.progress(safe_total/100)
                    with c2: st.metric("Commercial", f"{safe_comm}/40"); st.metric("Strategy", f"{safe_strat}/40")
                    with c3: st.info(f"**Feedback:** {r.feedback}")
                    pdf_data = create_pdf(selected_label, brief_text, {"total": safe_total, "comm": safe_comm, "strat": safe_strat}, r.feedback, st.session_state.messages)
                    st.download_button("📄 Download Professional AAR (PDF)", pdf_data, "AAR_Report.pdf", "application/pdf")
                except Exception as e: st.error(f"Error: {e}")
'''

with open("app.py", "w") as f:
    f.write(app_code)

# --- 5. LAUNCHER ---
print("🚀 Launching Procurement Simulator Pro...")
subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"])
time.sleep(3)
with open("cloudflare.log", "w") as f:
    subprocess.Popen(["./cloudflared-linux-amd64", "tunnel", "--url", "http://localhost:8501"], stdout=f, stderr=f)

time.sleep(5)
found_url = False
for i in range(10):
    try:
        with open("cloudflare.log", "r") as f:
            content = f.read()
            import re
            url_match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
            if url_match:
                print(f"\n✅ YOUR APP URL: {url_match.group(0)}\n")
                print(f"🔒 PROTECTED: Requires valid License Key for Product ID 'MFZpNGyCplKf9iTHq2f2xg=='")
                found_url = True
                break
    except: pass
    time.sleep(2)
if not found_url: print("❌ Error finding URL. Please re-run this cell.")
