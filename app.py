import streamlit as st
import sqlite3
import time
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="Procurement Pro", layout="wide", page_icon="💼")

# 🔒 SECURITY: LOGIN SYSTEM
# In a real app, use a database or environment variables for this.
VALID_PASSWORDS = ["negotiate2024", "procurement_master", "demo_user"]

def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.markdown("## 🔒 Login Required")
    st.markdown("Please enter the access code provided with your purchase.")
    
    password = st.text_input("Access Code", type="password")
    
    if st.button("Log In"):
        if password in VALID_PASSWORDS:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Invalid Code.")
    return False

if not check_password():
    st.stop()

# --- 2. SECURE AI CONNECTION ---
try:
    # Render looks for Environment Variables
    PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
    LOCATION = os.environ.get("GOOGLE_LOCATION", "us-central1")
except:
    PROJECT_ID = None
    LOCATION = "us-central1"

@st.cache_resource
def get_client():
    if not PROJECT_ID:
        return None
    try:
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        return None

client = get_client()

# --- 3. DATABASE LAYER ---
DB_FILE = 'procurement_saas_v2.db' # V2 forces a fresh database build

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
    
    data = [
        ("EPC Steel Variation Claim", "Construction", "Hard",
         "**Role:** Project Director.\n**Goal:** Reject $5M steel hike.", 
         "**Role:** Contractor PM.\n**Pressure:** Bankruptcy risk. Need cash."),
        ("SaaS Renewal", "IT", "Medium",
         "**Role:** IT Procurement.\n**Goal:** Cap increase at 3% (CPI).", 
         "**Role:** Sales VP.\n**Pressure:** Need to hit quarterly target."),
        ("JV Partner Approval", "Governance", "Hard",
         "**Role:** Asset Mgr.\n**Goal:** Sole Source $2M. Skip tender.", 
         "**Role:** Partner (NOP).\n**Pressure:** Suspect overspending."),
        ("Logistics Demurrage", "Logistics", "Easy",
         "**Role:** Logistics Supt.\n**Goal:** Pay $0. Crane failure.", 
         "**Role:** Shipowner.\n**Pressure:** Blame port congestion.")
    ]
    
    # ✅ FIX IS HERE: Exactly 5 question marks for 5 columns
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

# --- 4. APP UI ---
with st.sidebar:
    st.markdown("## 💼 Procurement Pro")
    if st.button("🚪 Log Out"):
        st.session_state.password_correct = False
        st.rerun()
    st.markdown("---")
    
    scenarios = get_scenarios()
    options = {f"{s[2]} | {s[1]}": s[0] for s in scenarios}
    selected_label = st.selectbox("Select Scenario", list(options.keys()))
    selected_id = options[selected_label]
    
    brief, persona = get_details(selected_id)
    with st.expander("📋 Mission Brief", expanded=True):
        st.info(brief)
    
    if st.button("💡 AI Advisor"):
        if not st.session_state.get("messages"):
             st.warning("Chat first.")
        else:
            transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            try:
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=f"Context: {brief}\nHistory: {transcript}\nGive one tactical negotiation tip."
                )
                st.info(resp.text)
            except:
                st.error("Advisor Offline.")

    if st.button("🔄 Reset"):
        st.session_state.messages = []
        st.rerun()

st.title(selected_label.split("|")[1].strip())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Enter response..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    sys_prompt = f"""
    Context: {selected_label}
    Role: {persona}
    Act as the supplier. Be tough but realistic. Concise responses.
    """
    
    gemini_history = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_history.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=gemini_history,
                config=types.GenerateContentConfig(system_instruction=sys_prompt, temperature=0.6)
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.error("AI Connection Error.")

# --- 5. SCORING ---
class Scorecard(BaseModel):
    total_score: int
    feedback: str

if st.button("📊 End & Score"):
    if len(st.session_state.messages) < 2:
        st.warning("Chat more first.")
    else:
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        try:
            resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"Context: {brief}\nTranscript: {transcript}\nGrade 0-100 JSON.",
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Scorecard)
            )
            r = resp.parsed
            st.success(f"Score: {r.total_score}/100")
            st.progress(min(r.total_score, 100)/100)
            st.write(r.feedback)
        except Exception as e:
            st.error(f"Error: {e}")
