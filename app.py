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
api_key = None
try:
    api_key = os.environ.get("GEMINI_API_KEY")
except Exception:
    pass

if not api_key:
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not api_key:
    st.error("⚠️ API Key missing. Please add GEMINI_API_KEY to Render Environment Variables.")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()


# --- DIAGNOSTIC LICENSE CHECKER ---
def check_license_debug(key):
    """
    Verifies the license key and returns the RAW response for debugging.
    """
    key = str(key).strip()
    
    # YOUR PRODUCT PERMALINK
    # Based on your URL: https://chukster06.gumroad.com/l/procurement-sim-pro
    PRODUCT_PERMALINK = "procurement-sim-pro" 

    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_permalink": PRODUCT_PERMALINK,
                "license_key": key,
                "increment_uses_count": "false"  # Don't use up a 'seat' just for testing
            }
        )
        
        return response.json()

    except Exception as e:
        return {"success": False, "message": f"Connection Error: {str(e)}"}

# --- SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "scenario_active" not in st.session_state:
    st.session_state.scenario_active = False
if "current_brief" not in st.session_state:
    st.session_state.current_brief = ""

# --- LOGIN SCREEN (DEBUG MODE) ---
if not st.session_state.authenticated:
    st.markdown("""
    <style>
    .login-container { max-width: 500px; margin: 100px auto; text-align: center; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.title("🔒 Professional Login")
        st.info("Enter your License Key to access the Simulator.")
        
        license_key = st.text_input("License Key", type="password")
        
        if st.button("Verify", type="primary", use_container_width=True):
            
            # RUN DEBUG CHECK
            result = check_license_debug(license_key)
            
            if result.get("success") == True:
                st.session_state.authenticated = True
                st.success("Access Granted. Loading...")
                st.rerun()
            else:
                # SHOW THE EXACT ERROR FROM GUMROAD
                st.error("❌ Verification Failed")
                st.warning(f"🔍 Debug Info (Send this to support): {result}")
    
    st.stop()

# --- MAIN APP (Standard content below) ---
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("Reset Session", type="primary"):
        st.session_state.messages = []
        st.session_state.scenario_active = False
        st.rerun()
    st.markdown("---")
    st.markdown("**Procurement Simulator Pro**")
    st.caption("v2.4 | IOC Edition")

st.title("🤝 Procurement Negotiation Simulator Pro")

# SCENARIO LIBRARY
SCENARIOS = {
    "Deepwater Rig Rate Review": {"brief": "Context: IOC Oil & Gas. Contractor wants +15% rates. Target: <5%."},
    "SaaS Renewal Dispute": {"brief": "Context: IT Procurement. Vendor wants +12% inflation. Target: 0% + credits."},
    "Construction Variation": {"brief": "Context: EPC. Subcontractor claims $2M for ground conditions. Target: <$500k."}
}

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
        custom_input = st.text_area("Situation Description:")
        if st.button("Generate Custom"):
            if custom_input:
                st.session_state.current_brief = f"Custom: {custom_input}"
                st.session_state.messages = []
                st.session_state.scenario_active = True
                st.rerun()

if st.session_state.scenario_active:
    with st.expander("📄 Mission Brief", expanded=False):
        st.info(st.session_state.current_brief)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Type your negotiation response...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Counterparty is thinking..."):
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    chat_history = []
                    for m in st.session_state.messages:
                         role = "user" if m["role"] == "user" else "model"
                         chat_history.append({"role": role, "parts": m["content"]})
                    
                    response = model.generate_content(chat_history)
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"AI Error: {e}")

    st.markdown("---")
    if st.button("📊 End Session & Generate Report"):
        with st.spinner("Analyzing..."):
            try:
                score_prompt = f"Score this negotiation (0-100) based on brief: {st.session_state.current_brief}. History: {st.session_state.messages}"
                model = genai.GenerativeModel("gemini-1.5-flash")
                analysis = model.generate_content(score_prompt)
                with st.expander("📈 Scorecard", expanded=True):
                    st.markdown(analysis.text)
            except Exception as e:
                st.error(f"Analysis Error: {e}")
