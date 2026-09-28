import streamlit as st
import os
import json
from google import genai

# ==========================================
# 🔑 1. CONTROLLO PASSWORD SEGRETA
# ==========================================
# Cambia "MAMMA123" con la password che vuoi tu!
PASSWORD_SEGRETA = "MOCCIA2026"

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.title("🔒 ACCESSO RISERVATO - MOCC_IA")
    pass_inserita = st.text_input("Inserisci la password segreta per accedere:", type="password")
    if st.button("Sblocca App"):
        if pass_inserita == PASSWORD_SEGRETA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Password errata! Riprova.")
    st.stop()  # Ferma l'app qui finché non mette la password giusta!

# ==========================================
# 2. CHIAVE API E CONFIGURAZIONE
# ==========================================
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6IWDCL_EFVyjE48i1A69svIGS6WMHNoQXrM6vl4bEvt_Q")
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="MOCC_IA ONLINE", page_icon="📚", layout="wide")

# Stile grafico
st.markdown("""
    <style>
    .stApp { background-color: #121212; font-family: 'Arial', sans-serif !important; }
    h1, h2, h3, label, p { font-family: 'Arial', sans-serif !important; text-transform: uppercase !important; }
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3 { background-color: rgba(0, 0, 0, 0.75) !important; color: white !important; padding: 4px 10px; border-radius: 6px; display: inline-block; }
    section[data-testid="stSidebar"] { background-color: rgba(18, 18, 18, 0.98) !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 MOCC_IA: ASSISTENTE SCRITTORE ONLINE")

# ==========================================
# 💾 MEMORIA VIRTUALIZZATA
# ==========================================
FILE_PERSONAGGI = "personaggi_memoria.json"

def carica_personaggi():
    if os.path.exists(FILE_PERSONAGGI):
        try:
            with open(FILE_PERSONAGGI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_personaggi(data):
    with open(FILE_PERSONAGGI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "personaggi" not in st.session_state:
    st.session_state["personaggi"] = carica_personaggi()

# ==========================================
# 🎭 BARRA LATERALE (PERSONAGGI & SALVATAGGIO)
# ==========================================
st.sidebar.header("🎭 GESTIONE PERSONAGGI")

with st.sidebar.expander("➕ AGGIUNGI PERSONAGGIO"):
    nome_p = st.text_input("NOME PERSONAGGIO:")
    desc_p = st.text_area("PROFILO E CARATTERE:")
    if st.button("💾 SALVA PERSONAGGIO"):
        if nome_p:
            st.session_state["personaggi"][nome_p] = {"profilo": desc_p, "ricordi": {}}
            salva_personaggi(st.session_state["personaggi"])
            st.success(f"{nome_p} SALVATO!")
            st.rerun()

st.sidebar.subheader("👥 PERSONAGGI MEMORIZZATI")
for nome, info in st.session_state["personaggi"].items():
    with st.sidebar.expander(f"👤 {nome}"):
        st.write(f"**PROFILO:** {info['profilo']}")

# Salva Scena
st.sidebar.divider()
st.sidebar.header("💾 SALVA LA SCENA")
cap_da_salvare = st.sidebar.number_input("NUMERO CAPITOLO:", min_value=1, value=1)
nuovo_fatto = st.sidebar.text_input("EVENTO DA RICORDARE IN FUTURO:")

if st.sidebar.button("📁 SALVA SCENA VIRTUALMENTE"):
    scena_da_salvare = st.session_state.get('scena_generata', '')
    if scena_da_salvare:
        cartella = "CAPITOLI_SCRITTI"
        if not os.path.exists(cartella):
            os.makedirs(cartella)
        with open(f"{cartella}/Capitolo_{cap_da_salvare}.txt", "a", encoding="utf-8") as f:
            f.write(f"\n\n--- CAPITOLO {cap_da_salvare} ---\n\n" + scena_da_salvare)
        
        if nuovo_fatto:
            for nome in st.session_state["personaggi"]:
                if nome.lower() in scena_da_salvare.lower():
                    st.session_state["personaggi"][nome]["ricordi"][str(cap_da_salvare)] = nuovo_fatto
            salva_personaggi(st.session_state["personaggi"])
        st.sidebar.success("SALVATO CON SUCCESSO! 🎉")

# ==========================================
# 📝 TAVOLO DA LAVORO
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 1. APPUNTI DELLA SCENA")
    capitolo_corrente = st.number_input("📌 CAPITOLO CORRENTE:", min_value=1, value=1)
    appunti = st.text_area("SCRIVI I TUOI APPUNTI:", height=250)
    
    if st.button("🚀 TRASFORMA IN SCENA CON MOCC_IA"):
        if appunti:
            with st.spinner("🤖 CREAZIONE SCENA IN CORSO..."):
                try:
                    info_p = ""
                    for nome, data in st.session_state["personaggi"].items():
                        if nome.lower() in appunti.lower():
                            info_p += f"\nPROFILO {nome}: {data['profilo']}\n"
                    
                    prompt = f"Sei MOCC_IA. Scrivi una scena per il Capitolo {capitolo_corrente}.\n{info_p}\nAppunti: {appunti}"
                    response = client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
                    st.session_state['scena_generata'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")

with col2:
    st.subheader("📖 2. LA SCENA GENERATA")
    st.text_area("TESTO FINALE:", value=st.session_state.get('scena_generata', ''), height=320)
    