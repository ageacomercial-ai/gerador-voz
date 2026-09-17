"""AGEA — Gerador de Voz Neural pt-BR"""
import asyncio
import re
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st

st.set_page_config(page_title="AGEA — Voz Neural", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

BASE = Path(__file__).parent
SAIDA = BASE / "audios"
SAIDA.mkdir(exist_ok=True)
REFS = BASE / "vozes"
REFS.mkdir(exist_ok=True)

# ─── CSS PROFISSIONAL ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg: #ffffff;
    --surface: #f8f9fa;
    --surface2: #eef1f4;
    --border: #dee2e6;
    --text: #202124;
    --text2: #5f6368;
    --accent: #1a73e8;
    --accent2: #1a73e8;
    --gradient: #1a73e8;
    --success: #188038;
    --error: #d93025;
}

* { font-family: 'Inter', -apple-system, sans-serif !important; }

.stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
}

.block-container {
    padding-top: 2rem !important;
    max-width: 720px !important;
    padding-bottom: 4rem !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header, .stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
button[aria-label="Menu"],
header[data-testid="stHeader"],
.streamlit-footer {display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden;}
a[href*="streamlit.io"], a[href*="github.com/streamlit"] {display: none !important;}

/* Typography */
h1, h2, h3, h4 { color: var(--text) !important; font-weight: 600 !important; }

/* Brand Header */
.brand {
    text-align: center;
    padding: 2rem 0 1rem;
}
.brand h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #202124 !important;
    letter-spacing: -0.5px;
    margin-bottom: 0.3rem;
}
.brand p {
    color: var(--text2);
    font-size: 0.95rem;
    font-weight: 300;
}
.brand .tag {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: var(--accent2);
    margin-top: 8px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    color: var(--text2) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 10px 16px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-accent {
    background: var(--surface);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* Inputs */
.stTextArea textarea, .stSelectbox div[data-baseweb="select"],
.stSlider div[data-baseweb="slider"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 12px !important;
}
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(26,115,232,0.15) !important;
}

/* Labels */
.stTextArea label, .stSelectbox label, .stSlider label,
.stRadio label, .stFileUploader label {
    color: var(--text2) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* Buttons */
.stButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    background: var(--surface2) !important;
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: #1a73e8 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* Quick buttons row */
.quick-btn {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: var(--text2);
    cursor: pointer;
    margin: 2px;
}
.quick-btn:hover {
    border-color: var(--accent);
    color: var(--accent2);
}

/* Info boxes */
.stInfo {
    background: var(--surface) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}
.stSuccess {
    background: var(--surface) !important;
    border: 1px solid var(--success) !important;
    border-radius: 12px !important;
}
.stWarning {
    background: var(--surface) !important;
    border: 1px solid #fdcb6e !important;
    border-radius: 12px !important;
}
.stError {
    background: var(--surface) !important;
    border: 1px solid var(--error) !important;
    border-radius: 12px !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
    opacity: 0.3 !important;
}

/* Audio player */
audio {
    border-radius: 12px !important;
}

/* Radio */
.stRadio > div {
    background: var(--surface) !important;
    border-radius: 12px !important;
    padding: 8px !important;
    border: 1px solid var(--border) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
}

/* Caption */
.stCaption, p { color: var(--text2) !important; }

/* Stats bar */
.stats {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding: 8px 0;
}
.stat {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 16px;
    text-align: center;
}
.stat .num {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent2);
}
.stat .label {
    font-size: 0.7rem;
    color: var(--text2);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Footer */
.footer-minimal {
    text-align: center;
    padding: 2rem 0 1rem;
    color: var(--text2);
    font-size: 0.75rem;
    opacity: 0.5;
}
</style>

<script>
function hideBranding() {
    document.querySelectorAll('footer, [data-testid="stFooter"], #MainMenu, [aria-label="menu"]').forEach(e => e.remove());
    document.querySelectorAll('a').forEach(a => {
        if (a.href && (a.href.includes('streamlit.io') || a.href.includes('github.com/streamlit'))) a.remove();
    });
}
hideBranding();
setTimeout(hideBranding, 2000);
setTimeout(hideBranding, 5000);
</script>
""", unsafe_allow_html=True)


# ─── IMPORTS ──────────────────────────────────────────────────────
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


# ─── DATA ─────────────────────────────────────────────────────────
VOZES = {
    "Francisca — Jovem, vendas": "pt-BR-FranciscaNeural",
    "Antonio — Grave, autoridade": "pt-BR-AntonioNeural",
    "Brenda — Suave": "pt-BR-BrendaNeural",
    "Donato — Jovem": "pt-BR-DonatoNeural",
    "Elza — Madura": "pt-BR-ElzaNeural",
    "Fabio — Comercial": "pt-BR-FabioNeural",
    "Giovanna — Animada": "pt-BR-GiovannaNeural",
    "Humberto — Narrativa": "pt-BR-HumbertoNeural",
    "Julio — Neutra": "pt-BR-JulioNeural",
    "Leila — Clara": "pt-BR-LeilaNeural",
    "Leticia — Doce": "pt-BR-LeticiaNeural",
    "Manuela — Infantil": "pt-BR-ManuelaNeural",
    "Nicolau — Forte": "pt-BR-NicolauNeural",
    "Valerio — Maduro": "pt-BR-ValerioNeural",
    "Yara — Marcante": "pt-BR-YaraNeural",
}

ROTEIROS = {
    "Vendas": "Resolve a tua letra em 14 dias. Vê o vídeo. Se gostares do método, o fascículo completo é teu por 2.950 Kwanzas. Toca no botão e começa hoje. Garantia de 14 dias, risco zero!",
    "Gancho TikTok": "Para tudo! Se a tua letra é feia, isto é para ti. Em 14 dias, nem vais reconhecer a tua escrita. Clica e descobre como!",
    "Aula": "Aula um. Pega na caneta de forma leve, sem apertar. Agora, desenha um traço lento, de cima para baixo. Respira. Repete cinco vezes. Muito bem.",
}


# ─── HEADER ───────────────────────────────────────────────────────
st.markdown("""
<div class="brand">
    <h1>⚡ AGEA</h1>
    <p>Gerador de Voz Neural — Narração profissional em português</p>
    <span class="tag">pt-BR · Inteligência Artificial · Gratuito</span>
</div>
""", unsafe_allow_html=True)


# ─── TABS ─────────────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["🎤 Neural", "⚡ Local", "🧬 Clonar"])


# ════════════════════════ ABA 1 — EDGE-TTS ════════════════════════
with aba1:
    if not HAS_EDGE:
        st.error("Biblioteca edge-tts não instalada.")
        st.stop()

    col1, col2 = st.columns([2, 1])
    with col1:
        nome_voz = st.selectbox("Voz", list(VOZES.keys()), index=0)
        voz = VOZES[nome_voz]
    with col2:
        velocidade = st.slider("Velocidade", -30, 30, 0, 5, format="%+d%%")

    col3, col4 = st.columns(2)
    with col3:
        volume = st.slider("Volume", -30, 30, 0, 5, format="%+d%%")
    with col4:
        tom = st.slider("Tom", -20, 20, 0, 5, format="%+dHz")

    pausa = st.selectbox("Estilo", ["Automática", "Mais pausada (aula)", "Direta (anúncio)"])

    texto = st.text_area("Texto da narração", height=160,
                         placeholder="Escreve ou cola aqui o roteiro...")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Vendas", key="r1"):
            st.session_state["_t"] = ROTEIROS["Vendas"]
    with c2:
        if st.button("Gancho", key="r2"):
            st.session_state["_t"] = ROTEIROS["Gancho TikTok"]
    with c3:
        if st.button("Aula", key="r3"):
            st.session_state["_t"] = ROTEIROS["Aula"]

    if "_t" in st.session_state and st.session_state["_t"]:
        texto = st.session_state["_t"]

    texto_final = texto or ""
    palavras = len(texto_final.strip().split()) if texto_final.strip() else 0

    if palavras > 0:
        duracao = round(palavras / 2.5)
        st.markdown(f"""
        <div class="stats">
            <div class="stat"><div class="num">{len(texto_final)}</div><div class="label">caracteres</div></div>
            <div class="stat"><div class="num">{palavras}</div><div class="label">palavras</div></div>
            <div class="stat"><div class="num">~{duracao}s</div><div class="label">duração</div></div>
        </div>
        """, unsafe_allow_html=True)

    def preparar(texto, modo):
        t = re.sub(r"\s+", " ", texto).strip()
        if modo == "Mais pausada (aula)":
            t = re.sub(r"([.!?…])\s*", r"\1 ... ", t)
        return t

    async def gerar_mp3(texto, voz, rate, vol, pitch, dest):
        comm = edge_tts.Communicate(texto, voice=voz,
                                    rate=f"{'+' if rate >= 0 else ''}{rate}%",
                                    volume=f"{'+' if vol >= 0 else ''}{vol}%",
                                    pitch=f"{'+' if pitch >= 0 else ''}{pitch}Hz")
        await comm.save(str(dest))

    if st.button("Gerar Áudio", type="primary", use_container_width=True, key="btn_mp3"):
        if not texto_final.strip():
            st.warning("Escreve o texto primeiro.")
            st.stop()
        if len(texto_final) > 8000:
            st.warning("Texto muito longo. Divide em partes.")
            st.stop()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", texto_final[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"{ts}_{nome}.mp3"

        with st.spinner("A gerar..."):
            try:
                asyncio.run(gerar_mp3(preparar(texto_final, pausa), voz, velocidade, volume, tom, out))
            except Exception as e:
                st.error(f"Falha: {e}")
                st.stop()

        st.success("Pronto!")
        st.audio(str(out), format="audio/mp3")
        with open(out, "rb") as f:
            st.download_button("Baixar MP3", f, file_name=out.name, mime="audio/mpeg",
                               use_container_width=True, key="dl_mp3")

    st.markdown("---")
    st.markdown("<p style='text-align:center;color:#5f6368;font-size:0.85rem;'>Últimos áudios</p>", unsafe_allow_html=True)
    mp3s = sorted(SAIDA.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if not mp3s:
        st.caption("Gera o primeiro áudio acima.")
    for m in mp3s:
        with st.expander(f"🔊 {m.name}"):
            st.audio(str(m), format="audio/mp3")
            with open(m, "rb") as f:
                st.download_button("Baixar", f, file_name=m.name, mime="audio/mpeg", key=f"dl_{m.name}")


# ════════════════════════ ABA 2 — PIPER ═══════════════════════════
with aba2:
    if not HAS_PIPER:
        st.error("Piper não instalado. Corre `pip install piper-tts`.")
        st.stop()

    st.markdown("""
    <div class="card">
        <p style="margin:0;color:#1a73e8;font-size:0.85rem;">⚡ Funciona offline — sem internet, sem limite</p>
    </div>
    """, unsafe_allow_html=True)

    nomes = [m.stem.replace("pt_BR-", "").replace("-", " ").title() for m in MODELOS_PIPER]
    idx = st.selectbox("Voz", range(len(nomes)), format_func=lambda i: nomes[i])
    modelo = MODELOS_PIPER[idx]

    @st.cache_resource(show_spinner=False)
    def load_piper(path):
        from piper import PiperVoice
        return PiperVoice.load(str(path))

    texto_p = st.text_area("Texto", height=160, key="tp", placeholder="Escreve aqui...")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Vendas", key="p1"):
            st.session_state["tp"] = ROTEIROS["Vendas"]
    with c2:
        if st.button("Gancho", key="p2"):
            st.session_state["tp"] = ROTEIROS["Gancho TikTok"]
    with c3:
        if st.button("Aula", key="p3"):
            st.session_state["tp"] = ROTEIROS["Aula"]

    texto_p = st.session_state.get("tp", "") or ""
    palavras_p = len(texto_p.strip().split()) if texto_p.strip() else 0
    if palavras_p > 0:
        st.caption(f"{len(texto_p)} caracteres · {palavras_p} palavras · ~{round(palavras_p/2.5)}s")

    if st.button("Gerar WAV", type="primary", use_container_width=True, key="btn_piper"):
        t = texto_p.strip()
        if not t:
            st.warning("Escreve o texto.")
            st.stop()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", t[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"piper_{ts}_{nome}.wav"

        with st.spinner("A gerar..."):
            try:
                pv = load_piper(modelo)
                with wave.open(str(out), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(pv.config.sample_rate)
                    for chunk in pv.synthesize(t):
                        audio_int = np.int16(chunk.audio_float_array * 32767)
                        wf.writeframes(audio_int.tobytes())
            except Exception as e:
                st.error(f"Falha: {e}")
                st.stop()

        st.success("Pronto!")
        st.audio(str(out), format="audio/wav")
        with open(out, "rb") as f:
            st.download_button("Baixar WAV", f, file_name=out.name, mime="audio/wav",
                               use_container_width=True, key="dl_piper")


# ════════════════════════ ABA 3 — CLONAR ══════════════════════════
with aba3:
    if not HAS_CLONE:
        st.error("voiceclonnx não instalado.")
        st.stop()

    st.markdown("""
    <div class="card">
        <p style="margin:0;color:#1a73e8;font-size:0.85rem;">🧬 Clona qualquer voz com 5-30 segundos de referência</p>
    </div>
    """, unsafe_allow_html=True)

    @st.cache_resource(show_spinner=False)
    def load_cloner():
        from voiceclonnx import VoiceCloner
        return VoiceCloner(engine="triaan")

    refs = sorted(REFS.glob("*.wav")) + sorted(REFS.glob("*.mp3"))
    opcoes = ["Enviar novo áudio"] + [r.name for r in refs]
    escolha = st.selectbox("Voz de referência", opcoes)

    ref_path = None
    if escolha == "Enviar novo áudio":
        metodo = st.radio("Método", ["Gravar agora", "Enviar ficheiro"], horizontal=True, key="metodo_ref")

        if metodo == "Gravar agora":
            import streamlit.components.v1 as components
            RECORDER_HTML = """
            <div style="text-align:center;padding:16px;background:#f8f9fa;border:1px solid #dee2e6;border-radius:16px;">
              <button id="btnRec" style="font-size:15px;padding:10px 28px;border:none;border-radius:10px;background:#1a73e8;color:#fff;cursor:pointer;font-weight:600;">🎙️ Gravar</button>
              <button id="btnStop" style="font-size:15px;padding:10px 28px;border:none;border-radius:10px;background:#dee2e6;color:#5f6368;cursor:pointer;font-weight:500;margin-left:8px;" disabled>⏹ Parar</button>
              <p id="status" style="font-size:13px;color:#5f6368;margin:12px 0 0;">Pronto para gravar</p>
              <audio id="player" controls style="width:100%;display:none;margin-top:12px;border-radius:10px;"></audio>
              <a id="download" style="display:none;margin-top:8px;font-size:13px;color:#1a73e8;"></a>
            </div>
            <script>
            let mr, chunks=[], blob;
            const b1=document.getElementById('btnRec'), b2=document.getElementById('btnStop'),
                  s=document.getElementById('status'), p=document.getElementById('player'),
                  d=document.getElementById('download');
            b1.onclick=async()=>{
              try{
                const stream=await navigator.mediaDevices.getUserMedia({audio:true});
                mr=new MediaRecorder(stream); chunks=[];
                mr.ondataavailable=e=>chunks.push(e.data);
                mr.onstop=()=>{
                  blob=new Blob(chunks,{type:'audio/webm'});
                  p.src=URL.createObjectURL(blob); p.style.display='block';
                  stream.getTracks().forEach(t=>t.stop());
                  s.textContent='✅ Gravado!';
                  d.textContent='💾 Descarregar'; d.href=p.src; d.download='gravacao.webm'; d.style.display='inline';
                };
                mr.start(); b1.disabled=true; b2.disabled=false;
                b1.style.background='#dee2e6'; b2.style.background='#1a73e8';
                s.textContent='🔴 A gravar...';
              }catch(e){s.textContent='❌ Microfone negado';}
            };
            b2.onclick=()=>{mr.stop();b1.disabled=false;b2.disabled=true;b1.style.background='#1a73e8';b2.style.background='#dee2e6';};
            </script>
            """
            components.html(RECORDER_HTML, height=180)

            uploaded = st.file_uploader("Ou carrega áudio", type=["wav", "mp3", "webm", "ogg"], key="rec_up")
            if uploaded:
                tmp_raw = REFS / f"tmp_{uploaded.name}"
                tmp_raw.write_bytes(uploaded.getbuffer())
                ext = uploaded.name.rsplit(".", 1)[-1].lower()
                if ext in ("webm", "ogg"):
                    tmp = REFS / "tmp_conv.wav"
                    try:
                        import imageio_ffmpeg, subprocess
                        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(tmp_raw),
                                        "-ar", "22050", "-ac", "1", "-f", "wav", str(tmp)],
                                       capture_output=True, check=True)
                    except Exception as e:
                        st.error(f"Erro: {e}"); st.stop()
                else:
                    tmp = tmp_raw
                st.audio(str(tmp))
                if st.button("Guardar voz", key="save_rec"):
                    final = REFS / "minha_voz.wav"
                    try:
                        import soundfile as sf
                        data, sr = sf.read(str(tmp))
                        if len(data.shape) > 1: data = data.mean(axis=1)
                        sf.write(str(final), data, sr, subtype="PCM_16")
                        st.success("Guardada! Atualiza a lista.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                ref_path = tmp
        else:
            up = st.file_uploader("Envia 5-30s de voz limpa", type=["wav", "mp3"])
            if up:
                tmp = REFS / f"tmp_{up.name}"
                tmp.write_bytes(up.getbuffer())
                st.audio(str(tmp))
                if st.button("Guardar voz"):
                    final = REFS / "minha_voz.wav"
                    try:
                        import soundfile as sf
                        data, sr = sf.read(str(tmp))
                        if len(data.shape) > 1: data = data.mean(axis=1)
                        sf.write(str(final), data, sr, subtype="PCM_16")
                        st.success("Guardada!")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                ref_path = tmp
    else:
        ref_path = REFS / escolha
        st.audio(str(ref_path))

    texto_clone = st.text_area("Texto para clonar", height=120, key="tc",
                               placeholder="Resolve a tua letra em 14 dias...")

    if st.button("Gerar Voz Clonada", type="primary", use_container_width=True, key="btn_clone"):
        if ref_path is None or not ref_path.exists():
            st.warning("Envia ou escolhe a referência.")
            st.stop()
        t = re.sub(r"\s+", " ", (texto_clone or "")).strip()
        if not t:
            st.warning("Escreve o texto.")
            st.stop()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = SAIDA / f"clone_{ts}.wav"
        piper_model = MODELOS_PIPER[0] if MODELOS_PIPER else None
        if not piper_model:
            st.warning("Modelo Piper necessário para voz fonte.")
            st.stop()

        with st.spinner("1/2 — A gerar voz fonte..."):
            try:
                from piper import PiperVoice
                pv = PiperVoice.load(str(piper_model))
                tmp_src = SAIDA / f"_src_{ts}.wav"
                with wave.open(str(tmp_src), "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(pv.config.sample_rate)
                    for chunk in pv.synthesize(t):
                        wf.writeframes(np.int16(chunk.audio_float_array * 32767).tobytes())
            except Exception as e:
                st.error(f"Falha: {e}"); st.stop()

        with st.spinner("2/2 — A clonar voz..."):
            try:
                cloner = load_cloner()
                cloner.clone_voice(str(tmp_src), str(ref_path), str(out))
            except Exception as e:
                st.error(f"Falha: {e}"); st.stop()

        st.success("Voz clonada!")
        st.audio(str(out), format="audio/wav")
        with open(out, "rb") as f:
            st.download_button("Baixar WAV", f, file_name=out.name, mime="audio/wav",
                               use_container_width=True, key="dl_clone")


# ─── FOOTER ───────────────────────────────────────────────────────
st.markdown("""
<div class="footer-minimal">
    AGEA · Voz Neural pt-BR · Powered by AI
</div>
""", unsafe_allow_html=True)
