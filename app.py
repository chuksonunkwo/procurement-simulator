import streamlit as st
import google.generativeai as genai
import requests
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Procurement Negotiation Simulator Pro",
    page_icon="🤝",
    layout="wide"
)

# --- API SETUP ---
# Prioritizes Render Environment Variables to prevent crashes
api_key = None

# 1. Try Render Environment (Server)
try:
    api_key = os.environ.get("GEMINI_API_KEY")
except Exception:
    pass

# 2. Try Streamlit Secrets (Local Testing)
if not api_key:
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

# 3. Final Check
if not api_key:
    st.error("⚠️ API Key missing. Please add GEMINI_API_KEY to Render Environment Variables.")
    st.stop()

# 4. Configure Google AI
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()


# --- LICENSE VERIFICATION (FIXED) ---
def check_license(key):
    """
    Verifies the license key with Gumroad using the specific Product ID.
    """
    # 1. Clean the key
    key = str(key).strip()

    # 2. THE EXACT ID GUMROAD ASKED FOR IN THE ERROR MESSAGE
    PRODUCT_ID = "MFZpNGyCplKf9iTHq2f2xg==" 

    # 3. Ask Gumroad
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": PRODUCT_ID,  # We switched back to product_id as requested
                "license_key": key
            }
        )
        
        # 4. Check result
        data = response.json()
        
        # Debug print (visible in server logs)
        if not data.get("success"):
            print(f"License check failed: {data}")
            
        return data.get("success", False)

    except Exception as e:
        print(f"Connection error: {e}")
        return False

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "scenario_active" not in st.session_state:
    st.session_state.scenario_active = False
if "current_brief" not in st.session_state:
    st.session_state.current_brief = ""

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 100px auto;
        padding: 40px;
        border-radius: 10px;
        background-color: #f0f2f6;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.title("🔒 Professional Login")
        st.info("Enter your License Key to access the Simulator.")
        
        license_key = st.text_input("License Key", type="password")
        
        if st.button("Verify", type="primary", use_container_width=True):
            if check_license(license_key):
                st.session_state.authenticated = True
                st.success("Access Granted. Loading...")
                st.rerun()
            else:
                st.error("❌ Invalid Key. Please check your Gumroad receipt.")
    
    st.stop()  # Stop here if not logged in

# --- MAIN APPLICATION ---

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("Reset Session", type="primary"):
        st.session_state.messages = []
        st.session_state.scenario_active = False
        st.session_state.current_brief = ""
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Procurement Simulator Pro**")
    st.caption("v2.5 | IOC Edition")

# Title
st.title("🤝 Procurement Negotiation Simulator Pro")

# SCENARIO LIBRARY
SCENARIOS = {
    "Deepwater Rig Rate Review": {
        "context": "IOC Oil & Gas",
        "brief": "You are a Category Manager for a major IOC. The rig market is tightening. Your contractor 'TransOceanic' wants to increase day rates by 15% on an active drilling campaign. Your target: keep increase below 5% or trade for performance KPIs."
    },
    "SaaS Renewal Dispute": {
        "context": "IT Procurement",
        "brief": "You are renewing a CRM software license. The vendor has added a 12% 'inflation' hike despite service outages last year. Target: 0% increase + service credits for downtime."
    },
    "Construction Variation Claim": {
        "context": "EPC / Infrastructure",
        "brief": "A sub-contractor is claiming $2M for 'unforeseen ground conditions' on a pipeline project. You suspect they didn't do proper surveys. Target: Settle for <$500k or reject entirely based on Clause 14.2."
    }
}

# --- SCENARIO SELECTION ---
if not st.session_state.scenario_active:
    st.subheader("Select Your Mission")
    
    tab1, tab2 = st.tabs(["📚 Scenario Library", "✨ Create Custom"])
    
    with tab1:
        selected_scenario = st.selectbox("Choose a pre-loaded scenario:", list(SCENARIOS.keys()))
        if st.button("Start Simulation"):
            st.session_state.current_brief = SCENARIOS[selected_scenario]["brief"]
            st.session_state.messages = []
            st.session_state.scenario_active = True
            st.rerun()

    with tab2:
        st.markdown("Describe a specific situation (e.g., 'Negotiating liability caps with a chemical supplier in Germany').")
        custom_input = st.text_area("Situation Description:")
        if st.button("Generate Custom Scenario"):
            if custom_input:
                st.session_state.current_brief = f"Custom Scenario: {custom_input}. Objective: Secure best commercial terms while maintaining relationship."
                st.session_state.messages = []
                st.session_state.scenario_active = True
                st.rerun()

# --- NEGOTIATION INTERFACE ---
if st.session_state.scenario_active:
    # Display Brief
    with st.expander("📄 Mission Brief (Click to View)", expanded=False):
        st.info(st.session_state.current_brief)

    # Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User Input
    user_input = st.chat_input("Type your negotiation response...")

    if user_input:
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Generate AI Response
        with st.chat_message("assistant"):
            with st.spinner("Counterparty is thinking..."):
                try:
                    # Construct Prompt
                    system_prompt = f"""
                    You are a tough, realistic negotiation counterparty. 
                    Scenario Brief: {st.session_state.current_brief}
                    
                    Guidelines:
                    1. Do not give in easily. Push back on price and terms.
                    2. Use emotional leverage (urgency, frustration, silence) if appropriate.
                    3. Keep responses concise (under 3-4 sentences).
                    4. React to the user's tone. If they are weak, dominate. If they are aggressive, defend.
                    """
                    
                    # Create AI Model
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # Build history for context
                    chat_history = [{"role": "user", "parts": system_prompt}]
                    for m in st.session_state.messages:
                        role = "user" if m["role"] == "user" else "model"
                        chat_history.append({"role": role, "parts": m["content"]})
                    
                    # Generate
                    response = model.generate_content(chat_history)
                    bot_reply = response.text
                    
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")

    # --- END SESSION & SCORING ---
    st.markdown("---")
    if st.button("📊 End Session & Generate Report"):
        with st.spinner("Analyzing negotiation performance..."):
            try:
                # Scoring Prompt
                score_prompt = f"""
                Analyze this negotiation transcript based on the following brief: {st.session_state.current_brief}
                
                Transcript:
                {st.session_state.messages}
                
                Provide:
                1. A Score out of 100.
                2. 3 Key Strengths.
                3. 3 Critical Weaknesses.
                4. A 'Better Line' suggestion for one of the user's weak responses.
                5. An IOC/Professional grade assessment (Junior, Senior, CPO Level).
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                analysis = model.generate_content(score_prompt)
                
                with st.expander("📈 Negotiation Scorecard & AAR", expanded=True):
                    st.markdown(analysis.text)
                    
            except Exception as e:
                st.error(f"Analysis Error: {e}")
