import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
import anthropic
import fitz  # PyMuPDF
import os

# --- ページ設定 (必ずファイルの先頭に) ---
st.set_page_config(
    page_title="Reviewer Zero",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
#  🎨 Dark Modern CSS Injection
# ==========================================
def inject_custom_css():
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

        <style>
        /* --- 変数定義 (ここを変えるだけでアクセントカラー変更可能) --- */
        :root {
            --bg-color: #0e0e0e;        /* 全体の背景色 (ほぼ黒) */
            --card-bg: #1a1a1a;         /* カードの背景色 */
            --text-main: #ffffff;       /* メインテキスト */
            --text-sub: #b0b0b0;        /* サブテキスト */
            --accent-color: #ff8c00;    /* ★アクセントカラー (オレンジ) */
            --accent-glow: rgba(255, 140, 0, 0.4); /* アクセントの光彩 */
            --shadow-white: rgba(255, 255, 255, 0.08); /* 白い影 */
        }

        /* --- 1. 全体設定 --- */
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-main);
        }
        
        /* --- 2. タイトルとヘッダー --- */
        .main-title {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-weight: 700;
            font-size: 3rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #ffffff, #888888);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* 使い方ガイドボックス */
        .guide-box {
            background-color: var(--card-bg);
            border-left: 4px solid var(--accent-color);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px var(--shadow-white);
        }
        .guide-text {
            color: var(--text-sub);
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .guide-title {
            color: var(--text-main);
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 0.5rem;
        }

        /* --- 3. サイドバー --- */
        section[data-testid="stSidebar"] {
            background-color: #050505; /* サイドバーはさらに暗く */
            border-right: 1px solid #333;
        }
        
        /* --- 4. ボタン (オレンジアクセント) --- */
        .stButton > button {
            background-color: transparent;
            color: var(--accent-color);
            border: 1px solid var(--accent-color);
            border-radius: 6px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .stButton > button:hover {
            background-color: var(--accent-color);
            color: #000; /* ホバー時は黒文字 */
            box-shadow: 0 0 15px var(--accent-glow);
            border-color: var(--accent-color);
        }
        .stButton > button:active {
            transform: scale(0.98);
        }

        /* --- 5. インプットフィールド & アップローダー --- */
        [data-testid="stFileUploader"] {
            background-color: var(--card-bg);
            border: 1px dashed #444;
            border-radius: 10px;
            padding: 20px;
            transition: border 0.3s;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent-color);
        }
        .stTextInput > div > div > input {
            background-color: #222;
            color: white;
            border: 1px solid #444;
        }
        .stSelectbox > div > div {
            background-color: #222;
            color: white;
        }

        /* --- 6. 結果表示エリア (カード風) --- */
        .result-card {
            background-color: var(--card-bg);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 2rem;
            margin-top: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 0 1px var(--shadow-white);
        }
        
        /* Markdownの見出し */
        .result-card h1, .result-card h2, .result-card h3 {
            color: var(--text-main);
            border-bottom: 1px solid #333;
            padding-bottom: 0.5rem;
            margin-top: 1.5rem;
        }
        .result-card strong {
            color: var(--accent-color);
        }

        /* --- 7. チャットメッセージ --- */
        .stChatMessage {
            background-color: var(--card-bg) !important;
            border: 1px solid #333;
            border-radius: 10px;
        }
        [data-testid="chatAvatarIcon-user"] {
            background-color: var(--accent-color) !important;
        }
        [data-testid="chatAvatarIcon-assistant"] {
            background-color: #444 !important;
        }

        /* --- 8. FontAwesomeアイコンの調整 --- */
        .icon {
            margin-right: 8px;
            width: 20px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

inject_custom_css()

# ==========================================
#  ロジック開始
# ==========================================

# --- Session State ---
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- サイドバー (Settings) ---
with st.sidebar:
    st.markdown("### <i class='fa-solid fa-gear'></i> Settings", unsafe_allow_html=True)
    
    # Demo Mode
    use_demo = st.toggle("Demo Mode (Free)", value=False)
    
    api_key = None
    base_url = None
    selected_provider = None
    selected_model = None

    if use_demo:
        st.markdown("""
        <div style='font-size:0.8rem; color:#888; margin-bottom:1rem;'>
        <i class="fa-solid fa-circle-info"></i> 管理者のキーで試用 (制限あり)
        </div>
        """, unsafe_allow_html=True)
        
        selected_provider = st.selectbox("Demo Provider", ["Google Gemini-2.5-flash-lite"])
        
        if selected_provider == "Google Gemini-2.5-flash-lite":
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                selected_model = "gemini-2.5-flash-lite"
            else:
                st.error("Secret key not configured.")
        
    else:
        # User API Key Mode
        st.markdown("<div style='font-size:0.8rem; color:#888;'>自分のAPIキーを使用します</div>", unsafe_allow_html=True)
        
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


# --- LLM Functions ---
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_system_prompt(lang):
    lang_instruction = f"Output language: **{lang}**."
    if "Japanese" in lang:
        lang_instruction += "\nIMPORTANT: Use full-width punctuation (，．) strictly."
    
    return f"""
    You are a Senior Area Chair at a top AI conference (NeurIPS/ICLR).
    {lang_instruction}
    Review the paper strictly. 
    Format in Markdown. 
    Required Sections:
    1. Summary (What problem? What contribution?)
    2. Strengths (Bullet points)
    3. Weaknesses (Bullet points)
    4. Future Directions (Propose 3 specific research topics).
    5. Novel Project Ideas.
    """

def call_llm(provider, model, key, sys_prompt, user_text, url=None):
    try:
        # Google
        if "Gemini" in provider:
            genai.configure(api_key=key)
            m = genai.GenerativeModel(model)
            response = m.generate_content(sys_prompt + "\n\nPaper:\n" + user_text)
            return response.text
        # OpenAI
        elif "OpenAI" in provider:
            client = OpenAI(api_key=key)
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":user_text}])
            return res.choices[0].message.content
        # Anthropic
        elif "Anthropic" in provider:
            client = anthropic.Anthropic(api_key=key)
            res = client.messages.create(model=model, max_tokens=4000, system=sys_prompt, messages=[{"role":"user","content":user_text}])
            return res.content[0].text
        # Groq
        elif "Groq" in provider:
            client = Groq(api_key=key)
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":user_text}])
            return res.choices[0].message.content
        # Local
        elif "Local" in provider:
            client = OpenAI(base_url=url, api_key="ollama")
            res = client.chat.completions.create(model=model, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":user_text}])
            return res.choices[0].message.content
            
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err or "rate limit" in err:
            return "⚠️ **Rate Limit Reached.** Please wait a moment or use your own API Key."
        return f"❌ Error: {str(e)}"

# --- Main UI Content ---

# 1. タイトル
st.markdown("<div class='main-title'>『 Reviewer Zero 』</div>", unsafe_allow_html=True)

# 2. 使い方ガイド (Description)
st.markdown("""
<div class='guide-box'>
    <div class='guide-title'><i class="fa-solid fa-circle-question"></i> About this Tool</div>
    <div class='guide-text'>
        「Reviewer Zero」は，LLMを使用し，論文査読とアイデア出しを加速させるAIツールです．<br>
        <br>
        <i class="fa-solid fa-check icon"></i> <b>Instant Review:</b> PDFをアップロードするだけで，トップカンファレンス基準の査読レポートを生成します．<br>
        <i class="fa-solid fa-check icon"></i> <b>Idea Generation:</b> 論文の限界点を見抜き，次に取るべき具体的な研究テーマを提案します．<br>
        <i class="fa-solid fa-check icon"></i> <b>Interactive Chat:</b> 読み込んだ論文に対して，「この数式の意味は？」といった質問が可能です．<br>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. APIキー確認 & アップロード
if not api_key:
    st.warning("← 左側のサイドバーで『Demo Mode』をオンにするか，APIキーを入力してください．")
    st.stop()

uploaded_file = st.file_uploader("Upload Paper PDF", type="pdf")

if uploaded_file:
    # Uploaded but not reviewed yet
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Start Review"):
            with st.spinner("Analyzing..."):
                text = extract_text_from_pdf(uploaded_file)
                st.session_state.paper_text = text
                
                sys_prompt = get_system_prompt(language)
                res = call_llm(selected_provider, selected_model, api_key, sys_prompt, text, url=base_url)
                
                st.session_state.review_result = res
                st.rerun()

# 4. 結果表示 & チャット
if st.session_state.review_result:
    st.markdown("---")
    
    # タブ選択
    tab1, tab2 = st.tabs(["Review Report", "Chat / Discussion"])
    
    with tab1:
        # 結果をカード風のコンテナに表示
        st.markdown(f"""
        <div class='result-card'>
            {st.session_state.review_result}
        </div>
        """, unsafe_allow_html=True)
        
        st.download_button(
            label="Download Markdown",
            data=st.session_state.review_result,
            file_name="review.md",
            mime="text/markdown"
        )

    with tab2:
        st.subheader("Chat with Paper")
        
        # 履歴表示
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # 入力フォーム
        if prompt := st.chat_input("Ask a question about this paper..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    context = f"Paper Context: {st.session_state.paper_text[:20000]}...\nUser: {prompt}"
                    ans = call_llm(selected_provider, selected_model, api_key, "You are a helpful assistant.", context, url=base_url)
                    st.markdown(ans)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})