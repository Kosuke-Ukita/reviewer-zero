import streamlit as st
from utils import md


def sidebar():
    with st.sidebar:
        md("### <i class='fa-solid fa-gear'></i> Settings")
        
        # Demo Mode
        use_demo = st.toggle("Demo Mode (Free)", value=False)
        
        api_key = None
        base_url = None
        selected_provider = None
        selected_model = None

        if use_demo:
            md("""
            <div style='font-size:0.8rem; color:#888; margin-bottom:1rem;'>
            <i class="fa-solid fa-circle-info"></i> 管理者のキーで試用 (制限あり)
            </div>
            """)
            
            selected_provider = st.selectbox("Demo Provider", ["Google Gemini-2.5-flash-lite"])
            
            if selected_provider == "Google Gemini-2.5-flash-lite":
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = st.secrets["GEMINI_API_KEY"]
                    selected_model = "gemini-2.5-flash-lite"
                else:
                    st.error("Secret key not configured.")
            
        else:
            # User API Key Mode
            md("<div style='font-size:0.8rem; color:#888;'>自分のAPIキーを使用します</div>")
            
            provider_options = ["Google Gemini", "OpenAI GPTs", "Anthropic Claude", "Groq"]
            selected_provider = st.selectbox("Provider", provider_options)

            if "Gemini" in selected_provider:
                api_key = st.text_input("API Key", type="password", placeholder="AIza...")
                if api_key: selected_model = st.selectbox("Model", ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.0-flash", "gemini-3.0-pro"])
                
            elif "OpenAI" in selected_provider:
                api_key = st.text_input("API Key", type="password", placeholder="sk-...")
                if api_key: selected_model = st.selectbox("Model", ["gpt-4", "gpt-4o-mini", "gpt-4o", "o1-mini", "o1", "o1-pro", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1", "o3-mini", "o3", "o3-pro", "o4-mini", "gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5-pro", "gpt-5.1", "gpt-5.2", "gpt-5.2-pro"])
                
            elif "Anthropic" in selected_provider:
                api_key = st.text_input("API Key", type="password", placeholder="sk-ant...")
                dict_models = {
                    "claude-haiku-4.5": "claude-haiku-4-5",
                    "claude-sonnet-4": "claude-sonnet-4",
                    "claude-sonnet-4.5": "claude-sonnet-4-5",
                    "claude-sonnet-4.6": "claude-sonnet-4-6",
                    "claude-opus-4": "claude-opus-4",
                    "claude-opus-4.1": "claude-opus-4-1",
                    "claude-opus-4.5": "claude-opus-4-5",
                    "claude-opus-4.6": "claude-opus-4-6"
                }
                if api_key: selected_model = dict_models[st.selectbox("Model", ["claude-haiku-4.5", "claude-sonnet-4", "claude-sonnet-4.5", "claude-sonnet-4.6", "claude-opus-4", "claude-opus-4.1", "claude-opus-4.5", "claude-opus-4.6"])]
                
            elif "Groq" in selected_provider:
                api_key = st.text_input("API Key", type="password", placeholder="gsk_...")
                dict_models = {
                    "gpt-oss-20b": "openai/gpt-oss-20b",
                    "gpt-oss-120b": "openai/gpt-oss-120b",
                    "llama-3.1-8b": "llama-3.1-8b-instant",
                    "llama-3.3-70b": "llama-3.3-70b-versatile",
                    "qwen3-32b": "qwen/qwen3-32b",
                    "kimi-k2": "moonshotai/kimi-k2-instruct-0905",
                    "llama-4-scout-17b": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "llama-4-maverick-17b": "meta-llama/llama-4-maverick-17b-128e-instruct",
                    "canopylabs/orpheus-v1": "canopylabs/orpheus-v1-english"
                }
                if api_key: selected_model = dict_models[st.selectbox("Model", ["gpt-oss-20b", "gpt-oss-120b", "llama-3.1-8b", "llama-3.3-70b", "qwen3-32b", "kimi-k2", "llama-4-scout-17b", "llama-4-maverick-17b", "canopylabs/orpheus-v1"])]
                
            elif "Local" in selected_provider:
                base_url = st.text_input("Base URL", value="http://localhost:11434/v1")
                selected_model = st.text_input("Model Name", value="llama3")
                api_key = "ollama"

        st.divider()
        language = st.selectbox("Language", ["Japanese", "English"])
        
        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()
    return api_key, selected_provider, selected_model, base_url, language