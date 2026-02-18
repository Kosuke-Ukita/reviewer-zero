import streamlit
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
import anthropic
import fitz

def md(html):
    streamlit.markdown(html, unsafe_allow_html=True)

def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        md(f'<style>{f.read()}</style>')



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
            return "Rate Limit Reached. Please wait a moment or use your own API Key."
        return f"Error: {str(e)}"
