import streamlit as st
import google.generativeai as genai
import requests
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Procurement Negotiation Simulator Pro", page_icon="🤝", layout="wide")

# --- PROFESSIONAL STYLING & UI FIXES ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    
    /* EXPANDED SIDEBAR WIDTH FOR BETTER TEXT SPACE */
    section[data-testid="stSidebar"] {
        width: 400px !important;
    }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] { 
        background-color: #f0f2f6; 
        border-right: 1px solid #e0e0e0; 
    }
    
    /* Mission Brief Box */
    .brief-box { 
        background-color: #e8f4f8; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff; 
        margin-bottom: 20px; 
    }
    
    /* High-Visibility Red End Button */
    .stButton button[kind="primary"] { 
        background-color: #ff4b4b; 
        border-color: #ff4b4b; 
        color: white; 
        font-weight: bold;
    }
    .stButton button[kind="primary"]:hover { 
        background-color: #ff3333; 
        border-color: #ff3333; 
    }

    /* Chat Input Floating Bar Visibility */
    [data-testid="stBottom"] {
        background-color: #ffffff;
        border-top: 2px solid #e0e0e0;
        padding-top: 15px;
        padding-bottom: 15px;
        box-shadow: 0px -4px 15px rgba(0,0,0,0.08);
    }
    
    .stChatInputContainer textarea {
        background-color: #f8f9fa;
        border: 1px solid #ced4da;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except: pass

if not api_key:
    st.error("⚠️ API Key missing. Add GEMINI_API_KEY to Render Environment Variables.")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# --- AUTHENTICATION ---
def check_license(key):
    try:
        response = requests.post("https://api.gumroad.com/v2/licenses/verify", 
                               data={"product_id": "MFZpNGyCplKf9iTHq2f2xg==", "license_key": str(key).strip()})
        return response.json().get("success", False)
    except: return False

# Initialize Session States
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "scenario_active" not in st.session_state: st.session_state.scenario_active = False
if "current_brief" not in st.session_state: st.session_state.current_brief = ""
if "current_title" not in st.session_state: st.session_state.current_title = "Welcome"
if "mentor_tip" not in st.session_state: st.session_state.mentor_tip = None

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>🔒 Enterprise Login</h1></div>", unsafe_allow_html=True)
        key = st.text_input("License Key", type="password")
        if st.button("Verify Access", use_container_width=True):
            if check_license(key):
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("❌ Invalid Key")
    st.stop()

# --- SCENARIO DATA (20 CORE CASES) ---
SCENARIOS = {
    "01. Deepwater Rig Rate Review": {"context": "IOC Upstream", "brief": "Category Manager for major IOC. Contractor 'TransOceanic' wants +15% rates mid-contract. Target: <5% or performance KPIs."},
    "02. Marine Logistics Fuel Surcharge": {"context": "Logistics", "brief": "OSV provider demands retroactive fuel surcharge not in contract. Objective: Reject retroactive, negotiate fair forward formula."},
    "03. EPC Variation Claim": {"context": "Infrastructure", "brief": "Sub-contractor claims $2M for 'unforeseen ground conditions'. Objective: Settle <$500k or reject via Clause 14.2."},
    "04. SaaS Renewal Dispute": {"context": "IT", "brief": "CRM renewal. Vendor added 12% inflation despite outages. Objective: 0% hike + service credits."},
    "05. Chemical Force Majeure": {"context": "Chemicals", "brief": "Sole supplier declared FM. Offers 50% volume at +40% price. Objective: Secure 80% volume at max +15% price."},
    "06. Professional Services Rate Card": {"context": "HR", "brief": "Big 4 wants 10% hike. Objective: <3% for Seniors only, freeze Juniors."},
    "07. Maintenance (MRO) Bulk Deal": {"context": "Operations", "brief": "Consolidating 5 workshops. Objective: 15% volume discount rebate structure in exchange for exclusivity."},
    "08. Liability Cap Negotiation": {"context": "Legal", "brief": "Start-up wants $1M cap. Objective: Unlimited for IP/Data, $5M general cap."},
    "09. Subsea Umbilicals Delay": {"context": "Supply Chain", "brief": "4 weeks late. Objective: Enforce LDs or trade for free site engineering."},
    "10. Termination for Convenience": {"context": "Projects", "brief": "Cancelled project. Builder claims Lost Profit. Objective: Pay work done only."},
    "11. Wind Turbine Warranty": {"context": "Renewables", "brief": "Buying 50 turbines. Need 5yr warranty, vendor offers 2yr. Objective: Secure 5yr availability guarantee."},
    "12. Green H2 Tech Risk": {"context": "R&D", "brief": "Pilot plant. Vendor wants Cost Plus. Objective: Target Cost with Cap."},
    "13. Child Labor Allegation": {"context": "ESG", "brief": "NGO report on supply chain. Objective: Immediate audit & zero-tolerance clause."},
    "14. Carbon Footprint": {"context": "Sustainability", "brief": "Logistics provider refuses EV trucks. Objective: Phased transition, pay premium only for green miles."},
    "15. Red Sea Blockade": {"context": "Logistics", "brief": "Route blocked. Forwarder wants $500k surcharge. Objective: Split 50/50."},
    "16. Supplier Insolvency": {"context": "Risk", "brief": "Supplier bankrupt. Receiver demands cash. Objective: Pay for raw materials only."},
    "17. The 'Rogue' Stakeholder": {"context": "Internal", "brief": "VP promised job to expensive vendor. Objective: Walk back promise, force competition."},
    "18. Budget Cut Survival": {"context": "Strategy", "brief": "Budget cut 20%. Objective: Secure 10% discount from top 3 providers."},
    "19. AI IP Ownership": {"context": "IT/AI", "brief": "Dev shop wants code IP. Objective: Work Made for Hire (you own it)."},
    "20. Cloud Overspend": {"context": "IT", "brief": "AWS budget blown by $200k. Objective: Forgiveness credit for 3yr commitment."}
}

# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    mode = st.radio("Mode:", ["📚 Scenarios", "✨ AI Architect (Custom)"])
    st.markdown("---")
    
    if mode == "📚 Scenarios":
        sel = st.selectbox("Select Scenario:", list(SCENARIOS.keys()))
        if st.button("▶️ Start Simulation", use_container_width=True):
            st.session_state.current_title = sel
            st.session_state.current_brief = SCENARIOS[sel]['brief']
            st.session_state.messages = []
            st.session_state.scenario_active = True
            st.session_state.mentor_tip = None
            st.rerun()
    else:
        ctx = st.text_input("Industry Context", placeholder="e.g. Mining, Oil and Gas")
        obj = st.text_area("Objective", placeholder="Describe your situation...")
        if st.button("✨ Generate & Start", use_container_width=True):
            if obj:
                st.session_state.current_title = f"Custom: {ctx}"
                st.session_state.current_brief = obj
                st.session_state.messages = []
                st.session_state.scenario_active = True
                st.session_state.mentor_tip = None
                st.rerun()

    if st.session_state.scenario_active:
        st.markdown("---")
        st.markdown("### 💡 AI Mentor")
        # REDUCED VERBOSITY IN MENTOR PROMPT
        if st.button("Get a Tactical Hint"):
            with st.spinner("Analyzing strategy..."):
                try:
                    tip_prompt = f"Negotiation context: {st.session_state.current_brief}. Current history: {st.session_state.messages}. Provide ONE short, sharp tactical tip for the user. BE CONCISE. Max 2 sentences."
                    mentor_resp = genai.GenerativeModel("gemini-2.0-flash-exp").generate_content(tip_prompt)
                    st.session_state.mentor_tip = mentor_resp.text
                except: st.session_state.mentor_tip = "Strategy: Test their claim by asking for specific supporting data."
        if st.session_state.mentor_tip:
            st.info(st.session_state.mentor_tip)

        st.markdown("---")
        if st.button("🛑 End Negotiation", type="primary", use_container_width=True): 
            st.session_state.show_score = True
            
        if st.button("🔄 Reset / New Session", use_container_width=True):
            st.session_state.scenario_active = False
            st.session_state.messages = []
            st.session_state.show_score = False
            st.session_state.mentor_tip = None
            st.rerun()

    st.markdown("---")
    with st.expander("⚖️ Disclaimer & Privacy"):
        st.caption("**Fictitious Entities:** All company names (e.g. 'TransOceanic') are fictitious for training purposes. No real association is intended.")
        st.caption("**Privacy:** Zero-retention architecture. No chat logs or scenarios are stored permanently.")
        st.caption("**Not Legal Advice:** Simulation results are educational and should not be relied upon for live contracts.")
    
    st.caption("Procurement Simulator Pro\nv2.0 | Enterprise | Gemini 2.0")

# --- MAIN INTERFACE ---
st.title("🤝 Procurement Negotiation Simulator")

if not st.session_state.scenario_active:
    st.markdown("### Welcome, Professional.\nSelect a mission from the **Control Panel** to enter the arena.")

else:
    # Mission Brief Display
    st.markdown(f"<div class='brief-box'><h4>📄 {st.session_state.current_title}</h4><p>{st.session_state.current_brief}</p></div>", unsafe_allow_html=True)

    # Chat History
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="👤" if m["role"]=="user" else "🤖"): 
            st.write(m["content"])

    # Input Area
    if user_in := st.chat_input("Type your proposal..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user", avatar="👤"): st.write(user_in)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Counterparty is thinking..."):
                try:
                    hist = [{"role": "user", "parts": f"You are a tough, realistic commercial counterparty. Scenario: {st.session_state.current_brief}. Be concise and push back on terms."}]
                    for m in st.session_state.messages: 
                        hist.append({"role": "user" if m["role"]=="user" else "model", "parts": m["content"]})
                    
                    model = genai.GenerativeModel("gemini-2.0-flash-exp")
                    resp = model.generate_content(hist)
                    st.write(resp.text)
                    st.session_state.messages.append({"role": "assistant", "content": resp.text})
                except Exception as e: st.error(f"AI Error: {e}")

    # Scorecard Logic
    if st.session_state.get("show_score", False):
        st.markdown("---")
        with st.spinner("Compiling Chief Procurement Officer Scorecard..."):
            try:
                score_prompt = f"Analyze negotiation: {st.session_state.current_brief}. History: {st.session_state.messages}. Provide: Score (0-100), Exec Summary, 3 Strengths, 3 Weaknesses, and Coaching Tip."
                analysis = genai.GenerativeModel("gemini-2.0-flash-exp").generate_content(score_prompt)
                
                st.balloons()
                with st.expander("📈 Negotiation Scorecard", expanded=True):
                    st.markdown(analysis.text)
                    st.download_button("📥 Download After-Action Review", analysis.text, "report.txt")
                st.session_state.show_score = False
            except Exception as e: st.error(f"Scoring Error: {e}")
