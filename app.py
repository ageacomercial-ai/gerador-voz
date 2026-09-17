"""Gerador de Voz Neural pt-BR — texto -> áudio para narração.
Aba 1 (MP3 neural): edge-tts, vozes Microsoft, precisa internet.
Aba 2 (Voz Local): Piper TTS, offline, rápido.
Aba 3 (Clonar voz): voiceclonnx, clonagem local, grátis.
Uso: streamlit run app.py --server.port 8502
"""
import asyncio
import re
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st

BASE = Path(__file__).parent
SAIDA = BASE / "audios"
SAIDA.mkdir(exist_ok=True)
REFS = BASE / "vozes"
REFS.mkdir(exist_ok=True)

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden !important; height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    button[aria-label="Menu"] {display: none !important;}
    footer {display: none !important;}
    footer:has(a) {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    header[data-testid="stHeader"] {display: none !important;}
    div[data-testid="stSidebarContent"] hr {display: none !important;}
    a[href*="streamlit.io"] {display: none !important;}
    a[href*="github.com/streamlit"] {display: none !important;}
    [data-testid="stMarkdownContainer"] small {display: none !important;}
    div[data-testid="stApp"] > div:last-child {display: none !important;}
    #streamlit-menu-bar {display: none !important;}
    section[data-testid="stSidebar"] div[data-testid="stDecoration"] {display: none !important;}
    .streamlit-footer {display: none !important;}
</style>
<script>
function removeBranding() {
    document.querySelectorAll('footer, [data-testid="stFooter"], #MainMenu, [aria-label="menu"]').forEach(e => e.remove());
    document.querySelectorAll('a').forEach(a => {
        if (a.href && (a.href.includes('streamlit.io') || a.href.includes('github.com/streamlit'))) a.remove();
    });
    document.querySelectorAll('[class*="streamlit"]').forEach(e => {
        if (e.tagName === 'FOOTER' || e.textContent.includes('Streamlit')) e.remove();
    });
}
removeBranding();
setTimeout(removeBranding, 2000);
setTimeout(removeBranding, 5000);
</script>
""", unsafe_allow_html=True)

try:
    import edge_tts
    HAS_EDGE = True
except ImportError:
    HAS_EDGE = False

try:
    from piper import PiperVoice as _PiperVoice
    MODELOS_PIPER = sorted(
        (BASE / "modelos").glob("*.onnx")
    ) if (BASE / "modelos").exists() else []
    HAS_PIPER = len(MODELOS_PIPER) > 0
except ImportError:
    HAS_PIPER = False
    MODELOS_PIPER = []

try:
    from voiceclonnx import VoiceCloner as _VoiceCloner
    HAS_CLONE = True
except ImportError:
    HAS_CLONE = False

VOZES_FALLBACK = {
    "pt-BR-FranciscaNeural (Feminina jovem — vendas)": "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural (Masculina grave — autoridade)": "pt-BR-AntonioNeural",
    "pt-BR-BrendaNeural (Feminina suave)": "pt-BR-BrendaNeural",
    "pt-BR-DonatoNeural (Masculina jovem)": "pt-BR-DonatoNeural",
    "pt-BR-ElzaNeural (Feminina madura)": "pt-BR-ElzaNeural",
    "pt-BR-FabioNeural (Masculina comercial)": "pt-BR-FabioNeural",
    "pt-BR-GiovannaNeural (Feminina TikTok)": "pt-BR-GiovannaNeural",
    "pt-BR-HumbertoNeural (Masculina narrativa)": "pt-BR-HumbertoNeural",
    "pt-BR-JulioNeural (Masculina neutra)": "pt-BR-JulioNeural",
    "pt-BR-LeilaNeural (Feminina clara)": "pt-BR-LeilaNeural",
    "pt-BR-LeticiaNeural (Feminina doce)": "pt-BR-LeticiaNeural",
    "pt-BR-ManuelaNeural (Feminina infantil/animada)": "pt-BR-ManuelaNeural",
    "pt-BR-NicolauNeural (Masculina forte)": "pt-BR-NicolauNeural",
    "pt-BR-ValerioNeural (Masculina madura)": "pt-BR-ValerioNeural",
    "pt-BR-YaraNeural (Feminina marcante)": "pt-BR-YaraNeural",
}

ROTEIROS = {
    "📢 Vendas (Caligrafia)": "Resolve a tua letra em 14 dias. Vê o vídeo. Se gostares do método, o fascículo completo é teu por 2.950 Kwanzas. Toca no botão e começa hoje. Garantia de 14 dias, risco zero!",
    "🪝 Gancho TikTok (15s)": "Para tudo! Se a tua letra é feia, isto é para ti. Em 14 dias, nem vais reconhecer a tua escrita. Clica e descobre como!",
    "📚 Tom de aula": "Aula um. Pega na caneta de forma leve, sem apertar. Agora, desenha um traço lento, de cima para baixo. Respira. Repete cinco vezes. Muito bem.",
}

st.set_page_config(page_title="Gerador de Voz pt-BR", page_icon="🎙️", layout="centered")
st.title("🎙️ Gerador de Voz — Narração pt-BR")
st.caption("Texto → áudio · ideal para YouCut / CapCut / TikTok")

aba1, aba2, aba3 = st.tabs(["🎤 Voz Neural (MP3)", "⚡ Voz Local (Piper)", "🧬 Clonar Voz"])

# ================= ABA 1 — EDGE-TTS =================
with aba1:
    if not HAS_EDGE:
        st.error("❌ Biblioteca `edge-tts` não instalada.")
        st.info("Corre `instalar.bat` dentro da pasta `gerador-voz` e recarrega.")
        st.stop()

    with st.sidebar:
        st.header("⚙️ Voz e estilo")
        nome_voz = st.selectbox("🎤 Voz", list(VOZES_FALLBACK.keys()), index=0)
        voz = VOZES_FALLBACK[nome_voz]
        velocidade = st.slider("Velocidade", -30, 30, 0, 5, format="%d%%",
                               help="0% = normal. +10% ritmo TikTok, -10% tom de aula.")
        volume = st.slider("Volume", -30, 30, 0, 5, format="%d%%")
        tom = st.slider("Tom (pitch)", -20, 20, 0, 5, format="%dHz")
        pausa = st.selectbox("Pausas", ["Automática", "Mais pausada (aula)", "Direta (anúncio)"])
        st.divider()
        st.caption("Motor: edge-tts · Vozes neurais Microsoft · MP3 48kHz")

    texto = st.text_area("📝 Texto da narração", height=180,
                         placeholder="Escreve ou cola aqui o roteiro...")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📢 Vendas"):
            texto = ROTEIROS["📢 Vendas (Caligrafia)"]
    with c2:
        if st.button("🪝 Gancho"):
            texto = ROTEIROS["🪝 Gancho TikTok (15s)"]
    with c3:
        if st.button("📚 Aula"):
            texto = ROTEIROS["📚 Tom de aula"]

    if texto:
        st.session_state["_t"] = texto

    texto_final = st.session_state.get("_t", texto) or texto
    palavras = len(texto_final.strip().split()) if texto_final.strip() else 0
    st.caption(f"📊 {len(texto_final)} caracteres · {palavras} palavras · ~{round(palavras/2.5)}s de áudio")

    def preparar(texto: str, modo_pausa: str) -> str:
        t = re.sub(r"\s+", " ", texto).strip()
        if modo_pausa == "Mais pausada (aula)":
            t = re.sub(r"([.!?…])\s*", r"\1 ... ", t)
        elif modo_pausa == "Direta (anúncio)":
            t = re.sub(r"([.!?…])\s*", r"\1 ", t)
        else:
            t = re.sub(r"([.!?…])\s*", r"\1 ", t)
        return t

    def ssml_rate(v: int) -> str:
        return f"{'+' if v >= 0 else ''}{v}%"

    async def gerar_mp3(texto: str, voz: str, rate: int, vol: int, pitch: int, destino: Path):
        communicate = edge_tts.Communicate(
            texto,
            voice=voz,
            rate=ssml_rate(rate),
            volume=f"{'+' if vol >= 0 else ''}{vol}%",
            pitch=f"{'+' if pitch >= 0 else ''}{pitch}Hz",
        )
        await communicate.save(str(destino))

    if st.button("🎙️ GERAR ÁUDIO MP3", type="primary", use_container_width=True):
        if not texto_final.strip():
            st.warning("⚠️ Escreve primeiro o texto.")
            st.stop()
        if len(texto_final) > 8000:
            st.warning("⚠️ Texto muito longo (limite ~8000 caracteres). Divide em partes.")
            st.stop()
        pronto = preparar(texto_final, pausa)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", texto_final[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"{ts}_{nome}.mp3"
        with st.spinner("🎙️ A gerar voz neural... (precisa internet, ~5-15s)"):
            try:
                asyncio.run(gerar_mp3(pronto, voz, velocidade, volume, tom, out))
            except Exception as e:
                st.error(f"❌ Falha ao gerar: {e}")
                st.info("Verifica a internet e tenta de novo.")
                st.stop()
        st.success("✅ Áudio pronto!")
        st.audio(str(out), format="audio/mp3")
        with open(out, "rb") as f:
            st.download_button("⬇️ BAIXAR MP3 (usa no YouCut/CapCut)", f,
                               file_name=out.name, mime="audio/mpeg",
                               use_container_width=True)
        st.caption(f"📁 Guardado em: gerador-voz/audios/{out.name}")

    st.divider()
    st.subheader("📁 Últimos áudios")
    mp3s = sorted(SAIDA.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if not mp3s:
        st.caption("Ainda sem áudios. Gera o primeiro acima. 👆")
    for m in mp3s:
        with st.expander(f"🔊 {m.name}"):
            st.audio(str(m), format="audio/mp3")
            with open(m, "rb") as f:
                st.download_button("⬇️ Baixar", f, file_name=m.name,
                                    mime="audio/mpeg", key=f"dl_{m.name}")

# ================= ABA 2 — PIPER TTS =================
with aba2:
    st.subheader("⚡ Voz Local — Piper TTS")
    st.caption("Motor offline, rápido, sem precisar de internet · vozes pt-BR")

    if not HAS_PIPER:
        st.error("❌ Piper não encontrado.")
        st.info("Corre `pip install piper-tts` e descarrega modelos para a pasta `modelos/`.")
        st.stop()

    nomes_modelos = [m.stem.replace("pt_BR-", "").replace("-", " ").title() for m in MODELOS_PIPER]
    escolha_idx = st.selectbox("🎤 Escolhe a voz", range(len(nomes_modelos)),
                               format_func=lambda i: nomes_modelos[i])
    modelo_path = MODELOS_PIPER[escolha_idx]
    st.caption(f"Modelo: `{modelo_path.name}`")

    @st.cache_resource(show_spinner=False)
    def carregar_piper(path):
        from piper import PiperVoice
        return PiperVoice.load(str(path))

    texto_piper = st.text_area("📝 Texto da narração", height=180, key="texto_piper",
                               placeholder="Escreve ou cola aqui o roteiro...")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📢 Vendas", key="piper_vendas"):
            st.session_state["texto_piper"] = ROTEIROS["📢 Vendas (Caligrafia)"]
    with c2:
        if st.button("🪝 Gancho", key="piper_gancho"):
            st.session_state["texto_piper"] = ROTEIROS["🪝 Gancho TikTok (15s)"]
    with c3:
        if st.button("📚 Aula", key="piper_aula"):
            st.session_state["texto_piper"] = ROTEIROS["📚 Tom de aula"]

    texto_piper = st.session_state.get("texto_piper", texto_piper) or ""
    palavras_p = len(texto_piper.strip().split()) if texto_piper.strip() else 0
    st.caption(f"📊 {len(texto_piper)} caracteres · {palavras_p} palavras · ~{round(palavras_p/2.5)}s")

    if st.button("⚡ GERAR WAV (offline)", type="primary", use_container_width=True, key="piper_gerar"):
        t = texto_piper.strip()
        if not t:
            st.warning("⚠️ Escreve primeiro o texto.")
            st.stop()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", t[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"piper_{ts}_{nome}.wav"
        with st.spinner("⚡ A gerar áudio local... (rápido, sem internet)"):
            try:
                pv = carregar_piper(modelo_path)
                with wave.open(str(out), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(pv.config.sample_rate)
                    for chunk in pv.synthesize(t):
                        audio_int = np.int16(chunk.audio_float_array * 32767)
                        wf.writeframes(audio_int.tobytes())
            except Exception as e:
                st.error(f"❌ Falha: {e}")
                st.stop()
        st.success("✅ Áudio pronto!")
        st.audio(str(out), format="audio/wav")
        with open(out, "rb") as f:
            st.download_button("⬇️ BAIXAR WAV", f, file_name=out.name,
                               mime="audio/wav", use_container_width=True)
        st.caption(f"📁 Guardado em: gerador-voz/audios/{out.name}")

# ================= ABA 3 — CLONAGEM DE VOZ =================
with aba3:
    st.subheader("🧬 Clonar uma voz")
    st.caption("Motor: voiceclonnx (triaan) · local, grátis, sem compilar · modelos baixam no 1º uso")

    if not HAS_CLONE:
        st.error("❌ `voiceclonnx` não instalado.")
        st.info("Corre: `pip install voiceclonnx` e recarrega.")
        st.stop()

    st.info("🎤 Grava ou envia 5-30 segundos de voz limpa (sem música/ruído) como referência.")
    st.info("⚡ O motor **triaan** é rápido e leve neste PC.")

    @st.cache_resource(show_spinner=False)
    def carregar_cloner():
        from voiceclonnx import VoiceCloner
        return VoiceCloner(engine="triaan")

    refs_guardadas = sorted(REFS.glob("*.wav")) + sorted(REFS.glob("*.mp3"))
    opcoes = ["— Enviar novo áudio —"] + [r.name for r in refs_guardadas]
    escolha = st.selectbox("🎤 Voz de referência", opcoes)

    ref_path = None
    if escolha == "— Enviar novo áudio —":
        metodo = st.radio("Como obter o áudio?", ["🎙️ Gravar agora", "📁 Enviar ficheiro"],
                          horizontal=True, key="metodo_ref")

        if metodo == "🎙️ Gravar agora":
            st.markdown("**Grava 5-30 segundos da tua voz.** Fala perto do microfone, sem ruído.")
            import streamlit.components.v1 as components
            RECORDER_HTML = """
            <div id="recorder" style="text-align:center;padding:10px;">
              <button id="btnRec" style="font-size:16px;padding:10px 24px;border:none;border-radius:10px;background:#ff4444;color:#fff;cursor:pointer;margin:4px;">🎙️ Gravar</button>
              <button id="btnStop" style="font-size:16px;padding:10px 24px;border:none;border-radius:10px;background:#444;color:#fff;cursor:pointer;margin:4px;" disabled>⏹ Parar</button>
              <p id="status" style="font-size:13px;color:#888;margin:8px 0;">Pronto para gravar</p>
              <audio id="player" controls style="width:100%;display:none;margin-top:8px;"></audio>
              <br>
              <a id="download" style="display:none;margin-top:8px;font-size:13px;"></a>
            </div>
            <script>
            let mediaRecorder, chunks=[], blob, audioB64='';
            const btnRec=document.getElementById('btnRec');
            const btnStop=document.getElementById('btnStop');
            const status=document.getElementById('status');
            const player=document.getElementById('player');
            const download=document.getElementById('download');
            btnRec.onclick=async()=>{
              try{
                const stream=await navigator.mediaDevices.getUserMedia({audio:true});
                mediaRecorder=new MediaRecorder(stream);
                chunks=[];
                mediaRecorder.ondataavailable=e=>chunks.push(e.data);
                mediaRecorder.onstop=()=>{
                  blob=new Blob(chunks,{type:'audio/webm'});
                  const url=URL.createObjectURL(blob);
                  player.src=url;
                  player.style.display='block';
                  stream.getTracks().forEach(t=>t.stop());
                  status.textContent='✅ Gravado! A converter...';
                  const reader=new FileReader();
                  reader.onload=()=>{
                    const arr=new Uint8Array(reader.result);
                    let binary='';
                    for(let i=0;i<arr.byteLength;i++) binary+=String.fromCharCode(arr[i]);
                    audioB64=btoa(binary);
                    window.parent.postMessage({type:'audio_recorded',data:audioB64.length>0},'*');
                    status.textContent='✅ Pronto! Clica em GUARDAR em baixo.';
                    download.textContent='💾 Descarregar gravação';
                    download.href=url;
                    download.download='gravacao.webm';
                    download.style.display='inline';
                  };
                  reader.readAsArrayBuffer(blob);
                };
                mediaRecorder.start();
                btnRec.disabled=true;
                btnStop.disabled=false;
                btnRec.style.background='#888';
                btnStop.style.background='#ff4444';
                status.textContent='🔴 A gravar... fala agora!';
              }catch(err){status.textContent='❌ Microfone negado. Autoriza no navegador.';}
            };
            btnStop.onclick=()=>{mediaRecorder.stop();btnRec.disabled=false;btnStop.disabled=true;btnRec.style.background='#ff4444';btnStop.style.background='#888';};
            </script>
            """
            components.html(RECORDER_HTML, height=180)

            uploaded_rec = st.file_uploader(
                "📥 Ou carrega aqui o áudio gravado:",
                type=["wav", "mp3", "webm", "ogg"], key="rec_upload"
            )
            if uploaded_rec is not None:
                tmp_raw = REFS / f"tmp_raw_{uploaded_rec.name}"
                tmp_raw.write_bytes(uploaded_rec.getbuffer())

                ext = uploaded_rec.name.rsplit(".", 1)[-1].lower()
                if ext in ("webm", "ogg"):
                    tmp = REFS / f"tmp_converted.wav"
                    try:
                        import imageio_ffmpeg
                        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
                        import subprocess
                        subprocess.run([
                            ffmpeg_bin, "-y", "-i", str(tmp_raw),
                            "-ar", "22050", "-ac", "1", "-f", "wav", str(tmp)
                        ], capture_output=True, check=True)
                        st.success("✅ WebM convertido para WAV!")
                    except Exception as e:
                        st.error(f"❌ Falha ao converter: {e}")
                        st.stop()
                else:
                    tmp = tmp_raw

                st.audio(str(tmp))
                if st.button("💾 Guardar como minha voz", key="btn_save_rec"):
                    final = REFS / "minha_voz.wav"
                    try:
                        import soundfile as sf
                        data, sr = sf.read(str(tmp))
                        if len(data.shape) > 1:
                            data = data.mean(axis=1)
                        sf.write(str(final), data, sr, subtype="PCM_16")
                        st.success(f"✅ Guardada como {final.name}. Atualiza a lista acima.")
                    except Exception as e:
                        st.error(f"❌ Falha ao guardar: {e}")
                ref_path = tmp
        else:
            up = st.file_uploader("Envia 5 a 30s de voz limpa (WAV ideal, sem música/ruído)",
                                  type=["wav", "mp3"])
            if up is not None:
                tmp = REFS / f"tmp_{up.name}"
                tmp.write_bytes(up.getbuffer())
                st.audio(str(tmp))
                if st.button("💾 Guardar como minha voz"):
                    final = REFS / "minha_voz.wav"
                    try:
                        import soundfile as sf
                        data, sr = sf.read(str(tmp))
                        if len(data.shape) > 1:
                            data = data.mean(axis=1)
                        sf.write(str(final), data, sr, subtype="PCM_16")
                        st.success(f"✅ Guardada como {final.name}. Escolhe ela na lista acima.")
                    except Exception as e:
                        st.error(f"❌ Falha ao guardar: {e}")
                ref_path = tmp
    else:
        ref_path = REFS / escolha
        st.audio(str(ref_path))

    texto_clone = st.text_area("📝 Texto para a voz clonada", height=120,
                               placeholder="Ex: Resolve a tua letra em 14 dias...",
                               key="texto_clone")

    if st.button("🧬 GERAR VOZ CLONADA", type="primary", use_container_width=True, key="btn_clone"):
        if ref_path is None or not ref_path.exists():
            st.warning("⚠️ Primeiro envia ou escolhe o áudio de referência.")
            st.stop()
        t = re.sub(r"\s+", " ", (texto_clone or "")).strip()
        if not t:
            st.warning("⚠️ Escreve o texto.")
            st.stop()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = SAIDA / f"clone_{ts}.wav"

        # Gera o áudio fonte com Piper primeiro
        piper_model = MODELOS_PIPER[0] if MODELOS_PIPER else None
        if piper_model is None:
            st.warning("⚠️ Nenhum modelo Piper encontrado para gerar a voz fonte.")
            st.stop()

        with st.spinner("⚡ 1/2: A gerar voz fonte (Piper)..."):
            try:
                from piper import PiperVoice
                import numpy as np
                pv = PiperVoice.load(str(piper_model))
                tmp_src = SAIDA / f"_src_{ts}.wav"
                with wave.open(str(tmp_src), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(pv.config.sample_rate)
                    for chunk in pv.synthesize(t):
                        audio_int = np.int16(chunk.audio_float_array * 32767)
                        wf.writeframes(audio_int.tobytes())
            except Exception as e:
                st.error(f"❌ Falha ao gerar voz fonte: {e}")
                st.stop()

        with st.spinner("🧬 2/2: A clonar voz (1ª vez baixa modelo, depois é rápido)..."):
            try:
                cloner = carregar_cloner()
                cloner.clone_voice(str(tmp_src), str(ref_path), str(out))
            except Exception as e:
                st.error(f"❌ Falha na clonagem: {e}")
                st.stop()

        st.success("✅ Voz clonada!")
        st.audio(str(out), format="audio/wav")
        with open(out, "rb") as f:
            st.download_button("⬇️ BAIXAR WAV (YouCut/CapCut aceitam)", f,
                               file_name=out.name, mime="audio/wav",
                               use_container_width=True)
        st.caption(f"📁 Guardado em: gerador-voz/audios/{out.name}")
