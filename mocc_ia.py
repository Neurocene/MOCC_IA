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

# CSS Personalizzato: Fondino sotto il microfono + Icona Bianco/Rosso
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
    .scena-libro {
        background-color: #2ecc71 !important;
        color: #ffffff !important;
        padding: 6px 10px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 6px;
    }
    /* Barra bianca evidente di separazione */
    .separatore-bianco {
        border: none;
        height: 4px;
        background-color: #ffffff;
        margin: 35px 0;
        box-shadow: 0px 0px 8px rgba(255, 255, 255, 0.8);
    }
    
    /* 🎙️ Fondino circolare per evidenziare l'icona del microfono */
    iframe[title="audio_recorder_streamlit.audio_recorder"] {
        background-color: #2b2b2b !important;
        padding: 6px 12px;
        border-radius: 20px;
        border: 1px solid #444444;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 MOCCIA.IA")

# ==========================================
# 💾 CARICAMENTO E SALVATAGGIO DATI
# ==========================================
FILE_PERSONAGGI = "personaggi_memoria.json"
FILE_SCENE = "scene_salvate.json"
FILE_LIBRO = "libro_capitoli.json"

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

if "libro" not in st.session_state:
    st.session_state["libro"] = carica_dati(FILE_LIBRO)

# ==========================================
# 🚀 SEZIONE SUPERIORE: SCRITTURA & GENERAZIONE
# ==========================================
col_pensieri, col_scena = st.columns(2, gap="large")

with col_pensieri:
    st.subheader("💭 1. I pensieri di Federico")
    
    testo_voce_o_file = st.session_state.get('appunti_voce_o_file', '')
    
    appunti = st.text_area(
        "Scrivi o modifica i tuoi pensieri:",
        value=testo_voce_o_file,
        height=260,
        placeholder="Es: Marta e Giovanni si incontrano a Ponte Milvio..."
    )
    st.session_state['appunti_temp'] = appunti

    st.write("🎙️ **Registra Vocale per i Pensieri:**")
    audio_bytes_appunti = audio_recorder(
        text="Clicca per registrare/fermare", 
        icon_size="2x", 
        neutral_color="#FFFFFF",
        recording_color="#FF0000",
        key="rec_appunti"
    )
    
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
                        st.toast("✅ Vocale trascritto nei pensieri!", icon="🎙️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore audio: {e}")
        with col_btn_a2:
            if st.button("🗑️ CANCELLA AUDIO", use_container_width=True, key="btn_del_appunti"):
                st.session_state['appunti_voce_o_file'] = ""
                st.toast("🗑️ Audio cancellato!", icon="🧹")
                st.rerun()

    file_appunti_up = st.file_uploader("📂 Carica file .txt con i pensieri:", type=["txt"], key="up_appunti")
    if file_appunti_up is not None:
        testo_caricato = file_appunti_up.read().decode("utf-8", errors="ignore")
        if st.session_state.get('appunti_voce_o_file') != testo_caricato:
            st.session_state['appunti_voce_o_file'] = testo_caricato
            st.toast("✅ File caricato con successo nei pensieri di Federico!", icon="📂")
            st.rerun()

    st.write("")
    if st.button("🚀 TRASFORMA IN SCENA CON MOCCIA.IA", type="primary", use_container_width=True):
        if appunti:
            with st.spinner("🤖 MOCCIA.IA sta elaborando la scena..."):
                try:
                    info_p = ""
                    for nome, data in st.session_state["personaggi"].items():
                        if nome.lower() in appunti.lower():
                            info_p += f"\n--- PROFILO {nome.upper()} ---\nPROFILO: {data['profilo']}\n"
                            ricordi_passati = [f"NEL CAP {k}: {v}" for k, v in data.get("ricordi", {}).items()]
                            if ricordi_passati:
                                info_p += "RICORDI PASSATI:\n" + "\n".join(ricordi_passati) + "\n"
                    
                    prompt = f"Sei MOCCIA.IA, uno scrittore professionista di romanzi.\n{info_p}\nPensieri di Federico: {appunti}\nScrivi direttamente la scena in italiano in modo lungo, ricco di dettagli ed emozionante."
                    
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
            st.warning("Inserisci prima i pensieri di Federico!")

with col_scena:
    st.subheader("🎬 2. La Scena Generata")
    scena_finale = st.text_area(
        "Testo finale della scena (puoi modificarlo):",
        value=st.session_state.get('scena_generata', ''),
        height=260
    )
    st.session_state['scena_generata'] = scena_finale

    st.divider()
    st.subheader("💾 Salva la Scena")
    titolo_scena = st.text_input("Titolo della Scena:", placeholder="Es: Il tramonto a Ponte Milvio")
    num_capitolo_salva = st.number_input("Numero capitolo:", min_value=1, value=1, step=1, key="cap_salva")

    if st.button("📁 SALVA SCENA NELL'ARCHIVIO", use_container_width=True, type="primary"):
        if scena_finale and titolo_scena:
            pensieri_attuali = st.session_state.get('appunti_temp', '')
            
            st.session_state["scene_salvate"][titolo_scena] = {
                "capitolo": num_capitolo_salva,
                "pensieri_federico": pensieri_attuali,
                "testo": scena_finale,
                "in_libro": False
            }
            salva_dati(FILE_SCENE, st.session_state["scene_salvate"])
            
            st.toast(f"🎉 Scena '{titolo_scena}' salvata con successo per il Capitolo {num_capitolo_salva}!", icon="💾")
            st.rerun()
        else:
            st.error("Inserisci un titolo e genera prima la scena!")

# ==========================================
# ⚪ BARRA BIANCA DI SEPARAZIONE EVIDENTE
# ==========================================
st.markdown("<hr class='separatore-bianco'>", unsafe_allow_html=True)

# ==========================================
# 💡 SEZIONE INFERIORE: LUCE & GESTIONE ARCHIVIO/LIBRO/PERSONAGGI
# ==========================================
col_luce, col_destra_inferiore = st.columns([1, 1], gap="large")

# --- COLONNA INFERIORE SINISTRA: LUCE ---
with col_luce:
    st.header("💡 LUCE - EDITOR NARRATIVO")
    
    opzioni_scene = ["Nessuna scena selezionata"] + list(st.session_state["scene_salvate"].keys())
    scena_scelta_luce = st.selectbox("📖 Seleziona una singola scena da analizzare:", opzioni_scene)
    
    testo_scena_selezionata = ""
    if scena_scelta_luce != "Nessuna scena selezionata":
        dati_s = st.session_state["scene_salvate"][scena_scelta_luce]
        pensieri_collegati = dati_s.get("pensieri_federico", "Nessun pensiero specificato.")
        testo_scena_selezionata = f"\n--- SCENA SINGOLA SELEZIONATA ('{scena_scelta_luce}' - Cap {dati_s['capitolo']}) ---\nPENSIERI DI FEDERICO:\n{pensieri_collegati}\n\nTESTO SCENA:\n{dati_s['testo']}\n"

    file_luce = st.file_uploader("📂 Invia un file .txt esterno a Luce:", type=["txt"], key="up_luce")
    testo_file_luce = ""
    if file_luce is not None:
        testo_file_luce = file_luce.read().decode("utf-8", errors="ignore")
        if st.session_state.get('last_luce_file') != file_luce.name:
            st.session_state['last_luce_file'] = file_luce.name
            st.toast("✅ File caricato con successo per Luce!", icon="💡")

    domanda_luce = st.text_area("Chiedi un consiglio o come andare avanti a Luce:", placeholder="Es: Analizza la coerenza complessiva del libro o dammi idee per i prossimi capitoli", height=100)
    
    st.write("🎙️️ **Parla a voce con Luce:**")
    audio_bytes_luce = audio_recorder(
        text="Clicca per registrare la domanda", 
        icon_size="2x", 
        neutral_color="#FFFFFF",
        recording_color="#FF0000",
        key="rec_luce"
    )
    
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

    testo_libro_completo = ""
    if st.session_state["libro"]:
        testo_libro_completo = "\n=== MEMORIA DEL LIBRO (SCENE INSERITE NELLA NARRATIVA UNICA) ===\n"
        scene_ordinate = sorted(st.session_state["libro"].items(), key=lambda x: x[1].get("capitolo", 0))
        for tit, d in scene_ordinate:
            testo_libro_completo += f"\n--- CAPITOLO {d['capitolo']}: {tit} ---\nPENSIERI ORIGINALI DI FEDERICO:\n{d.get('pensieri_federico', '')}\n\nTESTO SCENA:\n{d['testo']}\n"

    if st.button("💬 PARLA CON LUCE", use_container_width=True, type="primary"):
        testo_completo_domanda = domanda_luce + ("\n" + testo_voce_luce if testo_voce_luce else "")
        if testo_completo_domanda or testo_file_luce or testo_scena_selezionata or testo_libro_completo:
            with st.spinner("Luce sta analizzando il libro e le informazioni..."):
                try:
                    prompt_l = f"""Sei Luce, un'esperta editor narrativa e consulente letteraria d'élite per romanzi.
Hai accesso completo alla memoria del "LIBRO" (l'insieme dei capitoli ufficialmente approvati) e alle singole scene.

IL TUO OBIETTIVO:
1. Mantenere una visione d'insieme del LIBRO come opera unica, organica e coerente.
2. Identificare discrepanze, buchi di trama, anomalie temporali, incongruenze nei personaggi o nei pensieri di Federico.
3. Proporre correzioni pratiche e concrete per armonizzare il romanzo.
4. Suggerire idee per i capitoli successivi garantendo continuità e ritmo.

{testo_libro_completo}
{testo_scena_selezionata}
File allegato: {testo_file_luce}
Domanda dello scrittore: {testo_completo_domanda}"""

                    resp_l = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt_l
                    )
                    st.info(f"**Luce:** {resp_l.text}")
                except Exception as e:
                    st.error(f"Errore: {e}")
        else:
            st.warning("Aggiungi scene al libro, carica un file o fai una domanda a Luce!")

