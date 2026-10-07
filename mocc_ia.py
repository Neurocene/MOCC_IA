import json
import os
from openai import OpenAI
import streamlit as st
from supabase import create_client

# ==========================================
# 🔑 1. CONTROLLO ACCESSO E PASSWORD
# ==========================================
PASSWORD_SEGRETA = "MOCCIA2026"

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.title("🔒 ACCESSO RISERVATO - MOCCIA.IA")
    pass_inserita = st.text_input(
        "Inserisci la password segreta per accedere:", type="password"
    )
    if st.button("Sblocca App"):
        if pass_inserita == PASSWORD_SEGRETA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Password errata! Riprova.")
    st.stop()

# ==========================================
# 2. CONFIGURAZIONE CHIAVI, SUPABASE E PAGINA
# ==========================================
st.set_page_config(page_title="MOCCIA.IA", page_icon="📚", layout="wide")

# Inizializzazione protetta Client OpenAI (ChatGPT)
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", None)

client = None
if OPENAI_KEY and OPENAI_KEY.strip() != "":
    try:
        client = OpenAI(api_key=OPENAI_KEY)
    except Exception as e:
        st.error(f"⚠️ Errore nell'inizializzazione di OpenAI: {e}")
else:
    st.warning(
        "⚠️ Attenzione: OPENAI_API_KEY non trovata o vuota nei Secrets di Streamlit Cloud."
    )

# Configurazione Connessione Supabase
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Errore connessione Supabase: {e}")

