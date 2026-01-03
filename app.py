# ======================================================
# 🔒 PROCUREMENT SIMULATOR PRO: COMMERCIAL RELEASE
#    Product ID: MFZpNGyCplKf9iTHq2f2xg==
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

# --- 3. REQUIREMENTS (For Cloud Deployment) ---
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
# ✅ UPDATED: Your specific Gumroad Product ID
GUMROAD_PERMALINK = "MFZpNGyCplKf9iTHq2f2xg==" 

def check_gumroad_license(license_key):
    try:
        # Calls Gumroad API to verify the key belongs to your product
        r = requests.post("https://api.gumroad.com/v2/licenses/verify", 
                         data={"product_permalink": GUMROAD_PERMALINK, "license_key": license_key.strip()})
        data = r.json()
        
        # 1. Check if success is True
        # 2. Check if purchase is NOT refunded/cancelled
        is_valid = data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
        return is_valid
    except: 
        return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- LOCK SCREEN UI ---
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .lock-box { 
            text-align: center; 
            margin-top: 80px; 
            padding: 50px; 
            border: 1px solid #e0e0e0; 
            border-radius: 12px; 
            background-color: #ffffff;
            max-width: 550px; 
            margin-left: auto; 
            margin-right: auto; 
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
        license_input = st.text_input("License Key", placeholder="KW...-....", type="password")
        
        if st.button("Validate & Login", type="primary", use_container_width=True):
            with st.spinner("Verifying License with Gumroad..."):
                if check_gumroad_license(license_input):
                    st.session_state.authenticated = True
                    st.success("✅ License Verified.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid License Key. Access Denied.")
    st.stop()

# ==========================================
#  💼 MAIN APPLICATION (Protected Area)
# ==========================================

if "messages" not in st.session_state: st.session_state.messages = []

# AI SETUP
try:
    from google import genai
    from google.genai import types
except ImportError: st.error("System Error: AI Library missing."); st.stop()

@st.cache_resource
def get_client():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try: key = st.secrets["GEMINI_API_KEY"]
        except: return None
    try: return genai.Client(api_key=key, http_options={'api_version': 'v1alpha'})
    except: return None

client = get_client()

# DATABASE SETUP
DB_FILE = 'procurement_sim_final.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY, title TEXT, category TEXT, difficulty TEXT, user_brief TEXT, system_persona TEXT)")
    
    # Fast load: Only insert if empty
    c.execute("SELECT count(*) FROM scenarios")
    if c.fetchone()[0] == 0:
        data = [
            ("EPC Steel Variation Claim", "Construction", "Hard", "**Role:** Project Director.\n**Situation:** Contractor claims $5M for steel price hikes.\n**Goal:** Reject hike.", "**Role:** Contractor PM.\n**Motivation:** Needs cash for liquidity."),
            ("Camp Construction Delay", "Construction", "Medium", "**Role:** Site Mgr.\n**Situation:** Delivery delayed 2 months.\n**Goal:** Demand acceleration.", "**Role:** Construction Lead.\n**Motivation:** Weather delay (FM). Won't pay acceleration."),
            ("Deepwater Rig Rate", "Drilling", "Medium", "**Role:** Wells Lead.\n**Situation:** Oil down. Rates down 30%.\n**Goal:** -20% rate. 1yr extension.", "**Role:** Rig Contractor.\n**Motivation:** Terrified of stacking rig."),
            ("FPSO Termination Threat", "Production", "Expert", "**Role:** Asset Mgr.\n**Situation:** 85% uptime.\n**Goal:** Remedial plan or Default Notice.", "**Role:** FPSO Operator.\n**Motivation:** Parts stuck in customs."),
            ("SaaS Renewal Hike", "IT", "Medium", "**Role:** IT Buyer.\n**Situation:** +15% hike.\n**Goal:** Cap at 3%. No auto-renewal.", "**Role:** Sales VP.\n**Motivation:** Needs quarterly target."),
            ("Software License Audit", "IT", "Hard", "**Role:** CIO.\n**Situation:** $2M penalty claim.\n**Goal:** Settle <$200k.", "**Role:** Auditor.\n**Motivation:** Bonus tied to penalty size."),
            ("Data Breach Compensation", "IT", "Expert", "**Role:** Legal.\n**Situation:** Data leak.\n**Goal:** 1yr free service + monitoring.", "**Role:** Cloud Provider.\n**Motivation:** Limit liability to 1 month fees."),
            ("Logistics Demurrage", "Logistics", "Easy", "**Role:** Logistics Supt.\n**Situation:** 3 day delay. $50k claim.\n**Goal:** Pay $0.", "**Role:** Shipowner.\n**Motivation:** Needs cash for fuel."),
            ("Helicopter Fuel Surcharge", "Logistics", "Medium", "**Role:** Category Lead.\n**Situation:** +10% fuel surcharge.\n**Goal:** Floating mechanism only.", "**Role:** Heli Operator.\n**Motivation:** Zero margin without hike."),
            ("Warehousing Exclusivity", "Logistics", "Easy", "**Role:** Supply Mgr.\n**Situation:** Owner wants 5yr exclusive.\n**Goal:** 2yr non-exclusive.", "**Role:** Owner.\n**Motivation:** Needs lease for bank loan."),
            ("Consultancy Rate Hike", "Corporate", "Medium", "**Role:** HR Director.\n**Situation:** +10% rate ask.\n**Goal:** Flat rates.", "**Role:** Partner.\n**Motivation:** Salary inflation high."),
            ("Office Lease Renewal", "Real Estate", "Hard", "**Role:** Facilities Mgr.\n**Situation:** +20% rent ask.\n**Goal:** Flat or move.", "**Role:** Landlord.\n**Motivation:** Bluffing about other tenant."),
            ("Travel Agency Rebate", "Corporate", "Easy", "**Role:** Procurement Lead.\n**Situation:** New Agency.\n**Goal:** 3% rebate.", "**Role:** Agency Rep.\n**Motivation:** Thin margins. 1% max."),
            ("Pollution Liability Cap", "Legal", "Hard", "**Role:** Counsel.\n**Situation:** Wants $5M cap.\n**Goal:** Unlimited or $50M.", "**Role:** Owner.\n**Motivation:** Insurance limit is $10M."),
            ("JV Partner Approval", "Governance", "Hard", "**Role:** Asset Mgr.\n**Situation:** Sole-source $2M.\n**Goal:** Partner approval.", "**Role:** Partner.\n**Motivation:** Suspects gold-plating."),
            ("Force Majeure Claim", "Legal", "Expert", "**Role:** Contract Mgr.\n**Situation:** Supplier declares FM (Storm).\n**Goal:** Reject FM.", "**Role:** Supplier.\n**Motivation:** Factory damaged."),
            ("IP Ownership Dispute", "R&D", "Hard", "**Role:** R&D Lead.\n**Situation:** Joint dev.\n**Goal:** We own IP.", "**Role:** Startup CEO.\n**Motivation:** IP is only asset."),
            ("Local Content Quota", "ESG", "Medium", "**Role:** Content Mgr.\n**Situation:** 40% mandate.\n**Goal:** Enforce target.", "**Role:** Supplier.\n**Motivation:** Locals untrained."),
            ("HSE Incident Reporting", "HSE", "Medium", "**Role:** HSE Mgr.\n**Situation:** Hidden Near Miss.\n**Goal:** Reset bonus.", "**Role:** Supervisor.\n**Motivation:** Protecting crew bonus."),
            ("Green Energy Premium", "ESG", "Medium", "**Role:** Power Buyer.\n**Situation:** Buying renewable.\n**Goal:** <5% premium.", "**Role:** Generator.\n**Motivation:** High demand.")
        ]
        c.executemany('INSERT INTO scenarios (title, category, difficulty, user_brief, system_persona) VALUES (?,?,?,?,?)', data)
        conn.commit()

init_db()

def get_scenarios():
    conn = sqlite3.connect(DB_FILE)
    return conn.cursor().execute("SELECT id, title, category, difficulty FROM scenarios ORDER BY category, title").fetchall()
def get_details(sid):
    conn = sqlite3.connect(DB_FILE)
    return conn.cursor().execute("SELECT user_brief, system_persona FROM scenarios WHERE id=?", (sid,)).fetchone()

# PDF GENERATOR
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

# UI SIDEBAR
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
    
    scenarios = get_scenarios()
    options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
    selected_label = st.selectbox("Select Mission", list(options.keys()))
    selected_id = options[selected_label]
    brief, persona = get_details(selected_id)
    with st.expander("📋 Mission Briefing", expanded=True): st.markdown(brief)
    
    st.markdown("---"); st.subheader("🛠️ Tactical Support")
    if st.button("💡 Strategic Whisper"):
        if not st.session_state.messages: st.warning("Start negotiating first.")
        elif not client: st.error("AI Offline.")
        else:
            with st.spinner("Analyzing..."):
                t = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=f"Context: {brief}\nTranscript: {t}\nTask: Give ONE short tactical move.")
                    st.info(f"**Coach:** {r.text}")
                except: st.error("Coach unavailable.")
    if st.button("🔄 Reset Session", type="primary"): st.session_state.messages = []; st.rerun()
    st.markdown("---"); st.caption("**Disclaimer:** Training simulation. Fictional scenarios. Not professional advice.")

