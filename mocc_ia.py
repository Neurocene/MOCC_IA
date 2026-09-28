import streamlit as st
import os
import json
from google import genai
from audio_recorder_streamlit import audio_recorder

# ==========================================
# 🔑 1. CONTROLLO PASSWORD SEGRETA
# ==========================================
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
    st.stop()

# ==========================================
# 2. CHIAVE API E CONFIGURAZIONE
# ==========================================
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6IWDCL_EFVyjE48i1A69svIGS6WMHNoQXrM6vl4bEvt_Q")
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="MOCC_IA ONLINE", page_icon="📚", layout="wide")

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
# 💾 MEMORIA PERSONAGGI PER CAPITOLI
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
# 🎭 BARRA LATERALE SINISTRA
# ==========================================
st.sidebar.header("🎭 GESTIONE PERSONAGGI")

with st.sidebar.expander("➕ AGGIUNGI PERSONAGGIO"):
    nome_p = st.text_input("NOME PERSONAGGIO:")
    desc_p = st.text_area("PROFILO E CARATTERE:")
    if st.button("💾 SALVA PERSONAGGIO"):
        if nome_p:
            if nome_p not in st.session_state["personaggi"]:
                st.session_state["personaggi"][nome_p] = {"profilo": desc_p, "ricordi": {}}
            else:
                st.session_state["personaggi"][nome_p]["profilo"] = desc_p
            salva_personaggi(st.session_state["personaggi"])
            st.success(f"{nome_p} SALVATO!")
            st.rerun()

st.sidebar.subheader("👥 SCHEDE PERSONAGGI")
for nome, info in st.session_state["personaggi"].items():
    with st.sidebar.expander(f"👤 {nome}"):
        st.write(f"**PROFILO:** {info['profilo']}")
        st.write("**🧠 RICORDI PER CAPITOLO:**")
        ricordi_diz = info.get("ricordi", {})
        if ricordi_diz:
            for cap_num in sorted([int(k) for k in ricordi_diz.keys()]):
                st.markdown(f"📖 **CAPITOLO {cap_num}:** {ricordi_diz[str(cap_num)]}")
        else:
            st.caption("NESSUN RICORDO ANCORA REGISTRATO.")

# Salva Scena
st.sidebar.divider()
st.sidebar.header("💾 SALVA LA SCENA")
cap_da_salvare = st.sidebar.number_input("NUMERO CAPITOLO DA SALVARE:", min_value=1, value=1, step=1)
nuovo_fatto = st.sidebar.text_input("EVENTO DA RICORDARE PER IL FUTURO:")

if st.sidebar.button("📁 SALVA SCENA"):
    scena_da_salvare = st.session_state.get('scena_generata', '')
    if scena_da_salvare:
        cartella = "CAPITOLI_SCRITTI"
        if not os.path.exists(cartella):
            os.makedirs(cartella)
        with open(f"{cartella}/Capitolo_{cap_da_salvare}.txt", "a", encoding="utf-8") as f:
            f.write(f"\n\n--- CAPITOLO {cap_da_salvare} ---\n\n" + scena_da_salvare + "\n\n------------------------\n")
        
        if nuovo_fatto:
            for nome in st.session_state["personaggi"]:
                if nome.lower() in scena_da_salvare.lower() or nome.lower() in st.session_state.get('appunti_temp', '').lower():
                    st.session_state["personaggi"][nome]["ricordi"][str(cap_da_salvare)] = nuovo_fatto
            salva_personaggi(st.session_state["personaggi"])
        st.sidebar.success("SALVATO CON SUCCESSO! 🎉")
    else:
        st.sidebar.error("NESSUNA SCENA DA SALVARE!")

# ==========================================
# 📝 TAVOLO DA LAVORO
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 1. APPUNTI DELLA SCENA")
    capitolo_corrente = st.number_input("📌 CAPITOLO CORRENTE:", min_value=1, value=1, step=1)
    
    # --- REGISTRATORE VOCALE MAGICO ---
    st.write("🎙️ **REGISTRA UN VOCALE PER I TUOI APPUNTI:**")
    audio_bytes = audio_recorder(text="Clicca sul microfono per registrare", icon_size="2x")
    
    if audio_bytes:
        with st.spinner("🎧 Sto ascoltando il tuo vocale e lo trasformo in testo..."):
            try:
                # Mandiamo l'audio direttamente a Gemini!
                response_audio = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[
                        "Trascrivi fedelmente questo file audio in testo italiano senza aggiungere commenti:",
                        genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
                    ]
                )
                testo_trascritto = response_audio.text
                if 'appunti_voce' not in st.session_state or st.session_state['appunti_voce'] != testo_trascritto:
                    st.session_state['appunti_voce'] = testo_trascritto
                    st.success("Vocale trascritto con successo! ✨")
            except Exception as e:
                st.error(f"Errore trascrizione vocale: {e}")

    # Casella di testo dove va a finire sia la scrittura a mano che quella vocale
    valore_iniziale = st.session_state.get('appunti_voce', '')
    appunti = st.text_area("SCRIVI O MODIFICA I TUOI APPUNTI:", value=valore_iniziale, height=200, placeholder="Es: Marco incontra Elena al bar...")
    st.session_state['appunti_temp'] = appunti
    
    if st.button("🚀 TRASFORMA IN SCENA CON MOCC_IA"):
        if appunti:
            with st.spinner("🤖 CREAZIONE SCENA IN CORSO..."):
                try:
                    info_p = ""
                    for nome, data in st.session_state["personaggi"].items():
                        if nome.lower() in appunti.lower():
                            info_p += f"\n--- PROFILO {nome.upper()} ---\n"
                            info_p += f"PROFILO: {data['profilo']}\n"
                            ricordi_passati = []
                            for cap_num_str, testo_ricordo in data.get("ricordi", {}).items():
                                if int(cap_num_str) < capitolo_corrente:
                                    ricordi_passati.append(f"NEL CAPITOLO {cap_num_str}: {testo_ricordo}")
                            if ricordi_passati:
                                info_p += "RICORDI PASSATI:\n" + "\n".join(ricordi_passati) + "\n"
                    
                    prompt = f"Sei MOCC_IA, uno scrittore professionista.\nStai scrivendo per il Capitolo {capitolo_corrente}.\n{info_p}\nAppunti: {appunti}\nScrivi direttamente la scena in italiano."
                    response = client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
                    st.session_state['scena_generata'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
        else:
            st.warning("SCRIVI PRIMA GLI APPUNTI O REGISTRA UN VOCALE!")

with col2:
    st.subheader("📖 2. LA SCENA GENERATA")
    scena_finale = st.text_area("TESTO FINALE DA MODIFICARE:", value=st.session_state.get('scena_generata', ''), height=320)
    st.session_state['scena_generata'] = scena_finale
