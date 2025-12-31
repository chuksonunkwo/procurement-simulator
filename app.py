import streamlit as st
import sqlite3
import time
import os
import json
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Procurement Simulator Pro",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# ⬇️ SETTINGS ⬇️
# Replace this with your Gumroad Link ID if you have it. 
# Otherwise, the default allows testing.
GUMROAD_PRODUCT_PERMALINK = "procurement-sim-pro" 

# CSS STYLING
st.markdown("""
    <style>
    .sidebar-title {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #2C3E50 !important;
        margin-bottom: 20px !important;
        line-height: 1.2 !important;
        word-wrap: break-word !important;
    }
    .main-scenario-title {
        font-size: 36px !important;
        font-weight: 700 !important;
        color: #2C3E50 !important;
        border-bottom: 2px solid #eee;
        padding-bottom: 15px;
        margin-top: 20px !important;
    }
    .block-container { padding-top: 3rem !important; }
    .stChatInput { border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 8px; }
    section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# 🔒 LICENSE CHECK
def check_license(key):
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={"product_permalink": GUMROAD_PRODUCT_PERMALINK, "license_key": key.strip()}
        )
        return response.json().get("success", False)
    except:
        return False

if "license_valid" not in st.session_state:
    st.session_state.license_valid = False

if not st.session_state.license_valid:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🔒 Professional Login")
        st.info("Enter your License Key.")
        key_input = st.text_input("License Key", type="password")
        if st.button("Verify", type="primary"):
            if key_input == "negotiate2024" or check_license(key_input):
                st.session_state.license_valid = True
                st.rerun()
            else:
                st.error("❌ Invalid Key")
    st.stop()

# --- 2. AI CONNECTION (ROBUST) ---
try:
    API_KEY = os.environ.get("GEMINI_API_KEY")
except:
    API_KEY = None

@st.cache_resource
def get_client():
    if not API_KEY:
        return None
    try:
        return genai.Client(api_key=API_KEY)
    except:
        return None

client = get_client()

# --- 3. DATABASE ---
DB_FILE = 'procurement_pro_v7.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS scenarios")
    c.execute('''CREATE TABLE scenarios (
        id INTEGER PRIMARY KEY, title TEXT, category TEXT, 
        difficulty TEXT, user_brief TEXT, system_persona TEXT
    )''')
    
    data = [
        ("EPC Steel Variation Claim", "Construction", "Hard",
         "**Role:** Project Director.\n**Situation:** Contractor claims $5M for steel price hikes.\n**Goal:** Reject the claim completely. Protect the schedule.", 
         "**Role:** Contractor PM.\n**Motivation:** You are facing bankruptcy. You need cash or you will stop work."),
        ("Deepwater Rig Rate", "Drilling", "Medium",
         "**Role:** Wells Lead.\n**Situation:** Oil price crash. Rig rates dropped 30%.\n**Goal:** Reduce current rate by 20%. Offer 1-year extension as sweetener.", 
         "**Role:** Rig Contractor.\n**Motivation:** You are terrified of stacking the rig. You need this contract."),
        ("FX & Price Indexation", "Commercial", "Hard",
         "**Role:** Category Manager.\n**Situation:** Supplier demands CPI + 5% and FX protection.\n**Goal:** Cap escalation at 2% fixed. Deny FX risk transfer.", 
         "**Role:** Global Manufacturer.\n**Motivation:** Your raw materials are in USD, contract is in Local Currency. You are losing margin."),
        ("Pollution Liability Cap", "Legal", "Hard",
         "**Role:** Legal Counsel.\n**Situation:** Vessel owner wants Liability Cap limited to $5M.\n**Goal:** Insist on Unlimited Liability or $50M minimum.", 
         "**Role:** Vessel Owner.\n**Motivation:** Your insurance only covers $10M. You literally cannot sign for more."),
        ("HSE Incident Reporting", "HSE", "Medium",
         "**Role:** HSE Manager.\n**Situation:** Contractor failed to report a 'Near Miss'.\n**Goal:** Implement 'Stop Work'. Reset safety bonus to 0%.", 
         "**Role:** Site Supervisor.\n**Motivation:** If you report it, your crew loses their bonus. You tried to hide it."),
        ("JV Partner Approval", "Governance", "Hard",
         "**Role:** Asset Manager (Operator).\n**Situation:** Sole Source critical repair ($2M).\n**Goal:** Get Partner approval to skip tender.", 
         "**Role:** Partner (NOP).\n**Motivation:** You suspect the Operator is overspending. You demand a full tender."),
        ("MSA Negotiation Assist", "Contracting", "Medium",
         "**Role:** Contracts Lead.\n**Situation:** Negotiating 5-year MSA.\n**Goal:** Remove 'Consequential Damages' waiver.", 
         "**Role:** Sales VP.\n**Motivation:** Legal will never allow waiver removal. But you can discount price."),
        ("Marine Demurrage", "Logistics", "Easy",
         "**Role:** Logistics Supt.\n**Situation:** Vessel delayed 3 days.\n**Goal:** Pay $0 demurrage. Delay was crane failure.", 
         "**Role:** Shipowner.\n**Motivation:** You know the crane was shaky, but you will blame 'Port Congestion'."),
        ("FPSO Termination Threat", "Production", "Hard",
         "**Role:** Asset Mgr.\n**Situation:** FPSO performance is poor.\n**Goal:** Get remedial plan or threaten termination.", 
         "**Role:** FPSO Operator.\n**Motivation:** Spare parts are stuck in customs. You are terrified of losing the contract."),
        ("Local Content vs Schedule", "ESG", "Medium",
         "**Role:** Local Content Mgr.\n**Situation:** Supplier ignoring local hiring targets.\n**Goal:** Enforce 40% local spend.", 
         "**Role:** Supplier.\n**Motivation:** Local staff are untrained. Training them will delay project 3 months.")
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
    return conn.cursor().execute("SELECT user_brief, system_persona, title FROM scenarios WHERE id=?", (sid,)).fetchone()

# --- 4. UI ---
if "custom_scenario" not in st.session_state:
    st.session_state.custom_scenario = None
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Library"

with st.sidebar:
    st.markdown('<p class="sidebar-title">Procurement Simulator Pro</p>', unsafe_allow_html=True)
    if st.button("🚪 Log Out"):
        st.session_state.license_valid = False
        st.rerun()
    st.markdown("---")

    tab1, tab2 = st.tabs(["📚 Library", "✨ Create New"])
    
    with tab1:
        scenarios = get_scenarios()
        options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
        selected = st.selectbox("Select Scenario", list(options.keys()))
        if st.button("▶️ Load Library", type="primary"):
            st.session_state.active_mode = "Library"
            st.session_state.current_selection_id = options[selected]
            st.session_state.messages = []
            st.rerun()

    with tab2:
        st.caption("Enter a custom situation:")
        user_topic = st.text_area("Situation", height=100)
        if st.button("✨ Generate", type="primary"):
            if not client:
                st.error("❌ System Error: API Key not detected on Server.")
            elif not user_topic:
                st.warning("Please type a situation first.")
            else:
                with st.spinner("Generating scenario..."):
                    try:
                        # Using 1.5-flash for maximum stability with API Keys
                        resp = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=f"""
                            Role: Negotiation Architect.
                            Input: "{user_topic}"
                            Output JSON: {{
                                "title": "Short Title",
                                "user_brief": "Role & Goal (Markdown)",
                                "system_persona": "Counterparty Role & Hidden Motivation"
                            }}
                            """,
                            config=types.GenerateContentConfig(response_mime_type="application/json")
                        )
                        st.session_state.custom_scenario = json.loads(resp.text)
                        st.session_state.active_mode = "Custom"
                        st.session_state.messages = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Generation Failed. Error details: {str(e)}")

    st.markdown("---")
    
    # LOAD DATA
    if st.session_state.active_mode == "Library":
        if "current_selection_id" not in st.session_state:
            st.session_state.current_selection_id = list(options.values())[0]
        brief, persona, title = get_details(st.session_state.current_selection_id)
    else:
        data = st.session_state.custom_scenario
        if data:
            title = f"✨ {data.get('title')}"
            brief = data.get('user_brief')
            persona = data.get('system_persona')
        else:
            title, brief, persona = "No Scenario", "Please load a scenario.", ""

    st.markdown("### 📋 Brief")
    st.info(brief)

    st.markdown("### 🛠️ Tools")
    if st.button("💡 Whisper Hint"):
        if not st.session_state.messages:
            st.warning("Chat first.")
        else:
            try:
                # Using 1.5-flash
                transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                r = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=f"Context: {brief}\nChat: {transcript}\nGive 1 short tip."
                )
                st.success(r.text)
            except:
                st.error("Advisor Offline")

    if st.button("🔄 Reset"):
        st.session_state.messages = []
        st.rerun()

# --- 5. CHAT ---
st.markdown(f'<p class="main-scenario-title">{title}</p>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "👔"):
        st.markdown(msg["content"])

if inp := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": inp})
    with st.chat_message("user", avatar="👤"):
        st.markdown(inp)

    # Gemini 1.5 Flash for Chat
    gemini_hist = [types.Content(role="user" if m["role"]=="user" else "model", parts=[types.Part(text=m["content"])]) for m in st.session_state.messages]
    
    with st.chat_message("assistant", avatar="👔"):
        try:
            r = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=gemini_hist,
                config=types.GenerateContentConfig(
                    system_instruction=f"Role: {persona}. Context: {brief}. Be tough. Concise.",
                    temperature=0.7
                )
            )
            st.markdown(r.text)
            st.session_state.messages.append({"role": "assistant", "content": r.text})
        except:
            st.error("Connection Error")

# --- 6. SCORE ---
class Scorecard(BaseModel):
    total_score: int
    commercial: int
    strategy: int
    feedback: str

st.markdown("---")
with st.expander("📊 Scorecard"):
    if st.button("Calculate"):
        try:
            transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            r = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"Context: {brief}\nChat: {transcript}\nGrade (0-100). JSON output.",
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard)
            )
            d = r.parsed
            st.balloons()
            st.metric("Total Score", f"{d.total_score}/100")
            st.progress(min(d.total_score, 100)/100)
            c1, c2 = st.columns(2)
            c1.metric("Commercial", d.commercial)
            c2.metric("Strategy", d.strategy)
            st.write(d.feedback)
        except Exception as e:
            st.error(f"Scoring failed: {e}")