# --- COLONNA INFERIORE DESTRA: ARCHIVIO -> LIBRO -> PERSONAGGI ---
with col_destra_inferiore:
    # 1. ARCHIVIO SCENE
    st.header("📚 ARCHIVIO SCENE SALVATE")
    if st.session_state["scene_salvate"]:
        for tit, dati in st.session_state["scene_salvate"].items():
            in_lib = dati.get("in_libro", False) or (tit in st.session_state["libro"])
            
            if in_lib:
                st.markdown(f"<div class='scena-libro'>📖 Cap {dati['capitolo']}: {tit} (Nel Libro)</div>", unsafe_allow_html=True)
            elif dati.get("evidenziata", False):
                st.markdown(f"<div class='scena-evidenziata'>🟨 Cap {dati['capitolo']}: {tit} (In Memoria)</div>", unsafe_allow_html=True)
            else:
                st.write(f"📄 **Cap {dati['capitolo']}:** {tit}")
            
            with st.expander(f"Leggi '{tit}'"):
                if dati.get("pensieri_federico"):
                    st.caption(f"💭 **Pensieri di Federico:** {dati['pensieri_federico']}")
                    st.divider()
                st.write(dati["testo"])
                st.write("")
                
                if not in_lib:
                    if st.button(f"📖 Aggiungi al Libro", key=f"add_lib_{tit}", use_container_width=True):
                        st.session_state["libro"][tit] = dati
                        st.session_state["scene_salvate"][tit]["in_libro"] = True
                        salva_dati(FILE_LIBRO, st.session_state["libro"])
                        salva_dati(FILE_SCENE, st.session_state["scene_salvate"])
                        st.toast(f"Aggiunto '{tit}' al Libro e alla memoria di Luce!", icon="📖")
                        st.rerun()
    else:
        st.caption("Nessuna scena ancora salvata nell'archivio.")

    st.divider()

    # 2. IL LIBRO
    st.header("📖 IL LIBRO")
    if st.session_state["libro"]:
        st.caption(f"Contiene **{len(st.session_state['libro'])}** scene che formano l'opera unica.")
        scene_libro_ord = sorted(st.session_state["libro"].items(), key=lambda x: x[1].get("capitolo", 0))
        for tit, dati in scene_libro_ord:
            st.markdown(f"<div class='scena-libro'>📖 Cap {dati['capitolo']}: {tit}</div>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                with st.expander(f"Leggi Cap {dati['capitolo']}: {tit}"):
                    if dati.get("pensieri_federico"):
                        st.caption(f"💭 **Pensieri di Federico:** {dati['pensieri_federico']}")
                        st.divider()
                    st.write(dati["testo"])
            with col_b2:
                if st.button("❌ Rimuovi", key=f"rem_lib_{tit}", use_container_width=True):
                    del st.session_state["libro"][tit]
                    if tit in st.session_state["scene_salvate"]:
                        st.session_state["scene_salvate"][tit]["in_libro"] = False
                    salva_dati(FILE_LIBRO, st.session_state["libro"])
                    salva_dati(FILE_SCENE, st.session_state["scene_salvate"])
                    st.toast(f"Rimosso '{tit}' dal Libro", icon="🗑️")
                    st.rerun()
    else:
        st.caption("Nessuna scena inserita nel Libro. Aggiungi le scene dall'Archivio sovrastante.")

    st.divider()

    # 3. GESTIONE PERSONAGGI
    st.header("🎭 GESTIONE PERSONAGGI")
    with st.expander("➕ Aggiungi / Modifica Personaggio"):
        nome_p = st.text_input("Nome Personaggio:")
        desc_p = st.text_area("Profilo e Carattere:", height=80)
        file_p = st.file_uploader("📂 Carica file .txt profilo:", type=["txt"], key="file_p_up")
        if file_p is not None:
            desc_p += "\n" + file_p.read().decode("utf-8", errors="ignore")
            if st.session_state.get('last_p_file') != file_p.name:
                st.session_state['last_p_file'] = file_p.name
                st.toast("✅ Profilo personaggio caricato da file!", icon="👤")
        
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