# STILI CSS
st.markdown(
    """
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
    .separatore-bianco {
        border: none;
        height: 4px;
        background-color: #ffffff;
        margin: 35px 0;
        box-shadow: 0px 0px 8px rgba(255, 255, 255, 0.8);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🎬 MOCCIA.IA")


# ==========================================
# 💾 CARICAMENTO E SALVATAGGIO CLOUD SUPABASE (PROTEGGI CON TRY/EXCEPT)
# ==========================================
def carica_dati_supabase():
    scene, libro, personaggi = {}, {}, {}
    if not supabase:
        return scene, libro, personaggi

    try:
        res_scene = supabase.table("scene").select("*").execute()
        for r in res_scene.data:
            scene[r["titolo"]] = {
                "capitolo": r["capitolo"],
                "pensieri_federico": r.get("pensieri_federico", ""),
                "testo": r.get("testo", ""),
                "in_libro": r.get("in_libro", False),
            }
    except Exception as e:
        st.warning(f"⚠️ Impossibile caricare scene da Supabase: {e}")

    try:
        res_libro = supabase.table("libro").select("*").execute()
        for r in res_libro.data:
            libro[r["titolo"]] = {
                "capitolo": r["capitolo"],
                "pensieri_federico": r.get("pensieri_federico", ""),
                "testo": r.get("testo", ""),
            }
    except Exception as e:
        st.warning(f"⚠️ Impossibile caricare il libro da Supabase: {e}")

    try:
        res_p = supabase.table("personaggi").select("*").execute()
        for r in res_p.data:
            personaggi[r["nome"]] = {
                "profilo": r.get("profilo", ""),
                "ricordi": r.get("ricordi", {}),
            }
    except Exception as e:
        st.warning(f"⚠️ Impossibile caricare i personaggi da Supabase: {e}")

    return scene, libro, personaggi


def salva_scena_supabase(titolo, dati):
    if supabase:
        try:
            supabase.table("scene").upsert(
                {
                    "titolo": titolo,
                    "capitolo": dati["capitolo"],
                    "pensieri_federico": dati["pensieri_federico"],
                    "testo": dati["testo"],
                    "in_libro": dati["in_libro"],
                }
            ).execute()
        except Exception as e:
            st.error(f"❌ Errore salvataggio scena su Supabase (Disabilita RLS o assegna Primary Key a 'titolo'): {e}")


def salva_libro_supabase(titolo, dati):
    if supabase:
        try:
            supabase.table("libro").upsert(
                {
                    "titolo": titolo,
                    "capitolo": dati["capitolo"],
                    "pensieri_federico": dati["pensieri_federico"],
                    "testo": dati["testo"],
                }
            ).execute()
        except Exception as e:
            st.error(f"❌ Errore salvataggio libro su Supabase: {e}")


def rimuovi_libro_supabase(titolo):
    if supabase:
        try:
            supabase.table("libro").delete().eq("titolo", titolo).execute()
        except Exception as e:
            st.error(f"❌ Errore rimozione dal libro su Supabase: {e}")


def salva_personaggio_supabase(nome, dati):
    if supabase:
        try:
            supabase.table("personaggi").upsert(
                {"nome": nome, "profilo": dati["profilo"], "ricordi": dati["ricordi"]}
            ).execute()
        except Exception as e:
            st.error(f"❌ Errore salvataggio personaggio su Supabase: {e}")


if "scene_salvate" not in st.session_state:
    s, l, p = carica_dati_supabase()
    st.session_state["scene_salvate"] = s
    st.session_state["libro"] = l
    st.session_state["personaggi"] = p

# Chiavi dinamiche per reset immediato dei registratori
if "key_audio_pensieri" not in st.session_state:
    st.session_state["key_audio_pensieri"] = 0

if "key_audio_luce" not in st.session_state:
    st.session_state["key_audio_luce"] = 0

# ==========================================
# 🚀 SEZIONE SUPERIORE: SCRITTURA & GENERAZIONE
# ==========================================
col_pensieri, col_scena = st.columns(2, gap="large")

with col_pensieri:
    st.subheader("💭 1. I pensieri di Federico")

    testo_voce_o_file = st.session_state.get("appunti_voce_o_file", "")

    appunti = st.text_area(
        "Scrivi o modifica i tuoi pensieri:",
        value=testo_voce_o_file,
        height=220,
        placeholder="Es: Marta e Giovanni si incontrano a Ponte Milvio...",
    )
    st.session_state["appunti_temp"] = appunti

    # ==========================================
    # 🎙 REGISTRAZIONE VOCALE CON RESET ISTANTANEO
    # ==========================================
    st.markdown("### 🎙️ Registrazione vocale")

    key_pensieri = f"audio_pensieri_{st.session_state['key_audio_pensieri']}"
    audio_value_pensieri = st.audio_input(
        "Premi il microfono per registrare i pensieri", key=key_pensieri
    )

    if audio_value_pensieri is not None:
        if client:
            with st.spinner("🎧 Trascrizione in corso con Whisper..."):
                try:
                    temp_path = "temp_audio_pensieri.wav"
                    with open(temp_path, "wb") as f:
                        f.write(audio_value_pensieri.read())

                    with open(temp_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", file=audio_file, language="it"
                        )

                    testo_precedente = st.session_state.get(
                        "appunti_voce_o_file", ""
                    )
                    if testo_precedente:
                        st.session_state["appunti_voce_o_file"] = (
                            testo_precedente + "\n" + transcript.text
                        )
                    else:
                        st.session_state["appunti_voce_o_file"] = (
                            transcript.text
                        )

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    st.session_state["key_audio_pensieri"] += 1
                    st.toast(
                        "✅ Registrazione trascritta con successo!", icon="🎙️"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante la trascrizione: {e}")
        else:
            st.error("Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit.")

    if st.button(
        "🗑️ Cancella testo pensieri",
        use_container_width=True,
        key="btn_del_appunti",
    ):
        st.session_state["appunti_voce_o_file"] = ""
        st.toast("🗑️ Contenuto cancellato!", icon="🧹")
        st.rerun()

    st.divider()

    file_appunti_up = st.file_uploader(
        "📂 Carica file .txt con i pensieri:", type=["txt"], key="up_appunti"
    )
    if file_appunti_up is not None:
        testo_caricato = file_appunti_up.read().decode("utf-8", errors="ignore")
        if st.session_state.get("appunti_voce_o_file") != testo_caricato:
            st.session_state["appunti_voce_o_file"] = testo_caricato
            st.toast("✅ File caricato nei pensieri di Federico!", icon="📂")
            st.rerun()

    st.write("")
    if st.button(
        "🚀 TRASFORMA IN SCENA CON MOCCIA.IA",
        type="primary",
        use_container_width=True,
    ):
        if appunti:
            if client:
                with st.spinner(
                    "🤖 MOCCIA.IA sta elaborando la scena con ChatGPT..."
                ):
                    try:
                        info_p = ""
                        for (
                            nome,
                            data,
                        ) in st.session_state["personaggi"].items():
                            if nome.lower() in appunti.lower():
                                info_p += f"\n--- PROFILO {nome.upper()} ---\nPROFILO: {data['profilo']}\n"
                                ricordi_passati = [
                                    f"NEL CAP {k}: {v}"
                                    for k, v in data.get("ricordi", {}).items()
                                ]
                                if ricordi_passati:
                                    info_p += (
                                        "RICORDI PASSATI:\n"
                                        + "\n".join(ricordi_passati)
                                        + "\n"
                                    )

                        prompt = f"Sei MOCCIA.IA, uno scrittore professionista di romanzi.\n{info_p}\nPensieri di Federico: {appunti}\nScrivi direttamente la scena in italiano in modo lungo, ricco di dettagli ed emozionante."

                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        st.session_state["scena_generata"] = (
                            response.choices[0].message.content
                        )
                        st.toast("✨ Scena generata con successo!", icon="🎬")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore generazione: {e}")
            else:
                st.error(
                    "Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit."
                )
        else:
            st.warning("Inserisci prima i pensieri di Federico!")

with col_scena:
    st.subheader("🎬 2. La Scena Generata")
    scena_finale = st.text_area(
        "Testo finale della scena (puoi modificarlo):",
        value=st.session_state.get("scena_generata", ""),
        height=260,
    )
    st.session_state["scena_generata"] = scena_finale

    st.divider()
    st.subheader("💾 Salva la Scena")
    titolo_scena = st.text_input(
        "Titolo della Scena:", placeholder="Es: Il tramonto a Ponte Milvio"
    )
    num_capitolo_salva = st.number_input(
        "Numero capitolo:", min_value=1, value=1, step=1, key="cap_salva"
    )

    if st.button(
        "📁 SALVA SCENA NELL'ARCHIVIO",
        use_container_width=True,
        type="primary",
    ):
        if scena_finale and titolo_scena:
            pensieri_attuali = st.session_state.get("appunti_temp", "")

            dati_scena = {
                "capitolo": num_capitolo_salva,
                "pensieri_federico": pensieri_attuali,
                "testo": scena_finale,
                "in_libro": False,
            }
            st.session_state["scene_salvate"][titolo_scena] = dati_scena
            salva_scena_supabase(titolo_scena, dati_scena)

            st.toast(
                f"🎉 Scena '{titolo_scena}' salvata nel Cloud per tutti!",
                icon="💾",
            )
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

    opzioni_scene = ["Nessuna scena selezionata"] + list(
        st.session_state["scene_salvate"].keys()
    )
    scena_scelta_luce = st.selectbox(
        "📖 Seleziona una singola scena da analizzare:", opzioni_scene
    )

    testo_scena_selezionata = ""
    if scena_scelta_luce != "Nessuna scena selezionata":
        dati_s = st.session_state["scene_salvate"][scena_scelta_luce]
        pensieri_collegati = dati_s.get(
            "pensieri_federico", "Nessun pensiero specificato."
        )
        testo_scena_selezionata = f"\n--- SCENA SINGOLA SELEZIONATA ('{scena_scelta_luce}' - Cap {dati_s['capitolo']}) ---\nPENSIERI DI FEDERICO:\n{pensieri_collegati}\n\nTESTO SCENA:\n{dati_s['testo']}\n"

    file_luce = st.file_uploader(
        "📂 Invia un file .txt esterno a Luce:", type=["txt"], key="up_luce"
    )
    testo_file_luce = ""
    if file_luce is not None:
        testo_file_luce = file_luce.read().decode("utf-8", errors="ignore")

    domanda_luce = st.text_area(
        "Chiedi un consiglio o come andare avanti a Luce:",
        placeholder="Es: Analizza la coerenza complessiva del libro o dammi idee per i prossimi capitoli",
        height=100,
    )

    st.markdown("### 🎙️ Registrazione vocale Luce")
    key_luce = f"audio_luce_{st.session_state['key_audio_luce']}"
    audio_value_luce = st.audio_input(
        "Parla a voce con Luce", key=key_luce
    )

    testo_voce_luce = st.session_state.get("testo_voce_luce_temp", "")

    if audio_value_luce is not None:
        if client:
            with st.spinner("🎧 Trascrizione per Luce con Whisper..."):
                try:
                    temp_path_luce = "temp_luce_audio.wav"
                    with open(temp_path_luce, "wb") as f:
                        f.write(audio_value_luce.read())

                    with open(temp_path_luce, "rb") as audio_file:
                        transcript_l = client.audio.transcriptions.create(
                            model="whisper-1", file=audio_file, language="it"
                        )
                    st.session_state["testo_voce_luce_temp"] = (
                        transcript_l.text
                    )

                    if os.path.exists(temp_path_luce):
                        os.remove(temp_path_luce)

                    st.session_state["key_audio_luce"] += 1
                    st.toast("✅ Messaggio per Luce trascritto!", icon="💡")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore audio Luce: {e}")
        else:
            st.error("Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit.")

    testo_libro_completo = ""
    if st.session_state["libro"]:
        testo_libro_completo = "\n=== MEMORIA DEL LIBRO (SCENE INSERITE NELLA NARRATIVA UNICA) ===\n"
        scene_ordinate = sorted(
            st.session_state["libro"].items(),
            key=lambda x: x[1].get("capitolo", 0),
        )
        for tit, d in scene_ordinate:
            testo_libro_completo += f"\n--- CAPITOLO {d['capitolo']}: {tit} ---\nPENSIERI ORIGINALI DI FEDERICO:\n{d.get('pensieri_federico', '')}\n\nTESTO SCENA:\n{d['testo']}\n"

    if st.button("💬 PARLA CON LUCE", use_container_width=True, type="primary"):
        testo_completo_domanda = domanda_luce + (
            "\n" + testo_voce_luce if testo_voce_luce else ""
        )
        if (
            testo_completo_domanda
            or testo_file_luce
            or testo_scena_selezionata
            or testo_libro_completo
        ):
            if client:
                with st.spinner("Luce sta analizzando il libro con ChatGPT..."):
                    try:
                        prompt_l = f"""Sei Luce, un'esperta editor narrativa e consulente letteraria d'élite per romanzi.
Hai accesso completo alla memoria del "LIBRO" (l'insieme dei capitoli ufficialmente approvati) e alle singole scene.

IL TUO OBIETTIVO:
1. Mantenere una visione d'insieme del LIBRO come opera unica, organica e coerente.
2. Identificare discrepanze, buchi di trama, anomalie temporali, incongruenze nei personaggi o nei pensieri di Federico.
3. Proporre correzioni pratiche e concrete per harmonizzare il romanzo.
4. Suggerire idee per i capitoli successivi garantendo continuità e ritmo.

{testo_libro_completo}
{testo_scena_selezionata}
File allegato: {testo_file_luce}
Domanda dello scrittore: {testo_completo_domanda}"""

                        resp_l = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt_l}],
                        )
                        st.info(f"**Luce:** {resp_l.choices[0].message.content}")
                    except Exception as e:
                        st.error(f"Errore: {e}")
            else:
                st.error(
                    "Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit."
                )
        else:
            st.warning(
                "Aggiungi scene al libro, carica un file o fai una domanda a Luce!"
            )

# --- COLONNA INFERIORE DESTRA: ARCHIVIO -> LIBRO -> PERSONAGGI ---
with col_destra_inferiore:
    # 1. ARCHIVIO SCENE
    st.header("📚 ARCHIVIO SCENE SALVATE")
    if st.session_state["scene_salvate"]:
        for tit, dati in st.session_state["scene_salvate"].items():
            in_lib = dati.get("in_libro", False) or (
                tit in st.session_state["libro"]
            )

            if in_lib:
                st.markdown(
                    f"<div class='scena-libro'>📖 Cap {dati['capitolo']}: {tit} (Nel Libro)</div>",
                    unsafe_allow_html=True,
                )
            elif dati.get("evidenziata", False):
                st.markdown(
                    f"<div class='scena-evidenziata'>🟨 Cap {dati['capitolo']}: {tit} (In Memoria)</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.write(f"📄 **Cap {dati['capitolo']}:** {tit}")

            with st.expander(f"Leggi '{tit}'"):
                if dati.get("pensieri_federico"):
                    st.caption(
                        f"💭 **Pensieri di Federico:** {dati['pensieri_federico']}"
                    )
                    st.divider()
                st.write(dati["testo"])
                st.write("")

                if not in_lib:
                    if st.button(
                        f"📖 Aggiungi al Libro",
                        key=f"add_lib_{tit}",
                        use_container_width=True,
                    ):
                        st.session_state["libro"][tit] = dati
                        st.session_state["scene_salvate"][tit]["in_libro"] = True
                        salva_libro_supabase(tit, dati)
                        salva_scena_supabase(
                            tit, st.session_state["scene_salvate"][tit]
                        )
                        st.toast(
                            f"Aggiunto '{tit}' al Libro sul Cloud!", icon="📖"
                        )
                        st.rerun()
    else:
        st.caption("Nessuna scena ancora salvata nell'archivio.")

    st.divider()

    # 2. IL LIBRO
    st.header("📖 IL LIBRO")
    if st.session_state["libro"]:
        st.caption(
            f"Contiene **{len(st.session_state['libro'])}** scene che formano l'opera unica."
        )
        scene_libro_ord = sorted(
            st.session_state["libro"].items(),
            key=lambda x: x[1].get("capitolo", 0),
        )
        for tit, dati in scene_libro_ord:
            st.markdown(
                f"<div class='scena-libro'>📖 Cap {dati['capitolo']}: {tit}</div>",
                unsafe_allow_html=True,
            )
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                with st.expander(f"Leggi Cap {dati['capitolo']}: {tit}"):
                    if dati.get("pensieri_federico"):
                        st.caption(
                            f"💭 **Pensieri di Federico:** {dati['pensieri_federico']}"
                        )
                        st.divider()
                    st.write(dati["testo"])
            with col_b2:
                if st.button(
                    "❌ Rimuovi",
                    key=f"rem_lib_{tit}",
                    use_container_width=True,
                ):
                    del st.session_state["libro"][tit]
                    rimuovi_libro_supabase(tit)
                    if tit in st.session_state["scene_salvate"]:
                        st.session_state["scene_salvate"][tit][
                            "in_libro"
                        ] = False
                        salva_scena_supabase(
                            tit, st.session_state["scene_salvate"][tit]
                        )
                    st.toast(f"Rimosso '{tit}' dal Libro", icon="🗑️")
                    st.rerun()
    else:
        st.caption(
            "Nessuna scena inserita nel Libro. Aggiungi le scene dall'Archivio sovrastante."
        )

    st.divider()

    # 3. GESTIONE PERSONAGGI
    st.header("🎭 GESTIONE PERSONAGGI")
    with st.expander("➕ Aggiungi / Modifica Personaggio"):
        nome_p = st.text_input("Nome Personaggio:")
        desc_p = st.text_area("Profilo e Carattere:", height=80)
        file_p = st.file_uploader(
            "📂 Carica file .txt profilo:", type=["txt"], key="file_p_up"
        )
        if file_p is not None:
            desc_p += "\n" + file_p.read().decode("utf-8", errors="ignore")

        if st.button("💾 Salva Personaggio", use_container_width=True):
            if nome_p:
                dati_p = {
                    "profilo": desc_p,
                    "ricordi": st.session_state["personaggi"]
                    .get(nome_p, {})
                    .get("ricordi", {}),
                }
                st.session_state["personaggi"][nome_p] = dati_p
                salva_personaggio_supabase(nome_p, dati_p)
                st.toast(f"👤 Personaggio {nome_p} salvato!", icon="💾")
                st.rerun()

    if st.session_state["personaggi"]:
        for nome, info in st.session_state["personaggi"].items():
            with st.expander(f"👤 {nome}"):
                st.caption(f"**PROFILO:** {info['profilo']}")
                st.caption("**RICORDI:**")
                for k, v in info.get("ricordi", {}).items():
                    st.caption(f"- Cap {k}: {v}")
