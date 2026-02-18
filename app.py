import streamlit as st

from sidebar import sidebar
from utils import md, load_css, extract_text_from_pdf, get_system_prompt, call_llm

st.set_page_config(
    page_title="Reviewer Zero",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

md('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">')
load_css("style.css")

# --- Session State ---
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Main UI Content ---

if __name__ == "__main__":
    # title / description
    md("""
    <div class='main-title'>『 Reviewer Zero 』</div>
    <div class='guide-box'>
    <div class='guide-title'><i class="fa-solid fa-circle-question"></i> About this Tool</div>
    <div class='guide-text'>
        「Reviewer Zero」は，LLMを使用し，論文査読とアイデア出しを加速させるAIツールです．<br><br>
        <i class="fa-solid fa-check icon"></i> <b>Instant Review:</b> PDFをアップロードするだけで，トップカンファレンス基準の査読レポートを生成します．<br>
        <i class="fa-solid fa-check icon"></i> <b>Idea Generation:</b> 論文の限界点を見抜き，次に取るべき具体的な研究テーマを提案します．<br>
        <i class="fa-solid fa-check icon"></i> <b>Interactive Chat:</b> 読み込んだ論文に対して，「この数式の意味は？」といった質問が可能です．<br>
    </div>
    </div>
    """)

    # sideebar
    api_key, selected_provider, selected_model, base_url, language = sidebar()

    # 3. API / upload
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

    # 4. result / chat
    if st.session_state.review_result:
        md("---")
        tab1, tab2 = st.tabs(["Review Report", "Chat / Discussion"])
        
        with tab1:
            md(f"<div class='result-card'>{st.session_state.review_result}</div>")
            
            st.download_button(
                label="Download Markdown",
                data=st.session_state.review_result,
                file_name="review.md",
                mime="text/markdown"
            )

        with tab2:
            st.subheader("Chat with Paper")
            
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    md(msg["content"])
            
            if prompt := st.chat_input("Ask a question about this paper..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    md(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        context = f"Paper Context: {st.session_state.paper_text[:20000]}...\nUser: {prompt}"
                        ans = call_llm(selected_provider, selected_model, api_key, "You are a helpful assistant.", context, url=base_url)
                        md(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})