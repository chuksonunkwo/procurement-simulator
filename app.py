import streamlit as st
import sqlite3
import time
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Procurement Simulator Pro",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS: Refined for better alignment and visibility
st.markdown("""
    <style>
    /* 1. Sidebar Title - Adjusted size to prevent awkward wrapping */
    .sidebar-title {
        font-size: 32px !important; /* Reduced from 42px for better fit */
        font-weight: 800 !important;
        color: #2C3E50 !important;
        margin-bottom: 20px !important;
        line-height: 1.2 !important;
        word-wrap: break-word !important;
    }
    
    /* 2. Main Scenario Title - Added padding to ensure visibility */
    .main-scenario-title {
        font-size: 36px !important; /* Increased visibility */
        font-weight: 700 !important;
        color: #2C3E50 !important;
        border-bottom: 2px solid #eee;
        padding-bottom: 15px;
        margin-top: 20px !important; /* Pushes title down so it's not cut off */
    }
    
    /* General Cleanup */
    .block-container { 
        padding-top: 3rem !important; /* Extra padding at top of page */
    }
    .stChatInput { border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 8px; }
    
    /* Fix for sidebar text alignment */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# 🔒 SECURITY: LOGIN
VALID_PASSWORDS = ["negotiate2024", "procurement_master", "demo_user"]

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Professional Login Screen
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🔒 Professional Login")
        st.info("Enter access code to initialize the simulation.")
        password = st.text_input("Access Code", type="password")
        if st.button("Authenticate", type="primary"):
            if password in VALID_PASSWORDS:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Access Denied.")
    return False

if not check_password():
    st.stop()

# --- 2. AI CONNECTION ---
try:
    PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
    LOCATION = os.environ.get("GOOGLE_LOCATION", "us-central1")
except:
    PROJECT_ID = None

@st.cache_resource
def get_client():
    if not PROJECT_ID:
        return None
    try:
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        return None

client = get_client()

# --- 3. DATABASE (Presets) ---
DB_FILE = 'procurement_pro_v6.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS scenarios")
    c.execute('''CREATE TABLE scenarios (
        id INTEGER PRIMARY KEY, title TEXT, category TEXT, 
        difficulty TEXT, user_brief TEXT, system_persona TEXT
    )''')
    
    # 10 PRESET SCENARIOS
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

# --- 4. SCENARIO MANAGEMENT ---

if "custom_scenario" not in st.session_state:
    st.session_state.custom_scenario = None
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Library"

with st.sidebar:
    # 🎨 BIG SIDEBAR TITLE (Using Custom CSS Class)
    st.markdown('<p class="sidebar-title">Procurement Simulator Pro</p>', unsafe_allow_html=True)
    
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.password_correct = False
        st.rerun()
    st.markdown("---")

    # TABS
    tab1, tab2 = st.tabs(["📚 Library", "✨ Create New"])
    
    # TAB 1: LIBRARY
    with tab1:
        scenarios = get_scenarios()
        options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
        selected_label = st.selectbox("Select Scenario", list(options.keys()))
        
        if st.button("▶️ Load Library Scenario", type="primary", use_container_width=True):
            st.session_state.active_mode = "Library"
            st.session_state.current_selection_id = options[selected_label]
            st.session_state.messages = []
            st.rerun()

    # TAB 2: CUSTOM
    with tab2:
        st.caption("Describe a real-life situation.")
        user_topic = st.text_area("Situation", placeholder="e.g. Negotiating a software renewal...")
        
        if st.button("✨ Generate & Load", type="primary", use_container_width=True):
            if not user_topic:
                st.warning("Describe a situation first.")
            else:
                with st.spinner("Architecting Simulation..."):
                    try:
                        prompt = f"""
                        Act as Negotiation Architect. User Situation: "{user_topic}"
                        Create simulation JSON:
                        1. 'title': Short title.
                        2. 'user_brief': User's Role & Goal (Markdown).
                        3. 'system_persona': Counterparty Role & Motivation.
                        Output JSON only.
                        """
                        response = client.models.generate_content(
                            model='gemini-2.0-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(response_mime_type="application/json")
                        )
                        data = json.loads(response.text)
                        st.session_state.custom_scenario = data
                        st.session_state.active_mode = "Custom"
                        st.session_state.messages = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")
    
    # LOAD ACTIVE DATA
    active_brief = ""
    active_persona = ""
    active_title = ""

    if st.session_state.active_mode == "Library":
        if "current_selection_id" not in st.session_state:
            st.session_state.current_selection_id = list(options.values())[0]
        active_brief, active_persona, active_title = get_details(st.session_state.current_selection_id)
        
    elif st.session_state.active_mode == "Custom" and st.session_state.custom_scenario:
        data = st.session_state.custom_scenario
        active_title = f"✨ {data.get('title', 'Custom Session')}"
        active_brief = data.get('user_brief', '')
        active_persona = data.get('system_persona', '')

    # BRIEF
    st.markdown("### 📋 Executive Brief")
    with st.container(border=True):
        st.markdown(active_brief)

    # TOOLS
    st.markdown("### 🛠️ Tools")
    if st.button("💡 AI Whisper", use_container_width=True):
        if not st.session_state.messages:
             st.warning("Start negotiating first.")
        else:
            transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            try:
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=f"Context: {active_brief}\nTranscript: {transcript}\nTask: Give one tactical tip."
                )
                st.info(f"**Mentor:** {resp.text}")
            except:
                st.error("Offline.")

    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN CHAT AREA ---

# 🎨 SMALLER MAIN TITLE (Using Custom CSS Class)
st.markdown(f'<p class="main-scenario-title">{active_title}</p>', unsafe_allow_html=True)
st.caption(f"Mode: {st.session_state.active_mode} | Interactive Counterparty")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "👔"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if user_input := st.chat_input("Enter your commercial response..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    sys_prompt = f"""
    Simulation: {active_title}
    My Role (Secret): {active_persona}
    User Brief: {active_brief}
    Directives: Act as tough counterparty. Concise. Negotiate hard.
    """
    
    gemini_history = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

    with st.chat_message("assistant", avatar="👔"):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=gemini_history,
                config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.6)
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.error("Connection Interrupted.")

# --- 6. SCORING ---
class Scorecard(BaseModel):
    total_score: int
    commercial: int
    strategy: int
    feedback: str

st.markdown("---")
with st.expander("📊 End Session & Generate Report", expanded=False):
    if st.button("Analyze Performance"):
        if len(st.session_state.messages) < 2:
            st.warning("Insufficient data.")
        else:
            with st.spinner("Assessing..."):
                transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                try:
                    resp = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=f"""
                        Context: {active_brief}
                        Transcript: {transcript}
                        Task: Grade user (0-100). Schema: {{total_score, commercial, strategy, feedback}} Output: JSON.
                        """,
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard)
                    )
                    r = resp.parsed
                    
                    st.success(f"### Score: {min(r.total_score, 100)} / 100")
                    st.progress(min(r.total_score, 100)/100)
                    
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1:
                        st.metric("💰 Commercial", f"{min(r.commercial, 40)}/40")
                        st.progress(min(r.commercial, 40)/40)
                    with c2:
                        st.metric("♟️ Strategy", f"{min(r.strategy, 40)}/40")
                        st.progress(min(r.strategy, 40)/40)
                    with c3:
                        st.info(f"**Feedback:** {r.feedback}")
                except:
                    st.error("Analysis Error.")