# MAIN CHAT
st.markdown(f"### {selected_label.split('|')[1].strip()}") 
if not client: st.error("⚠️ AI Key Missing. Please set GEMINI_API_KEY env var."); st.stop()

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "👔"
    with st.chat_message(msg["role"], avatar=avatar): st.markdown(msg["content"])

if user_input := st.chat_input("Enter your position..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.markdown(user_input)
    sys_prompt = f"Sim: {selected_label}\nRole: {persona}\nAct as professional counterparty. Concise. Tough."
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
                try:
                    r = client.models.generate_content(model='gemini-2.0-flash', contents=f"Context: {brief}\nTranscript: {t}\nTask: Grade (0-100). JSON.", config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard, temperature=0.1)).parsed
                    safe_total = min(max(r.total_score, 0), 100)
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1: st.metric("Total Score", f"{safe_total}/100"); st.progress(safe_total/100)
                    with c2: st.metric("Commercial", f"{r.commercial}/40"); st.metric("Strategy", f"{r.strategy}/40")
                    with c3: st.info(f"**Feedback:** {r.feedback}")
                    pdf_data = create_pdf(selected_label, brief, {"total": safe_total, "comm": r.commercial, "strat": r.strategy}, r.feedback, st.session_state.messages)
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
                print("🔒 LOCKED: Requires valid license for Product ID 'MFZpNGyCplKf9iTHq2f2xg=='")
                found_url = True
                break
    except: pass
    time.sleep(2)
if not found_url: print("❌ Error finding URL. Please re-run this cell.")
