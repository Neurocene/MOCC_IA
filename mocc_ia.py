with col_pensieri:
    st.subheader("💭 1. I pensieri di Federico")

    testo_voce_o_file = st.session_state.get("appunti_voce_o_file", "")

    appunti = st.text_area(
        "Scrivi o modifica i tuoi pensieri:",
        value=testo_voce_o_file,
        height=240,
        placeholder="Es: Marta e Giovanni si incontrano a Ponte Milvio...",
    )
    st.session_state["appunti_temp"] = appunti

    # ==========================================
    # 🎙️ INTERFACCIA REGISTRAZIONE AUDIO DEDICATA
    # ==========================================
    st.markdown("🎙️ **Registrazione Audio Pensieri:**")
    
    # Widget Registratore (SfondoScuro + Colori Verde/Rosso)
    audio_bytes_appunti = audio_recorder(
        text="Usa i comandi sottostanti per registrare",
        icon_size="2x",
        neutral_color="#2ECC71",   # Verde in Pausa/Pronto
        recording_color="#E74C3C", # Rosso durante RECORD
        key="rec_appunti",
    )

    # Tasti di Comando: RECORD / STOP & TRASCRIVI / CANCELLA
    col_rec1, col_rec2, col_rec3 = st.columns([1, 1.3, 1])
    
    with col_rec1:
        st.info("🔴 **RECORD**\n(Clicca sul microfono sopra per avviare)")
        
    with col_rec2:
        if audio_bytes_appunti:
            if st.button("⏹️ STOP & TRASCRIVI", type="primary", use_container_width=True, key="btn_stop_appunti"):
                if client:
                    with st.spinner("🎧 Trascrizione veloce in corso con Whisper..."):
                        try:
                            temp_path = "temp_audio_pensieri.wav"
                            with open(temp_path, "wb") as f:
                                f.write(audio_bytes_appunti)
                            
                            with open(temp_path, "rb") as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="it"
                                )
                            
                            st.session_state["appunti_voce_o_file"] = transcript.text
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            
                            st.toast("✅ Vocale trascritto nei pensieri!", icon="🎙️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore trascrizione audio: {e}")
                else:
                    st.error("Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit.")
        else:
            st.button("⏹️ STOP", disabled=True, use_container_width=True, key="btn_stop_disabled")

    with col_rec3:
        if st.button("🗑️ CANCELLA", use_container_width=True, key="btn_del_appunti"):
            st.session_state["appunti_voce_o_file"] = ""
            st.toast("🗑️ Audio e testo cancellati!", icon="🧹")
            st.rerun()

    if audio_bytes_appunti:
        st.markdown("<span class='recording-status'>🔴 RECORDING EFFETTUATO - PRONTO PER LA TRASCRIZIONE</span>", unsafe_allow_html=True)

    st.divider()

    # Caricamento file .txt alternativo
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
    if st.button("🚀 TRASFORMA IN SCENA CON MOCCIA.IA", type="primary", use_container_width=True):
        if appunti:
            if client:
                with st.spinner("🤖 MOCCIA.IA sta elaborando la scena..."):
                    try:
                        info_p = ""
                        for nome, data in st.session_state["personaggi"].items():
                            if nome.lower() in appunti.lower():
                                info_p += f"\n--- PROFILO {nome.upper()} ---\nPROFILO: {data['profilo']}\n"
                                ricordi_passati = [
                                    f"NEL CAP {k}: {v}"
                                    for k, v in data.get("ricordi", {}).items()
                                ]
                                if ricordi_passati:
                                    info_p += "RICORDI PASSATI:\n" + "\n".join(ricordi_passati) + "\n"

                        prompt = f"Sei MOCCIA.IA, uno scrittore professionista di romanzi.\n{info_p}\nPensieri di Federico: {appunti}\nScrivi direttamente la scena in italiano in modo lungo, ricco di dettagli ed emozionante."

                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.session_state["scena_generata"] = response.choices[0].message.content
                        st.toast("✨ Scena generata con successo!", icon="🎬")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore generazione: {e}")
            else:
                st.error("Inserisci la tua OPENAI_API_KEY nei Secrets di Streamlit.")
        else:
            st.warning("Inserisci prima i pensieri di Federico!")
