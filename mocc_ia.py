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

st.set_page_config(page_title="MOCC_IA", page_icon="📚", layout="wide")

# Stile grafico con evidenziatore giallo e font Arial
st.markdown("""
    <style>
    .stApp { background-color: #121212; font-family: 'Arial', sans-serif !important; }
    h1, h2, h3, label, p, span { font-family: 'Arial', sans-serif !important; text-transform: uppercase !important; }
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3 { background-color: rgba(0, 0, 0, 0.85) !important; color: white !important; padding: 4px 10px; border-radius: 6px; display: inline-block; }
    section[data-testid="stSidebar"] { background-color: rgba(18, 18, 18, 0.98) !important; }
    
    /* Evidenziatore giallo per scene memorizzate */
    .scena-evidenziata {
        background-color: #f1c40f !important;
        color: #000000 !important;
        padding: 8px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Nuovo Titolo Pulito
st.title("🎬 MOCC_IA")

# ==========================================
# 💾 MEMORIA PERSONAGGI E SCENE
# ==========================================
FILE_PERSONAGGI = "personaggi_memoria.json"
FILE_SCENE = "scene_salvate.json"

def carica_dati(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_dati(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "personaggi" not in st.session_state:
    st.session_state["personaggi"] = carica_dati(FILE_PERSONAGGI)

if "scene_salvate" not in st.session_state:
    st.session_state["scene_salvate"] = carica_dati(FILE_SCENE)

# ==========================================
# 🎭 BARRA LATERALE (LUCE, PERSONAGGI & SALVATAGGI)
# ==========================================

# --- 💡 CHAT CON LUCE (L'EDITOR NARRATIVO) ---
st.sidebar.header("💡 LUCE - EDITOR NARRATIVO")
with st.sidebar.expander("💬 CHATTA CON LUCE"):
    st.write("Ciao Luigi! Sono **Luce**. Chiedimi consigli sui dialoghi o sulla struttura della storia!")
    domanda_luce = st.text_input("Fai una domanda a Luce:", placeholder="Es: Come posso rendere questo dialogo più emozionante?")
    if st.button("Chiedi a Luce"):
        if domanda_luce:
            with st.spinner("Luce sta pensando..."):
                try:
                    prompt_luce = f"Sei Luce, un'esperta editor narrativa e docente di scrittura creativa. Rispondi in modo incoraggiante, chiaro ed efficace fornendo consigli pratici sul seguente dubbio dello scrittore: {domanda_luce}"
                    resp_luce = client.models.generate_content(model='gemini-3.8-flash', contents=prompt_luce)
                    st.info(f"**Luce:** {resp_luce.text}")
                except Exception as e:
                    st.error(f"Errore: {e}")

st.sidebar.divider()

# --- 🎭 GESTIONE PERSONAGGI ---
st.sidebar.header("🎭 GESTIONE PERSONAGGI")

with st.sidebar.expander("➕ AGGIUNGI / MODIFICA PERSONAGGIO"):
    nome_p = st.text_input("NOME PERSONAGGIO:")
    desc_p = st.text_area("PROFILO E CARATTERE:")
    
    # Upload file per il personaggio
    file_p = st.file_uploader("📂 Carica file .txt per il profilo:", type=["txt"], key="file_p_up")
    if file_p is not None:
        desc_p += "\n" + file_p.read().decode("utf-8", errors="ignore")
        st.success("File caricato e aggiunto al profilo!")

    if st.button("💾 SALVA PERSONAGGIO"):
        if nome_p:
            if nome_p not in st.session_state["personaggi"]:
                st.session_state["personaggi"][nome_p] = {"profilo": desc_p, "ricordi": {}}
            else:
                st.session_state["personaggi"][nome_p]["profilo"] = desc_p
            salva_dati(FILE_PERSONAGGI, st.session_state["personaggi"])
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

# --- 💾 SALVA SCENA E LISTA SCENE ---
st.sidebar.divider()
st.sidebar.header("💾 SALVA LA SCENA")

titolo_scena = st.sidebar.text_input("TITOLO DELLA SCENA:", placeholder="Es: Il primo incontro a Ponte Milvio")
cap_da_salvare = st.sidebar.number_input("NUMERO CAPITOLO:", min_value=1, value=1, step=1)
nuovo_fatto = st.sidebar.text_input("EVENTO DA RICORDARE (PER IL PERSONAGGIO):")

if st.sidebar.button("📁 SALVA SCENA"):
    scena_da_salvare = st.session_state.get('scena_generata', '')
    if scena_da_salvare and titolo_scena:
        
        # Determiniamo se la scena entra nella memoria del personaggio
        in_memoria = False
        if nuovo_fatto:
            in_memoria = True
            for nome in st.session_state["personaggi"]:
                if nome.lower() in scena_da_salvare.lower() or nome.lower() in st.session_state.get('appunti_temp', '').lower():
                    st.session_state["personaggi"][nome]["ricordi"][str(cap_da_salvare)] = f"[{titolo_scena}] {nuovo_fatto}"
            salva_dati(FILE_PERSONAGGI, st.session_state["personaggi"])
        
        # Salviamo la scena nella lista complessiva
        st.session_state["scene_salvate"][titolo_scena] = {
            "capitolo": cap_da_salvare,
            "testo": scena_da_salvare,
            "evidenziata": in_memoria
        }
        salva_dati(FILE_SCENE, st.session_state["scene_salvate"])
        st.sidebar.success("SCENA SALVATA CON SUCCESSO! 🎉")
        st.rerun()
    else:
        st.sidebar.error("INSERISCI TITOLO E GENERALE PRIMA LA SCENA!")

# Lista delle scene salvate
st.sidebar.subheader("📚 LISTA SCENE SALVATE")
if st.session_state["scene_salvate"]:
    for tit, dati in st.session_state["scene_salvate"].items():
        # Se è stata salvata nella memoria del personaggio, la evidenziamo in giallo!
        if dati.get("evidenziata", False):
            st.sidebar.markdown(f"<div class='scena-evidenziata'>🟨 Cap {dati['capitolo']}: {tit} (In Memoria)</div>", unsafe_allow_html=True)
        else:
            st.sidebar.write(f"📄 Cap {dati['capitolo']}: {tit}")
else:
    st.sidebar.caption("Nessuna scena salvata ancora.")

# ==========================================
# 📝 TAVOLO DA LAVORO PRINCIPALE
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 1. APPUNTI DELLA SCENA")
    capitolo_corrente = st.number_input("📌 CAPITOLO CORRENTE:", min_value=1, value=1, step=1)
    
    # 🎙️ Registratore Vocale
    st.write("🎙️ **REGISTRA VOCALE APPUNTI:**")
    audio_bytes = audio_recorder(text="Clicca per registrare", icon_size="2x")
    if audio_bytes:
        with st.spinner("🎧 Trascrizione vocale..."):
            try:
                response_audio = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=["Trascrivi il file audio in italiano:", genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")]
                )
                st.session_state['appunti_voce'] = response_audio.text
                st.success("Vocale trascritto!")
            except Exception as e:
                st.error(f"Errore: {e}")

    # 📂 Upload file appunti/scena
    file_scena_up = st.file_uploader("📂 Oppure carica un file .txt con gli appunti:", type=["txt"])
    testo_file_caricato = ""
    if file_scena_up is not None:
        testo_file_caricato = file_scena_up.read().decode("utf-8", errors="ignore")

    valore_iniziale = st.session_state.get('appunti_voce', '') + ("\n" + testo_file_caricato if testo_file_caricato else "")
    appunti = st.text_area("SCRIVI O MODIFICA GLI APPUNTI:", value=valore_iniziale, height=200, placeholder="Es: Marco incontra Elena al bar...")
    st.session_state['appunti_temp'] = appunti
    
    if st.button("🚀 TRASFORMA IN SCENA CON MOCC_IA"):
        if appunti:
            with st.spinner("🤖 CREAZIONE SCENA IN CORSO..."):
                try:
                    info_p = ""
                    for nome, data in st.session_state["personaggi"].items():
                        if nome.lower() in appunti.lower():
                            info_p += f"\n--- PROFILO {nome.upper()} ---\nPROFILO: {data['profilo']}\n"
                            ricordi_passati = [f"NEL CAPITOLO {k}: {v}" for k, v in data.get("ricordi", {}).items() if int(k) < capitolo_corrente]
                            if ricordi_passati:
                                info_p += "RICORDI PASSATI:\n" + "\n".join(ricordi_passati) + "\n"
                    
                    prompt = f"Sei MOCC_IA, uno scrittore professionista.\nStai scrivendo per il Capitolo {capitolo_corrente}.\n{info_p}\nAppunti: {appunti}\nScrivi la scena in italiano in modo fluido ed emozionante."
                    response = client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
                    st.session_state['scena_generata'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
        else:
            st.warning("SCRIVI O CARICA PRIMA GLI APPUNTI!")

with col2:
    st.subheader("📖 2. LA SCENA GENERATA")
    scena_finale = st.text_area("TESTO FINALE DA MODIFICARE:", value=st.session_state.get('scena_generata', ''), height=340)
    st.session_state['scena_generata'] = scena_finale
