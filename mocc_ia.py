import streamlit as st
import os
import json
from google import genai
from audio_recorder_streamlit import audio_recorder

# ==========================================
# 🔑 1. CONTROLLO ACCESSO E PASSWORD
# ==========================================
PASSWORD_SEGRETA = "MOCCIA2026"

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.title("🔒 ACCESSO RISERVATO - MOCCIA.IA")
    pass_inserita = st.text_input("Inserisci la password segreta per accedere:", type="password")
    if st.button("Sblocca App"):
        if pass_inserita == PASSWORD_SEGRETA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Password errata! Riprova.")
    st.stop()

# ==========================================
# 2. CONFIGURAZIONE CHIAVE E PAGINA
# ==========================================
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6IWDCL_EFVyjE48i1A69svIGS6WMHNoQXrM6vl4bEvt_Q")
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="MOCCIA.IA", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    .scena-evidenziata {
        background-color: #f1c40f !important;
        color: #000000 !important;
        padding: 6px 10px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 MOCCIA.IA")

# ==========================================
# 💾 CARICAMENTO E SALVATAGGIO DATI
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
# 📐 STRUTTURA A 2 COLONNE PRINCIPALI
# ==========================================
col_sinistra, col_destra = st.columns([2, 1], gap="large")

# ------------------------------------------
# 📝 COLONNA SINISTRA: SCRITTURA & GENERAZIONE
# ------------------------------------------
with col_sinistra:
    st.header("📝 TAVOLO DA LAVORO SCRITTORE")
    
    col_appunti, col_generata = st.columns(2, gap="medium")
    
    with col_appunti:
        st.subheader("1. I Tuoi Appunti")
        
        testo_voce_o_file = st.session_state.get('appunti_voce_o_file', '')
        
        appunti = st.text_area(
            "Scrivi o modifica gli appunti:",
            value=testo_voce_o_file,
            height=240,
            placeholder="Es: Marta e Giovanni si incontrano a Ponte Milvio..."
        )
        st.session_state['appunti_temp'] = appunti

        st.write("🎙️️ **Registra Vocale per Appunti:**")
        audio_bytes_appunti = audio_recorder(text="Clicca l'icona per registrare/fermare", icon_size="2x", key="rec_appunti")
        
        if audio_bytes_appunti:
            col_btn_a1, col_btn_a2 = st.columns(2)
            with col_btn_a1:
                if st.button("🛑 STOP & TRASCRIVI", type="primary", use_container_width=True, key="btn_stop_appunti"):
                    with st.spinner("🎧 Trascrizione in corso..."):
                        try:
                            resp_audio = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=["Trascrivi fedelmente questo audio in italiano:", genai.types.Part.from_bytes(data=audio_bytes_appunti, mime_type="audio/wav")]
                            )
                            st.session_state['appunti_voce_o_file'] = resp_audio.text
                            st.toast("✅ Vocale trascritto!", icon="🎙️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore audio: {e}")
            with col_btn_a2:
                if st.button("🗑️️ CANCELLA AUDIO", use_container_width=True, key="btn_del_appunti"):
                    st.session_state['appunti_voce_o_file'] = ""
                    st.toast("🗑️ Audio cancellato!", icon="🧹")
                    st.rerun()

        file_appunti_up = st.file_uploader("📂 Carica file .txt per gli appunti:", type=["txt"], key="up_appunti")
        if file_appunti_up is not None:
            testo_caricato = file_appunti_up.read().decode("utf-8", errors="ignore")
            if st.session_state.get('appunti_voce_o_file') != testo_caricato:
                st.session_state['appunti_voce_o_file'] = testo_caricato
                st.toast("✅ File caricato negli appunti!", icon="📂")
                st.rerun()

        capitolo_corrente = st.number_input("📌 Numero Capitolo Corrente:", min_value=1, value=1, step=1)

        st.write("")
        if st.button("🚀 TRASFORMA IN SCENA CON MOCCIA.IA", type="primary", use_container_width=True):
            if appunti:
                with st.spinner("🤖 MOCCIA.IA sta elaborando la scena..."):
                    try:
                        info_p = ""
                        for nome, data in st.session_state["personaggi"].items():
                            if nome.lower() in appunti.lower():
                                info_p += f"\n--- PROFILO {nome.upper()} ---\nPROFILO: {data['profilo']}\n"
                                ricordi_passati = [f"NEL CAP {k}: {v}" for k, v in data.get("ricordi", {}).items() if int(k) < capitolo_corrente]
                                if ricordi_passati:
                                    info_p += "RICORDI PASSATI:\n" + "\n".join(ricordi_passati) + "\n"
                        
                        prompt = f"Sei MOCCIA.IA, uno scrittore professionista di romanzi.\nStai scrivendo per il Capitolo {capitolo_corrente}.\n{info_p}\nAppunti: {appunti}\nScrivi direttamente la scena in italiano in modo lungo, ricco di dettagli ed emozionante."
                        
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=prompt
                        )
                        st.session_state['scena_generata'] = response.text
                        st.toast("✨ Scena generata con successo!", icon="🎬")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore generazione: {e}")
            else:
                st.warning("Inserisci prima gli appunti!")

    with col_generata:
        st.subheader("2. La Scena Generata")
        scena_finale = st.text_area(
            "Testo finale della scena (puoi modificarlo):",
            value=st.session_state.get('scena_generata', ''),
            height=240
        )
        st.session_state['scena_generata'] = scena_finale

        st.divider()
        st.subheader("💾 Salva la Scena")
        titolo_scena = st.text_input("Titolo della Scena:", placeholder="Es: Il tramonto a Ponte Milvio")
        nuovo_fatto = st.text_input("Evento da salvare nella memoria dei personaggi:", placeholder="Es: Marta e Giovanni ricordano il lucchetto")

        if st.button("📁 SALVA SCENA NELL'ARCHIVIO", use_container_width=True):
            if scena_finale and titolo_scena:
                in_memoria = False
                if nuovo_fatto:
                    in_memoria = True
                    for nome in st.session_state["personaggi"]:
                        if nome.lower() in scena_finale.lower() or nome.lower() in st.session_state.get('appunti_temp', '').lower():
                            st.session_state["personaggi"][nome]["ricordi"][str(capitolo_corrente)] = f"[{titolo_scena}] {nuovo_fatto}"
                    salva_dati(FILE_PERSONAGGI, st.session_state["personaggi"])

                st.session_state["scene_salvate"][titolo_scena] = {
                    "capitolo": capitolo_corrente,
                    "testo": scena_finale,
                    "evidenziata": in_memoria
                }
                salva_dati(FILE_SCENE, st.session_state["scene_salvate"])
                
                st.toast(f"🎉 Scena '{titolo_scena}' salvata con successo!", icon="💾")
                if in_memoria:
                    st.toast("🧠 Ricordo aggiunto alla memoria dei personaggi!", icon="🟨")
                st.rerun()
            else:
                st.error("Inserisci un titolo e genera prima la scena!")

