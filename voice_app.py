import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# 1. Configurazione della pagina
st.set_page_config(
    page_title="Fixi",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Definizione del percorso ASSOLUTO per il file della cronologia
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "chat_history.json")

# 3. Caricamento API Key
load_dotenv()
api_key = os.getenv("API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# 4. Funzioni per salvataggio e caricamento permanente
def save_chat_history(messages):
    """Salva la cronologia corrente nel file JSON."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")

def load_chat_history():
    """Carica i messaggi salvati su file o ne crea uno nuovo subito."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
            
    # Se il file non esiste o è corrotto, creiamo la struttura iniziale e IL FILE SUBITO
    initial_messages = [
        {
            "role": "system",
            "content": "Sei Fixi, un'intelligenza artificiale minimale. Rispondi in modo chiaro, diretto e amichevole in italiano."
        }
    ]
    save_chat_history(initial_messages)
    return initial_messages

# Inizializza la memoria caricando i dati salvati su disco
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# 5. Layout e Stili CSS
st.markdown("""
<style>
    * { box-sizing: border-box; }
    #MainMenu, header, footer, .stDeployButton { display: none !important; }
    
    div[data-testid="stAppViewContainer"], div[data-testid="stMain"] {
        background-color: #0d0f14 !important;
    }

    body { 
        margin: 0; padding: 0; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
        background-color: #0d0f14; color: #e0e0e0; 
    }

    .block-container {
        padding: 20px 20px 140px 20px !important; 
        max-width: 900px !important;
        margin: 0 auto !important;
    }

    /* SFONDO GLOW */
    .glow-purple {
        position: fixed; bottom: -10%; left: -5%; width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(70, 45, 140, 0.2) 0%, rgba(13, 15, 20, 0) 70%);
        pointer-events: none; z-index: 1;
    }
    .glow-cyan {
        position: fixed; top: -10%; right: -5%; width: 550px; height: 550px;
        background: radial-gradient(circle, rgba(30, 90, 140, 0.15) 0%, rgba(13, 15, 20, 0) 70%);
        pointer-events: none; z-index: 1;
    }

    /* HEADER */
    .header-section {
        display: flex; flex-direction: column; align-items: center; margin-bottom: 25px; z-index: 5;
    }
    .waveform-container {
        position: relative; width: 75px; height: 75px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
    }
    .wave-ring-1 {
        position: absolute; width: 100%; height: 100%;
        border-radius: 42% 58% 60% 40% / 45% 55% 45% 55%;
        border: 2px solid #38bdf8;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.6), inset 0 0 6px rgba(56, 189, 248, 0.2);
        animation: waveMorph1 6s ease-in-out infinite alternate;
    }
    .wave-ring-2 {
        position: absolute; width: 95%; height: 95%;
        border-radius: 55% 45% 38% 62% / 50% 42% 58% 50%;
        border: 2px solid #c084fc;
        box-shadow: 0 0 10px rgba(192, 132, 252, 0.6), inset 0 0 6px rgba(192, 132, 252, 0.2);
        animation: waveMorph2 7s ease-in-out infinite alternate;
    }
    .wave-ring-3 {
        position: absolute; width: 90%; height: 90%;
        border-radius: 48% 52% 55% 45% / 60% 40% 60% 40%;
        border: 2px solid #818cf8;
        box-shadow: 0 0 8px rgba(129, 140, 248, 0.4);
        animation: waveMorph3 5s ease-in-out infinite alternate;
    }

    @keyframes waveMorph1 {
        0% { transform: rotate(0deg) scale(0.97); border-radius: 42% 58% 60% 40% / 45% 55% 45% 55%; }
        50% { transform: rotate(180deg) scale(1.02); border-radius: 58% 42% 40% 60% / 55% 45% 55% 45%; }
        100% { transform: rotate(360deg) scale(0.97); border-radius: 42% 58% 60% 40% / 45% 55% 45% 55%; }
    }
    @keyframes waveMorph2 {
        0% { transform: rotate(0deg) scale(1.01); border-radius: 55% 45% 38% 62% / 50% 42% 58% 50%; }
        50% { transform: rotate(-180deg) scale(0.96); border-radius: 40% 60% 55% 45% / 45% 55% 42% 58%; }
        100% { transform: rotate(-360deg) scale(1.01); border-radius: 55% 45% 38% 62% / 50% 42% 58% 50%; }
    }
    @keyframes waveMorph3 {
        0% { transform: rotate(0deg) scale(0.98); }
        100% { transform: rotate(180deg) scale(1.03); }
    }
    .status-text { font-size: 11px; color: rgba(255, 255, 255, 0.6); }

    /* MESSAGGI */
    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px 15px;
        margin-bottom: 15px;
        z-index: 5;
    }

    /* INPUT CHAT FISSO IN BASSO */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 25px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 40px) !important;
        max-width: 900px !important;
        z-index: 100 !important;
        background: transparent !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: rgba(13, 15, 20, 0.95) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 -10px 25px rgba(13, 15, 20, 0.9) !important;
    }
</style>

<div class="glow-purple"></div>
<div class="glow-cyan"></div>
""", unsafe_allow_html=True)

# Header (Animazione e Status)
st.markdown("""
<div class="header-section">
    <div class="waveform-container">
        <div class="wave-ring-1"></div>
        <div class="wave-ring-2"></div>
        <div class="wave-ring-3"></div>
    </div>
    <div class="status-text">Fixi ti sta ascoltando...</div>
</div>
""", unsafe_allow_html=True)

# Mostra tutti i messaggi caricati dal file
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Auto-scroll verso il basso
st.markdown("""
<div id="chat-end"></div>
<script>
    function forceScrollBottom() {
        var endElement = document.getElementById("chat-end");
        if (endElement) {
            endElement.scrollIntoView({ behavior: "smooth", block: "end" });
        }
        var mainContainer = window.parent.document.querySelector('.main');
        if (mainContainer) {
            mainContainer.scrollTop = mainContainer.scrollHeight;
        }
    }
    setTimeout(forceScrollBottom, 150);
</script>
""", unsafe_allow_html=True)

# Input Chat
prompt = st.chat_input("Scrivi un messaggio o parla...", accept_audio=True)

# Logica di risposta dell'IA
if prompt:
    user_text = prompt.text if hasattr(prompt, "text") else str(prompt)
    if user_text:
        # Aggiunge e salva subito il messaggio dell'utente
        st.session_state.messages.append({"role": "user", "content": user_text})
        save_chat_history(st.session_state.messages)
        
        with st.chat_message("user"):
            st.write(user_text)
            
        with st.spinner("Fixi sta elaborando..."):
            risposta = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            testo_risposta = risposta.choices[0].message.content
            
            # Aggiunge e salva subito la risposta dell'IA
            st.session_state.messages.append({"role": "assistant", "content": testo_risposta})
            save_chat_history(st.session_state.messages)
            
            st.rerun()