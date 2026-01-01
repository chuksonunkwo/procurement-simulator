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

# --- PROFESSIONAL STYLING (CSS) ---
st.markdown("""
<style>
    /* Professional Login Box */
    .login-container {
        max-width: 500px;
        margin: 100px auto;
        padding: 40px;
        border-radius: 12px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    /* Sidebar Branding */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* Button Styling */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
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


# --- LICENSE VERIFICATION ---
def check_license(key):
    """
    Verifies the license key using the validated Gumroad Product ID.
    """
    key = str(key).strip()
    
    # VALIDATED PRODUCT ID
    PRODUCT_ID = "MFZpNGyCplKf9iTHq2f2xg==" 

    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": PRODUCT_ID,
                "license_key": key
            }
        )
        
        data = response.json()
        
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
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>🔒 Professional Login</h1></div>", unsafe_allow_html=True)
        st.info("Please enter your Enterprise License Key to access the simulator.")
        
        license_key = st.text_input("License Key", type="password")
        
        if st.button("Verify Access", type="primary", use_container_width=True):
            if check_license(license_key):
                st.session_state.authenticated = True
                st.toast("✅ Access Granted", icon="🔓")
                st.rerun()
            else:
                st.error("❌ Invalid Key. Please check your Gumroad receipt.")
    st.stop()

# --- MAIN APPLICATION ---

# Sidebar
with st.sidebar:
    st.header("⚙️ Control Panel")
    if st.button("🔄 Reset Simulation", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.scenario_active = False
        st.session_state.current_brief = ""
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🛠 Tools")
    st.caption("• Negotiation Brief")
    st.caption("• Live AI Counterparty")
    st.caption("• CPO Scorecard")
    st.caption("• PDF Export (Beta)")
    st.markdown("---")
    st.caption("Procurement Simulator Pro\nv2.6 | IOC Edition")

# Main Header
st.title("🤝 Procurement Negotiation Simulator Pro")
st.markdown("*Master high-stakes commercial deals with AI-powered roleplay.*")
st.divider()

# --- FULL 10-SCENARIO LIBRARY ---
SCENARIOS = {
    "1. Deepwater Rig Rate Review": {
        "context": "IOC Oil & Gas / Upstream",
        "brief": "Context: You are a Category Manager for a major IOC. The rig market is tightening. Contractor 'TransOceanic' wants to increase day rates by 15% on an active drilling campaign mid-contract. Objective: Keep increase below 5% or trade for significant performance KPIs. Walk-away: 8% increase."
    },
    "2. Marine Logistics (OSV) Fuel Surcharge": {
        "context": "Marine Logistics",
        "brief": "Context: Your Offshore Support Vessel (OSV) provider is demanding a new 'Bunker Adjustment Factor' (fuel surcharge) due to rising diesel prices, retroactive for 6 months. This is not in the contract. Objective: Reject retroactive charges, negotiate a fair forward-looking formula."
    },
    "3. EPC Construction Variation Claim": {
        "context": "EPC / Infrastructure",
        "brief": "Context: A major sub-contractor is claiming $2M for 'unforeseen ground conditions' on a pipeline project. You suspect they failed to do proper surveys (which were their scope). Objective: Settle for <$500k or reject entirely based on Clause 14.2 (Site Conditions)."
    },
    "4. SaaS Renewal Dispute": {
        "context": "IT Procurement",
        "brief": "Context: You are renewing a mission-critical CRM license. The vendor has added a 12% 'inflation' hike despite 3 major service outages last year. Objective: 0% increase + secure service credits (refunds) for the downtime. Leverage: Threaten RFP."
    },
    "5. Chemical Sole Source (Force Majeure)": {
        "context": "Production Chemicals",
        "brief": "Context: Your sole supplier of a critical demulsifier has declared Force Majeure due to a plant fire. They can only supply 50% volume at +40% price (spot market rates). Objective: Secure 80% volume allocation and cap price increase at 15% by offering a longer term extension."
    },
    "6. Professional Services Rate Card": {
        "context": "Consultancy / HR",
        "brief": "Context: A 'Big 4' consultancy wants to update their rate card for the next 2 years, proposing a 10% hike across all roles (Junior to Partner). Objective: Agree to <3% hike, but only for Senior roles. Freeze Junior rates."
    },
    "7. Maintenance (MRO) Bulk Deal": {
        "context": "MRO / Operations",
        "brief": "Context: You are consolidating 5 separate MRO workshops into one master contract. The incumbent vendor is lazy and assumes they will win. Objective: Demand a 15% volume discount rebate structure in exchange for exclusivity."
    },
    "8. Liability Cap Negotiation (Legal)": {
        "context": "Legal / Contract Terms",
        "brief": "Context: A new technology start-up (AI sensors) refuses your standard 'Unlimited Liability' clause for IP infringement and Data Privacy. They want a cap of $1M. Objective: Maintain unlimited liability for IP/Gross Negligence, but offer a $5M cap for general contract claims."
    },
    "9. Subsea Umbilicals Late Delivery": {
        "context": "Projects / Supply Chain",
        "brief": "Context: Critical subsea equipment is 4 weeks late, delaying First Oil. The vendor cites 'supply chain issues'. Contract allows for Liquidated Damages (LDs). Objective: Enforce LDs to cover your losses, or trade LDs for free installation support/engineers on site."
    },
    "10. Termination for Convenience": {
        "context": "Strategic / Corporate",
        "brief": "Context: Your company cancelled a warehouse project halfway through. You must negotiate the 'Termination Sum' with the builder. They are claiming for 'Lost Profit' on the unbuilt portion. Objective: Pay only for work done + reasonable demobilization. Reject 'Lost Profit' claims."
    }
}

# --- SCENARIO SELECTION ---
if not st.session_state.scenario_active:
    st.subheader("📍 Select Your Mission")
    
    tab1, tab2 = st.tabs(["📚 Standard Library", "✨ AI Architect (Custom)"])
    
    with tab1:
        selected_scenario = st.selectbox("Choose a pre-loaded scenario:", list(SCENARIOS.keys()))
        
        st.info(f"**Context:** {SCENARIOS[selected_scenario]['context']}")
        st.markdown(f"**Brief:** {SCENARIOS[selected_scenario]['brief']}")
        
        if st.button("🚀 Start Simulation", type="primary"):
            st.session_state.current_brief = SCENARIOS[selected_scenario]["brief"]
            st.session_state.messages = []
            st.session_state.scenario_active = True
            st.rerun()

    with tab2:
        st.markdown("Generate a unique training scenario tailored to your specific industry.")
        col_cust1, col_cust2 = st.columns(2)
        with col_cust1:
            custom_context = st.text_input("Industry / Context", placeholder="e.g. Chemicals, Logistics, Legal")
        with col_cust2:
            custom_topic = st.text_input("Negotiation Topic", placeholder="e.g. Liability Caps, Payment Terms")
            
        custom_detail = st.text_area("Specific Situation / Pressure:", placeholder="e.g. The supplier is the sole source, but we have a quality dispute...")
        
        if st.button("✨ Generate Custom Scenario"):
            if custom_detail:
                st.session_state.current_brief = f"Context: {custom_context}. Topic: {custom_topic}. Situation: {custom_detail}. Objective: Secure best commercial terms."
                st.session_state.messages = []
                st.session_state.scenario_active = True
                st.rerun()

# --- NEGOTIATION INTERFACE ---
if st.session_state.scenario_active:
    with st.expander("📄 Mission Brief (Reference)", expanded=False):
        st.info(st.session_state.current_brief)

    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    user_input = st.chat_input("Type your proposal or counter-offer...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Counterparty is analyzing your offer..."):
                try:
                    system_prompt = f"""
                    You are a tough, realistic negotiation counterparty. 
                    Scenario Brief: {st.session_state.current_brief}
                    Guidelines:
                    1. Do not give in easily. Push back on price and terms.
                    2. Use emotional leverage (urgency, frustration, silence) if appropriate.
                    3. Keep responses concise (under 3-4 sentences).
                    4. React to the user's tone. If they are weak, dominate. If they are aggressive, defend.
                    """
                    
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    chat_history = [{"role": "user", "parts": system_prompt}]
                    for m in st.session_state.messages:
                        role = "user" if m["role"] == "user" else "model"
                        chat_history.append({"role": role, "parts": m["content"]})
                    
                    response = model.generate_content(chat_history)
                    bot_reply = response.text
                    
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")

    st.markdown("---")
    if st.button("📊 End Session & Generate Scorecard", type="primary", use_container_width=True):
        with st.spinner("Compiling CPO Report..."):
            try:
                score_prompt = f"""
                Analyze this negotiation transcript based on the following brief: {st.session_state.current_brief}
                Transcript:
                {st.session_state.messages}
                Provide a structured report in Markdown:
                1. **Overall Score** (0/100)
                2. **Executive Summary** (2 sentences)
                3. **3 Key Strengths** (Bullet points)
                4. **3 Critical Weaknesses** (Bullet points)
                5. **Coaching Corner:** Rewrite the user's weakest line to be stronger.
                6. **Seniority Rating:** (Analyst / Manager / Director / CPO)
                """
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                analysis = model.generate_content(score_prompt)
                
                st.balloons()
                with st.expander("📈 Negotiation Scorecard & AAR", expanded=True):
                    st.markdown(analysis.text)
                    st.download_button("📥 Download Report (TXT)", analysis.text, file_name="negotiation_AAR.txt")
                    
            except Exception as e:
                st.error(f"Analysis Error: {e}")
