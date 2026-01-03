# ======================================================
# 🔒 PROCUREMENT SIMULATOR PRO: FINAL MASTER BUILD
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
        # DATA WITH ENHANCED CONTEXT
        data = [
            ("EPC Steel Variation Claim", "Construction", "Hard", 
             "**Role:** Project Director (Owner)\n**Context:** Your EPC contractor has submitted a $5M variation order citing global steel price hikes. The contract is Lump Sum Turnkey (LSTK), meaning they explicitly assumed this risk.\n**Goal:** Firmly reject the price increase while ensuring they do not slow down the project schedule due to cash flow issues.", 
             "**Role:** Contractor PM.\n**Motivation:** Your HQ is squeezing you. You are facing liquidity issues. You need this cash or you will be forced to slow down works."),
            
            ("Camp Construction Delay", "Construction", "Medium", 
             "**Role:** Site Manager\n**Context:** The modular camp units are 2 months late. The contractor is blaming 'unforeseeable weather' (Force Majeure), but your logs show the weather was mild.\n**Goal:** Reject the Force Majeure claim. Demand a recovery plan and acceleration at their own cost to hit the start date.", 
             "**Role:** Construction Lead.\n**Motivation:** It was mismanagement, but you can't admit that. You want the client to pay for the overtime needed to catch up."),
            
            ("Deepwater Rig Rate", "Drilling", "Medium", 
             "**Role:** Wells Category Lead\n**Context:** Oil prices have dropped, and the rig market is soft. Your current rig rate is 30% above the new market average.\n**Goal:** Renegotiate the current contract rate down by 20%. You can offer a 1-year contract extension as leverage.", 
             "**Role:** Rig Contractor.\n**Motivation:** You are terrified of having to 'stack' (idle) the rig, which costs millions. You will act tough, but you need this extension."),
            
            ("FPSO Termination Threat", "Production", "Expert", 
             "**Role:** Asset Manager\n**Context:** The FPSO uptime has dropped to 85% (Contract Target: 95%). This is costing you daily production revenue. They are making excuses about spare parts.\n**Goal:** Issue a formal notice requiring a Remedial Plan within 7 days, or threaten to issue a Default Notice.", 
             "**Role:** FPSO Operator.\n**Motivation:** The spare parts are stuck in customs due to your administrative error. You are terrified of losing this contract."),
            
            ("SaaS Renewal Hike", "IT", "Medium", 
             "**Role:** IT Procurement Manager\n**Context:** Your critical software vendor has proposed a 15% price increase for the renewal, citing 'inflation' and 'new features' you don't use.\n**Goal:** Cap the increase at 3% (CPI). Remove the 'Auto-Renewal' clause from the new agreement.", 
             "**Role:** Software Sales VP.\n**Motivation:** You have a quarterly revenue target to hit. You can trade price discount if they sign a longer term (3 years)."),
            
            ("Software License Audit", "IT", "Hard", 
             "**Role:** CIO\n**Context:** A vendor audit claims you are non-compliant and owe $2M in penalties. You believe their data methodology is flawed and counts inactive users.\n**Goal:** Settle for less than $200k. Prove their usage data is incorrect.", 
             "**Role:** Compliance Auditor.\n**Motivation:** Your personal bonus is directly tied to the size of the penalty you collect. You have 'proof' (though it might be shaky)."),
            
            ("Data Breach Compensation", "IT", "Expert", 
             "**Role:** Legal Counsel\n**Context:** Your cloud provider had a breach that leaked some of your employee data. They are offering a generic apology.\n**Goal:** Secure 1-year of free service credits and paid Identity Theft Monitoring for all affected employees.", 
             "**Role:** Cloud Provider.\n**Motivation:** Your contract limits liability to 1 month of fees. You want to stick to the contract strict terms."),
            
            ("Logistics Demurrage", "Logistics", "Easy", 
             "**Role:** Logistics Superintendent\n**Context:** A vessel was delayed 3 days at port. The shipowner is claiming $50k in demurrage fees. The delay was actually caused by the vessel's own crane breaking down.\n**Goal:** Pay $0. Establish that the delay was due to vessel equipment failure, not the port.", 
             "**Role:** Shipowner.\n**Motivation:** You know the crane was shaky, but you will blame 'Port Congestion' to try and get paid. You need cash for fuel."),
            
            ("Helicopter Fuel Surcharge", "Logistics", "Medium", 
             "**Role:** Category Lead\n**Context:** Your aviation provider wants a fixed 10% rate hike to cover rising fuel costs. You want to avoid locking in a high rate if fuel drops later.\n**Goal:** Reject the fixed hike. Agree only to a floating 'Fuel Surcharge Mechanism' that goes up/down with the market index.", 
             "**Role:** Heli Operator.\n**Motivation:** Fuel prices spiked and are eating your margin. You want a fixed hike to guarantee profit."),
            
            ("Warehousing Exclusivity", "Logistics", "Easy", 
             "**Role:** Supply Base Manager\n**Context:** A warehouse owner offers a good rate but demands a 5-year exclusive contract. You expect your drilling campaign to end in 2 years.\n**Goal:** Secure the lease for 2 years with an option to extend. Do not agree to exclusivity.", 
             "**Role:** Warehouse Owner.\n**Motivation:** You need a long-term signed lease to show your bank to secure a loan."),
            
            ("Consultancy Rate Hike", "Corporate", "Medium", 
             "**Role:** HR Director\n**Context:** Your strategy consulting firm wants to increase hourly rates by 10%. They claim 'talent retention costs'. You have a frozen budget.\n**Goal:** Hold rates flat. Offer to expand their scope to other projects (volume) in exchange for rate stability.", 
             "**Role:** Partner.\n**Motivation:** Inflation is high, but you care more about utilization. You might trade rate for a guaranteed volume of work."),
            
            ("Office Lease Renewal", "Real Estate", "Hard", 
             "**Role:** Facilities Manager\n**Context:** Your landlord wants a 20% rent hike for the HQ renewal. The commercial real estate market is actually softening.\n**Goal:** Renew flat or with a max 2% increase. Threaten to move to the cheaper suburbs.", 
             "**Role:** Landlord.\n**Motivation:** You are bluffing that you have another tenant lined up. You actually can't afford to have the building empty."),
            
            ("Travel Agency Rebate", "Corporate", "Easy", 
             "**Role:** Procurement Lead\n**Context:** You are selecting a new Global Travel Agency. You have a spend of $10M/year.\n**Goal:** Secure a 3% rebate on all booked volume, payable annually.", 
             "**Role:** Agency Rep.\n**Motivation:** Margins are thin. 3% is too high, you usually offer 1%. You might budge if they promise 100% exclusivity."),
            
            ("Pollution Liability Cap", "Legal", "Hard", 
             "**Role:** General Counsel\n**Context:** A tugboat owner wants to cap their pollution liability at $5M. Your risk analysis shows a spill could cost $50M.\n**Goal:** Insist on Unlimited Liability, or at minimum a $50M cap backed by insurance.", 
             "**Role:** Vessel Owner.\n**Motivation:** Your insurance policy only covers $10M. You literally cannot sign for more than that."),
            
            ("JV Partner Approval", "Governance", "Hard", 
             "**Role:** Asset Manager (Operator)\n**Context:** You need to sole-source a $2M urgent repair to a specific vendor. Your Non-Operating Partner (NOP) usually demands a full tender process.\n**Goal:** Convince the Partner to waive the tender requirement to save critical time.", 
             "**Role:** Partner (NOP).\n**Motivation:** You suspect the Operator is 'gold-plating' costs. You want to block this unless they can prove a safety risk."),
            
            ("Force Majeure Claim", "Legal", "Expert", 
             "**Role:** Contract Manager\n**Context:** A supplier has declared Force Majeure due to a 'severe storm' to excuse a missed delivery. Weather data shows the storm was minor and predictable.\n**Goal:** Formally reject the Force Majeure claim. Enforce Liquidated Damages (LDs) for the delay.", 
             "**Role:** Supplier.\n**Motivation:** The factory was actually damaged due to poor maintenance, not the storm. You need the FM claim to avoid penalties."),
            
            ("IP Ownership Dispute", "R&D", "Hard", 
             "**Role:** R&D Lead\n**Context:** You are co-developing a new sensor with a startup. They want to own the Intellectual Property (IP). You are funding 100% of the dev cost.\n**Goal:** Secure 100% ownership of the IP. Offer them a royalty-free license to use it in other non-competing industries.", 
             "**Role:** Startup CEO.\n**Motivation:** This IP is your company's only real asset. If you sell it, you have nothing."),
            
            ("Local Content Quota", "ESG", "Medium", 
             "**Role:** Local Content Manager\n**Context:** New government regulations mandate 40% local spend. Your prime contractor is currently at 15% and making excuses.\n**Goal:** Demand a detailed 'Local Content Plan' to hit 40% within 6 months. Threaten to withhold payments.", 
             "**Role:** Prime Contractor.\n**Motivation:** Local suppliers are expensive and untrained. Meeting this target will eat your entire profit margin."),
            
            ("HSE Incident Reporting", "HSE", "Medium", 
             "**Role:** HSE Manager\n**Context:** You discovered a contractor supervisor hid a 'Near Miss' incident to protect their safety stats.\n**Goal:** Issue a formal reprimand. Reset their safety bonus to 0% for this quarter to send a message.", 
             "**Role:** Site Supervisor.\n**Motivation:** If the crew loses their bonus, they will mutiny. You tried to hide it to keep morale up."),
            
            ("Green Energy Premium", "ESG", "Medium", 
             "**Role:** Power Buyer\n**Context:** You are buying renewable power (RECs) to meet corporate net-zero goals. The generator wants a 15% premium over grid prices.\n**Goal:** Negotiate the premium down to <5%. Argue that long-term offtake security is worth the discount.", 
             "**Role:** Solar Generator.\n**Motivation:** Demand for green power is skyrocketing. You have other buyers lined up who might pay more.")
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

# CHAT
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
                # SCORING FIX: Explicitly instruct AI on limits + Safety Clamp
                score_prompt = f"""
                Context: {brief}
                Transcript: {t}
                Task: Grade performance. Returns JSON.
                Rules: 
                - total_score (0-100)
                - commercial (0-40) [MAX IS 40]
                - strategy (0-40) [MAX IS 40]
                """
                try:
                    r = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=score_prompt, 
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard, temperature=0.1)
                    ).parsed
                    
                    # SAFETY CLAMP
                    safe_total = min(max(r.total_score, 0), 100)
                    safe_comm = min(max(r.commercial, 0), 40)
                    safe_strat = min(max(r.strategy, 0), 40)
                    
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1: st.metric("Total Score", f"{safe_total}/100"); st.progress(safe_total/100)
                    with c2: st.metric("Commercial", f"{safe_comm}/40"); st.metric("Strategy", f"{safe_strat}/40")
                    with c3: st.info(f"**Feedback:** {r.feedback}")
                    
                    pdf_data = create_pdf(selected_label, brief, {"total": safe_total, "comm": safe_comm, "strat": safe_strat}, r.feedback, st.session_state.messages)
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