# ------------------------------------------
# 💡 COLONNA DESTRA: LUCE, PERSONAGGI & ARCHIVIO
# ------------------------------------------
with col_destra:
    st.header("💡 LUCE - EDITOR NARRATIVO")
    
    file_luce = st.file_uploader("📂 Invia un file .txt a Luce:", type=["txt"], key="up_luce")
    testo_file_luce = ""
    if file_luce is not None:
        testo_file_luce = file_luce.read().decode("utf-8", errors="ignore")

    domanda_luce = st.text_area("Chiedi un consiglio a Luce:", placeholder="Es: Come impostare meglio i dialoghi?", height=80)
    
    st.write("🎙️ **Parla a voce con Luce:**")
    audio_bytes_luce = audio_recorder(text="Clicca per registrare la domanda", icon_size="2x", key="rec_luce")
    
    testo_voce_luce = st.session_state.get('testo_voce_luce_temp', '')
    
    if audio_bytes_luce:
        col_btn_l1, col_btn_l2 = st.columns(2)
        with col_btn_l1:
            if st.button("🛑 STOP & TRASCRIVI", type="primary", use_container_width=True, key="btn_stop_luce"):
                with st.spinner("🎧 Trascrizione per Luce..."):
                    try:
                        resp_audio_l = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=["Trascrivi fedelmente questo audio in italiano:", genai.types.Part.from_bytes(data=audio_bytes_luce, mime_type="audio/wav")]
                        )
                        st.session_state['testo_voce_luce_temp'] = resp_audio_l.text
                        st.toast("✅ Messaggio per Luce trascritto!", icon="💡")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore audio Luce: {e}")
        with col_btn_l2:
            if st.button("🗑️ CANCELLA AUDIO", use_container_width=True, key="btn_del_luce"):
                st.session_state['testo_voce_luce_temp'] = ""
                st.toast("🗑️ Audio cancellato!", icon="🧹")
                st.rerun()

    if st.button("💬 PARLA CON LUCE", use_container_width=True, type="primary"):
        testo_completo_domanda = domanda_luce + ("\n" + testo_voce_luce if testo_voce_luce else "")
        if testo_completo_domanda or testo_file_luce:
            with st.spinner("Luce sta analizzando..."):
                try:
                    prompt_l = f"Sei Luce, un'esperta editor narrativa. Rispondi in modo pratico.\nFile allegato: {testo_file_luce}\nDomanda dello scrittore: {testo_completo_domanda}"
                    resp_l = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt_l
                    )
                    st.info(f"**Luce:** {resp_l.text}")
                except Exception as e:
                    st.error(f"Errore: {e}")

    st.divider()

    st.header("🎭 GESTIONE PERSONAGGI")
    with st.expander("➕ Aggiungi / Modifica Personaggio"):
        nome_p = st.text_input("Nome Personaggio:")
        desc_p = st.text_area("Profilo e Carattere:", height=80)
        file_p = st.file_uploader("📂 Carica file .txt profilo:", type=["txt"], key="file_p_up")
        if file_p is not None:
            desc_p += "\n" + file_p.read().decode("utf-8", errors="ignore")
        
        if st.button("💾 Salva Personaggio", use_container_width=True):
            if nome_p:
                if nome_p not in st.session_state["personaggi"]:
                    st.session_state["personaggi"][nome_p] = {"profilo": desc_p, "ricordi": {}}
                else:
                    st.session_state["personaggi"][nome_p]["profilo"] = desc_p
                salva_dati(FILE_PERSONAGGI, st.session_state["personaggi"])
                st.toast(f"👤 Personaggio {nome_p} salvato!", icon="💾")
                st.rerun()

    if st.session_state["personaggi"]:
        for nome, info in st.session_state["personaggi"].items():
            with st.expander(f"👤 {nome}"):
                st.caption(f"**PROFILO:** {info['profilo']}")
                st.caption("**RICORDI:**")
                for k, v in info.get("ricordi", {}).items():
                    st.caption(f"- Cap {k}: {v}")

    st.divider()

    st.header("📚 SCENE SALVATE")
    if st.session_state["scene_salvate"]:
        for tit, dati in st.session_state["scene_salvate"].items():
            if dati.get("evidenziata", False):
                st.markdown(f"<div class='scena-evidenziata'>🟨 Cap {dati['capitolo']}: {tit} (In Memoria)</div>", unsafe_allow_html=True)
            else:
                st.write(f"📄 **Cap {dati['capitolo']}:** {tit}")
            with st.expander(f"Leggi '{tit}'"):
                st.write(dati["testo"])
    else:
        st.caption("Nessuna scena ancora salvata.")
