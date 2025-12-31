import streamlit as st
import sqlite3
import time
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

# --- 1. CONFIGURATION & CORPORATE STYLING ---
st.set_page_config(
    page_title="Procurement Simulator Pro",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    h1 { color: #0E1117; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    .stChatInput { border-radius: 10px; }
    .sidebar-text { font-size: 1.2rem; font-weight: bold; color: #444; }
    div[data-testid="stExpander"] { border: 1px solid #ddd; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 🔒 SECURITY: LOGIN SYSTEM
VALID_PASSWORDS = ["negotiate2024", "procurement_master", "demo_user"]

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Login Screen
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🔒 Professional Login")
        st.info("Please enter your access code to initialize the simulation environment.")
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

# --- 2. ENTERPRISE AI CONNECTION ---
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

# --- 3. DATABASE (Full Library) ---
DB_FILE = 'procurement_pro_v3.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS scenarios")
    # Table has 5 content columns (+1 Auto ID)
    c.execute('''CREATE TABLE scenarios (
        id INTEGER PRIMARY KEY, 
        title TEXT, 
        category TEXT, 
        difficulty TEXT, 
        user_brief TEXT, 
        system_persona TEXT
    )''')
    
    # ALL 10 SCENARIOS RESTORED
    data = [
        ("EPC Steel Variation Claim", "Construction", "Hard",
         "**Role:** Project Director.\n**Situation:** Contractor claims $5M for steel price hikes.\n**Goal:** Reject the claim completely. Protect the schedule.", 
         "**Role:** Contractor PM.\n**Motivation:** You are facing bankruptcy. You need cash or you will stop work."),
        
        ("Deepwater Rig Rate", "Drilling", "Medium",
         "**Role:** Wells Lead.\n**Situation:** Oil price crash. Rig rates dropped 30%.\n**Goal:** Reduce current rate by 20%. Offer 1-year extension as sweetener.", 
         "**Role:** Rig Contractor.\n**Motivation:** You are terrified of stacking the rig (idling costs). You need this contract."),
        
        ("FX & Price Indexation", "Commercial", "Hard",
         "**Role:** Category Manager.\n**Situation:** Supplier demands CPI + 5% and FX protection.\n**Goal:** Cap escalation at 2% fixed. Deny FX risk transfer.", 
         "**Role:** Global Manufacturer.\n**Motivation:** Your raw materials are in USD, contract is in Local Currency. You are losing margin fast."),
        
        ("Pollution Liability Cap", "Legal", "Hard",
         "**Role:** Legal Counsel.\n**Situation:** Vessel owner wants Liability Cap limited to $5M.\n**Goal:** Insist on Unlimited Liability for pollution or $50M minimum.", 
         "**Role:** Vessel Owner.\n**Motivation:** Your insurance only covers $10M. You literally cannot sign for more."),
        
        ("HSE Incident Reporting", "HSE", "Medium",
         "**Role:** HSE Manager.\n**Situation:** Contractor failed to report a 'Near Miss'.\n**Goal:** Implement 'Stop Work'. Reset safety bonus to 0%.", 
         "**Role:** Site Supervisor.\n**Motivation:** If you report it, your crew loses their bonus. You tried to hide it to keep morale high."),
        
        ("JV Partner Approval", "Governance", "Hard",
         "**Role:** Asset Manager (Operator).\n**Situation:** Sole Source critical repair ($2M).\n**Goal:** Get Partner approval to skip tender process.", 
         "**Role:** Partner (NOP).\n**Motivation:** You suspect the Operator is overspending. You demand a full tender."),
        
        ("MSA Negotiation Assist", "Contracting", "Medium",
         "**Role:** Contracts Lead.\n**Situation:** Negotiating 5-year MSA.\n**Goal:** Remove 'Consequential Damages' waiver.", 
         "**Role:** Sales VP.\n**Motivation:** Corporate legal will never allow waiver removal. It is a red line. But you can discount price."),
         
        ("Marine Demurrage", "Logistics", "Easy",
         "**Role:** Logistics Supt.\n**Situation:** Vessel delayed 3 days.\n**Goal:** Pay $0 demurrage. Delay was crane failure.", 
         "**Role:** Shipowner.\n**Motivation:** You know the crane was shaky, but you will blame 'Port Congestion' to get paid."),
         
        ("FPSO Termination Threat", "Production", "Hard",
         "**Role:** Asset Mgr.\n**Situation:** FPSO performance is poor.\n**Goal:** Get remedial plan or threaten termination.", 
         "**Role:** FPSO Operator.\n**Motivation:** Spare parts are stuck in customs. You are terrified of losing the contract."),
         
        ("Local Content vs Schedule", "ESG", "Medium",
         "**Role:** Local Content Mgr.\n**Situation:** Supplier ignoring local hiring targets.\n**Goal:** Enforce 40% local spend immediately.", 
         "**Role:** Supplier.\n**Motivation:** Local staff are untrained. Training them will delay the project 3 months.")
    ]
    
    # 5 Question Marks for 5 Data Fields
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

# --- 4. PROFESSIONAL UI ---
with st.sidebar:
    st.markdown("## 🏢 Procurement Negotiation Simulator")
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.password_correct = False
        st.rerun()
    st.markdown("---")
    
    scenarios = get_scenarios()
    # Format: "Category | Title (Difficulty)"
    options = {f"{s[2]} | {s[1]} ({s[3]})": s[0] for s in scenarios}
    selected_label = st.selectbox("Select Simulation Scenario", list(options.keys()))
    selected_id = options[selected_label]
    
    brief, persona = get_details(selected_id)
    
    st.markdown("### 📋 Executive Brief")
    with st.container(border=True):
        st.markdown(brief)
    
    st.markdown("### 🛠️ Strategic Tools")
    if st.button("💡 AI Strategic Whisper", use_container_width=True):
        if not st.session_state.get("messages"):
             st.warning("Please begin the negotiation first.")
        else:
            transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            try:
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=f"Context: {brief}\nHistory: {transcript}\nTask: You are a senior mentor. Give ONE sharp, tactical suggestion to gain leverage."
                )
                st.info(f"**Mentor:** {resp.text}")
            except:
                st.error("Mentor currently unavailable.")

    if st.button("🔄 Reset Simulation", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Page Header
st.title(selected_label.split("|")[1].strip())
st.caption(f"Category: {selected_label.split('|')[0]} | Mode: Interactive AI Counterparty")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat Interface
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "👔"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Game Logic
if user_input := st.chat_input("Enter your commercial response..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    sys_prompt = f"""
    Context: {selected_label}
    Your Role: {persona}
    Directives:
    1. Act as the tough counterparty.
    2. Be concise (max 2-3 sentences).
    3. Do NOT reveal your hidden pressure immediately.
    4. Negotiate hard.
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
            st.error("Connection Interrupted. Please check API quota.")

# --- 5. ANALYTICS ---
class Scorecard(BaseModel):
    total_score: int
    commercial: int
    strategy: int
    feedback: str

st.markdown("---")
with st.expander("📊 End Session & Generate Performance Report", expanded=False):
    if st.button("Analyze Performance"):
        if len(st.session_state.messages) < 2:
            st.warning("Insufficient data for analysis.")
        else:
            with st.spinner("Generating CPO Assessment..."):
                transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                try:
                    resp = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=f"""
                        Context: {brief}
                        Transcript: {transcript}
                        Task: Grade the user (0-100).
                        Schema: {{total_score (0-100), commercial (0-40), strategy (0-40), feedback (string)}}
                        Output: JSON.
                        """,
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard)
                    )
                    r = resp.parsed
                    
                    # Safety Clamps
                    safe_total = min(r.total_score, 100)
                    safe_comm = min(r.commercial, 40)
                    safe_strat = min(r.strategy, 40)

                    st.success(f"### Final Score: {safe_total} / 100")
                    st.progress(safe_total / 100)
                    
                    c1, c2, c3 = st.columns([1,1,2])
                    with c1:
                        st.metric("💰 Commercial Value", f"{safe_comm}/40")
                        st.progress(safe_comm/40)
                    with c2:
                        st.metric("♟️ Strategic Leverage", f"{safe_strat}/40")
                        st.progress(safe_strat/40)
                    with c3:
                        st.info(f"**CPO Feedback:** {r.feedback}")

                except Exception as e:
                    st.error(f"Analysis Error: {e}")
