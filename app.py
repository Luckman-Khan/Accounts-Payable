import streamlit as st
import os
from pypdf import PdfReader
from dotenv import load_dotenv  # <--- NEW IMPORT
from agent import app as agent_app

# --- 1. LOAD ENVIRONMENT VARIABLES ---
load_dotenv()  # This reads your .env file immediately
api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Senitac AI Agent", page_icon="🤖", layout="wide")

# --- SIDEBAR (Updated) ---
st.sidebar.title("🔧 Agent Controls")

# check if key is loaded
if api_key:
    st.sidebar.success("✅ API Key Loaded from .env")
else:
    st.sidebar.error("⚠️ No API Key found!")
    # Allow manual override if .env fails
    api_key = st.sidebar.text_input("Enter Gemini API Key manually", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key

# --- MAIN UI ---
st.title("🤖 AI Accounts Payable Employee")
st.markdown("### Upload an Invoice to begin the 3-Way Match")

# 1. FILE UPLOADER
uploaded_file = st.file_uploader("Drop your PDF Invoice here", type=["pdf"])

if uploaded_file:
    # --- STEP 1: READ THE FILE (The Eyes) ---
    with st.spinner("👀 Reading PDF..."):
        with open("temp_invoice.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        reader = PdfReader("temp_invoice.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
            
        st.success("PDF Read Successfully!")
        with st.expander("See Raw Text"):
            st.text(text)

    # --- STEP 2: RUN THE AGENT (The Brain) ---
    if st.button("🚀 Process Invoice"):
        if not api_key:
            st.error("❌ Critical Error: No API Key provided. Agent cannot work.")
        else:
            with st.spinner("🤖 Agent is thinking... (Checking Database & Rules)"):
                # Invoke LangGraph
                final_state = agent_app.invoke({"invoice_text": text})
                decision = final_state["final_decision"]
                data = final_state["extracted_data"]
                validation = final_state["validation_result"]

                # --- STEP 3: DISPLAY RESULTS ---
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📄 Extracted Data")
                    if data:
                        st.json(data.model_dump())
                    else:
                        st.error("Could not extract data.")

                with col2:
                    st.subheader("⚖️ Final Decision")
                    if decision == "PAY":
                        st.balloons()
                        st.success(f"## ✅ APPROVED")
                        st.write("Invoice matched PO and Vendor rules.")
                    elif decision == "DENY":
                        st.error(f"## ❌ REJECTED")
                        if validation:
                            for error in validation.errors:
                                st.write(f"- {error}")
                    else:
                        st.warning("## ⚠️ HUMAN REVIEW NEEDED")

                st.divider()
                st.subheader("📜 Agent Audit Log")
                st.write(f"Processed via LangGraph Node: {list(final_state.keys())}")