import os
import json
import base64
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from upstash_redis import Redis

# 1. Configurazione della pagina
st.set_page_config(
    page_title="Fixi",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Caricamento variabili d'ambiente
load_dotenv()

api_key = st.secrets.get("API_KEY") or os.getenv("API_KEY")
redis_url = st.secrets.get("UPSTASH_REDIS_REST_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
redis_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# Connessione Redis
redis = Redis(url=redis_url, token=redis_token) if (redis_url and redis_token) else None

# 3. Funzione per leggere i file locali e di GitHub
def load_github_knowledge():
    """Legge tutti i file di testo (.txt, .md, .csv, .json) presenti nel repository."""
    knowledge = ""
    allowed_extensions = ('.txt', '.md', '.csv', '.json')
    ignored_files = {'requirements.txt'}

    try:
        for file in os.listdir("."):
            if file.endswith(allowed_extensions) and file not in ignored_files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                        knowledge += f"\n--- CONTENUTO FILE '{file}' ---\n{content}\n"
                except Exception:
                    pass
    except Exception as e:
        print(f"Errore lettura file: {e}")
        
    return knowledge

# 4. Gestione della Memoria su Cloud
def load_chat_history():
    if redis:
        try:
            data = redis.get("fixi_chat_history")
            if data:
                return json.loads(data)
        except Exception:
            pass
            
    return []

def save_chat_history(messages):
    if redis:
        try:
            # Pulisce le immagini prima del salvataggio su Redis per ottimizzare lo spazio
            clean_messages = []
            for m in messages:
                if isinstance(m.get("content"), list):
                    text_parts = [p.get("text", "") for p in m["content"] if p.get("type") == "text"]
                    clean_messages.append({"role": m["role"], "content": f"[Foto inviata] {' '.join(text_parts)}"})
                else:
                    clean_messages.append(m)
            redis.set("fixi_chat_history", json.dumps(clean_messages, ensure_ascii=False))
        except Exception as e:
            st.error(f"Errore nel salvataggio della memoria cloud: {e}")

# Inizializza la memoria
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# 5. Stili CSS
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
        padding: 20px 20px 160px 20px !important; 
        max-width: 900px !important;
        margin: 0 auto !important;
    }

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
        0% { transform: rotate(0deg) scale(0.97); }
        100% { transform: rotate(360deg) scale(0.97); }
    }
    @keyframes waveMorph2 {
        0% { transform: rotate(0deg) scale(1.01); }
        100% { transform: rotate(-360deg) scale(1.01); }
    }
    @keyframes waveMorph3 {
        0% { transform: rotate(0deg) scale(0.98); }
        100% { transform: rotate(180deg) scale(1.03); }
    }
    .status-text { font-size: 11px; color: rgba(255, 255, 255, 0.6); }

    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px 15px;
        margin-bottom: 15px;
        z-index: 5;
    }

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

# Header
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

# Caricamento conoscenza dai file su GitHub
github_docs = load_github_knowledge()

system_prompt = {
    "role": "system",
    "content": f"Sei Fixi, un'intelligenza artificiale minimale con capacità visive. Rispondi in modo chiaro, diretto e amichevole in italiano.\n"
               f"Hai accesso ai seguenti file di conoscenza del tuo proprietario:\n{github_docs}"
}

# Mostra i messaggi della chat
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.write(message["content"])
            elif isinstance(message["content"], list):
                for part in message["content"]:
                    if part.get("type") == "text":
                        st.write(part["text"])
                    elif part.get("type") == "image_url":
                        st.image(part["image_url"]["url"], width=280)

# Sezione allegati: Foto o Documenti
col1, col2 = st.columns(2)
with col1:
    uploaded_image = st.file_uploader("📸 Invia una foto a Fixi", type=["jpg", "jpeg", "png", "webp"])
with col2:
    uploaded_file = st.file_uploader("📄 Allega un file di testo", type=["txt", "md", "csv", "json"])

uploaded_text_content = ""
if uploaded_file is not None:
    uploaded_text_content = uploaded_file.read().decode("utf-8")
    st.success(f"File '{uploaded_file.name}' pronto!")

if uploaded_image is not None:
    st.image(uploaded_image, caption="Foto selezionata", width=180)

# Input della Chat
prompt = st.chat_input("Scrivi un messaggio o chiedi qualcosa sulla foto...", accept_audio=True)

if prompt:
    user_text = prompt.text if hasattr(prompt, "text") else str(prompt)
    
    if uploaded_text_content:
        user_text += f"\n\n[FILE ALLEGATO - {uploaded_file.name}]:\n{uploaded_text_content}"
        
    model_to_use = "llama-3.3-70b-versatile"
    
    # Se è presente un'immagine, attiva la modalità Visiva
    if uploaded_image is not None:
        model_to_use = "llama-3.2-11b-vision-preview"
        bytes_data = uploaded_image.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        mime_type = uploaded_image.type
        
        user_message_content = [
            {"type": "text", "text": user_text if user_text else "Descrivi cosa vedi in questa immagine."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            }
        ]
        user_msg = {"role": "user", "content": user_message_content}
    else:
        user_msg = {"role": "user", "content": user_text}

    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if isinstance(user_msg["content"], list):
            st.write(user_text if user_text else "Descrivi cosa vedi in questa immagine.")
            st.image(uploaded_image, width=250)
        else:
            st.write(user_text)

    with st.spinner("Fixi sta analizzando la foto..."):
        full_messages = [system_prompt] + st.session_state.messages
        
        risposta = client.chat.completions.create(
            model=model_to_use,
            messages=full_messages
        )
        testo_risposta = risposta.choices[0].message.content
        
        st.session_state.messages.append({"role": "assistant", "content": testo_risposta})
        save_chat_history(st.session_state.messages)
        
        st.rerun()
