"""AGEA — Gerador de Voz Neural pt-BR (online + offline)"""
import asyncio
import re
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st

st.set_page_config(page_title="AGEA — Gerador de Voz", page_icon="🎙️", layout="centered", initial_sidebar_state="collapsed")

BASE = Path(__file__).parent
SAIDA = BASE / "audios"
SAIDA.mkdir(exist_ok=True)

if "tema" not in st.session_state:
    st.session_state["tema"] = "Claro"

_top_l, _top_r = st.columns([5, 1])
with _top_r:
    escuro = st.toggle("🌙", value=(st.session_state["tema"] == "Escuro"), key="toggle_tema",
                       help="Modo escuro / claro")
    st.session_state["tema"] = "Escuro" if escuro else "Claro"

DARK = st.session_state["tema"] == "Escuro"
C = {
    "bg": "#0f1113" if DARK else "#ffffff",
    "surface": "#1a1d21" if DARK else "#f8f9fa",
    "surface2": "#24282e" if DARK else "#eef1f4",
    "border": "#33373d" if DARK else "#dee2e6",
    "text": "#f1f3f4" if DARK else "#202124",
    "text2": "#9aa0a6" if DARK else "#5f6368",
    "accent": "#8ab4f8" if DARK else "#1a73e8",
}

# ─── CSS ────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
:root {{
    --bg: {C["bg"]};
    --surface: {C["surface"]};
    --surface2: {C["surface2"]};
    --border: {C["border"]};
    --text: {C["text"]};
    --text2: {C["text2"]};
    --accent: {C["accent"]};
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', -apple-system, sans-serif !important; }
.stApp { background: var(--bg) !important; color: var(--text) !important; }
.block-container { padding-top: 2rem !important; max-width: 720px !important; padding-bottom: 4rem !important; }
#MainMenu, footer, header, .stDeployButton,
div[data-testid="stToolbar"], div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"], button[aria-label="Menu"],
header[data-testid="stHeader"], .streamlit-footer
{display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden;}
a[href*="streamlit.io"], a[href*="github.com/streamlit"] {display: none !important;}
h1, h2, h3, h4 { color: var(--text) !important; font-weight: 600 !important; }
.brand { text-align: center; padding: 1.5rem 0 0.5rem; }
.brand h1 { font-size: 2.2rem !important; font-weight: 700 !important; color: var(--text) !important; margin-bottom: 0.2rem; }
.brand p { color: var(--text2); font-size: 1rem; }
.brand .tag { display: inline-block; background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; padding: 4px 14px; font-size: 0.75rem; color: var(--accent); margin-top: 8px; }
.steps { display: flex; gap: 10px; margin: 1.2rem 0; }
.step { flex: 1; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 14px 12px; text-align: center; }
.step .n { display: inline-block; width: 26px; height: 26px; line-height: 26px; border-radius: 50%; background: var(--accent); color: #fff; font-weight: 700; font-size: 0.85rem; margin-bottom: 6px; }
.step .t { font-weight: 600; font-size: 0.85rem; color: var(--text); }
.step .d { font-size: 0.78rem; color: var(--text2); margin-top: 2px; }
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 12px !important; padding: 4px !important; gap: 4px !important; border: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { border-radius: 10px !important; color: var(--text2) !important; font-weight: 500 !important; }
.stTabs [aria-selected="true"] { background: var(--accent) !important; color: white !important; }
.stTextArea textarea { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; color: var(--text) !important; font-size: 0.95rem !important; }
.stTextArea textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(26,115,232,0.15) !important; }
.stTextArea label, .stSelectbox label, .stSlider label { color: var(--text2) !important; font-weight: 500 !important; font-size: 0.85rem !important; }
.stButton > button { background: var(--surface) !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; font-weight: 500 !important; padding: 0.6rem 1.2rem !important; }
.stButton > button:hover { border-color: var(--accent) !important; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background: var(--accent) !important; color: white !important; border: none !important; font-weight: 600 !important; padding: 0.75rem 2rem !important; }
.stInfo, .stSuccess, .stWarning, .stError { border-radius: 12px !important; }
hr { border-color: var(--border) !important; opacity: 0.4 !important; }
audio { border-radius: 12px !important; width: 100%; }
.streamlit-expanderHeader { background: var(--surface) !important; border-radius: 12px !important; border: 1px solid var(--border) !important; }
.stCaption, p { color: var(--text2) !important; }
.stats { display: flex; gap: 10px; justify-content: center; padding: 8px 0; }
.stat { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 8px 16px; text-align: center; }
.stat .num { font-size: 1.1rem; font-weight: 600; color: var(--accent); }
.stat .label { font-size: 0.7rem; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; }
.howto { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; margin: 10px 0; }
.howto h4 { margin: 0 0 6px 0; font-size: 0.95rem; }
.howto ol, .howto ul { margin: 6px 0 0 18px; padding: 0; color: var(--text); font-size: 0.9rem; }
.howto li { margin-bottom: 4px; }
.footer-minimal { text-align: center; padding: 2rem 0 1rem; color: var(--text2); font-size: 0.75rem; opacity: 0.6; }
</style>
<script>
function hideBranding() {
    document.querySelectorAll('footer, [data-testid="stFooter"], #MainMenu, [aria-label="menu"]').forEach(e => e.remove());
    document.querySelectorAll('a').forEach(a => {
        if (a.href && (a.href.includes('streamlit.io') || a.href.includes('github.com/streamlit'))) a.remove();
    });
}
hideBranding(); setTimeout(hideBranding, 2000); setTimeout(hideBranding, 5000);
</script>
""", unsafe_allow_html=True)

try:
    import edge_tts
    HAS_EDGE = True
except ImportError:
    HAS_EDGE = False

try:
    from piper import PiperVoice as _PiperVoice
    MODELOS_PIPER = sorted((BASE / "modelos").glob("*.onnx")) if (BASE / "modelos").exists() else []
    HAS_PIPER = len(MODELOS_PIPER) > 0
except ImportError:
    HAS_PIPER = False
    MODELOS_PIPER = []

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

# ─── HEADER ─────────────────────────────────────────────────────────
st.markdown("""
<div class="brand">
    <h1>🎙️ AGEA Voz</h1>
    <p>Transforma texto em narração profissional em português.<br>Ideal para TikTok, Reels, YouTube, anúncios e aulas.</p>
    <span class="tag">15 vozes pt-BR · Online e Offline · Grátis</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="steps">
    <div class="step"><div class="n">1</div><div class="t">Escolhe a voz</div><div class="d">Online ou offline</div></div>
    <div class="step"><div class="n">2</div><div class="t">Escreve o texto</div><div class="d">Usa um modelo ou o teu roteiro</div></div>
    <div class="step"><div class="n">3</div><div class="t">Gera e baixa</div><div class="d">MP3 ou WAV para o vídeo</div></div>
</div>
""", unsafe_allow_html=True)

tab_online, tab_offline = st.tabs(["🌐 Online (15 vozes)", "💻 Offline (sem rede)"])

# ═══════════════ ONLINE — EDGE TTS ═══════════════
with tab_online:
    if not HAS_EDGE:
        st.error("Biblioteca edge-tts não instalada.")
        st.stop()

    st.caption("Precisa de internet. Melhor qualidade, 15 vozes.")

    st.subheader("1. Escolhe a voz")
    nome_voz = st.selectbox("Voz", list(VOZES.keys()), index=0, key="voz_neural", label_visibility="collapsed")
    voz = VOZES[nome_voz]
    st.caption("Dica: Francisca para vendas, Antonio para autoridade, Giovanna para TikTok.")

    st.divider()
    st.subheader("2. Escreve o texto")
    m1, m2, m3 = st.columns(3)
    with m1:
        if st.button("📢 Vendas", key="r1", use_container_width=True):
            st.session_state["_t"] = ROTEIROS["Vendas"]
    with m2:
        if st.button("🪝 Gancho TikTok", key="r2", use_container_width=True):
            st.session_state["_t"] = ROTEIROS["Gancho TikTok"]
    with m3:
        if st.button("📚 Aula", key="r3", use_container_width=True):
            st.session_state["_t"] = ROTEIROS["Aula"]

    texto = st.text_area("Texto", height=170, key="_t", label_visibility="collapsed",
                         placeholder="Ex: Resolve a tua letra em 14 dias. Toca no botão e começa hoje...")
    texto_final = texto or ""
    palavras = len(texto_final.strip().split()) if texto_final.strip() else 0
    if palavras > 0:
        st.markdown(f"""
        <div class="stats">
            <div class="stat"><div class="num">{len(texto_final)}</div><div class="label">caracteres</div></div>
            <div class="stat"><div class="num">{palavras}</div><div class="label">palavras</div></div>
            <div class="stat"><div class="num">~{round(palavras / 2.5)}s</div><div class="label">áudio</div></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👆 Escolhe um modelo acima ou escreve o teu texto.")

    st.divider()
    st.subheader("3. Ajusta (opcional)")
    with st.expander("Velocidade, volume, tom e estilo", expanded=False):
        velocidade = st.slider("Velocidade", -30, 30, 0, 5, format="%+d%%", key="vel_neural")
        cv1, cv2 = st.columns(2)
        with cv1:
            volume = st.slider("Volume", -30, 30, 0, 5, format="%+d%%", key="vol_neural")
        with cv2:
            tom = st.slider("Tom", -20, 20, 0, 5, format="%+dHz", key="tom_neural")
        pausa = st.selectbox("Estilo de pausas", ["Automática", "Mais pausada (aula)", "Direta (anúncio)"], key="pausa_neural")

    st.divider()
    st.subheader("4. Gera o áudio")

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

    if st.button("🎙️ Gerar Áudio MP3", type="primary", use_container_width=True, key="btn_mp3"):
        if not texto_final.strip():
            st.warning("Escreve o texto primeiro (passo 2).")
            st.stop()
        if len(texto_final) > 8000:
            st.warning("Texto muito longo. Divide em partes.")
            st.stop()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", texto_final[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"{ts}_{nome}.mp3"
        with st.spinner("A gerar voz... 5 a 15 segundos."):
            ok, ultimo_erro = False, None
            for tentativa in range(1, 4):
                try:
                    asyncio.run(gerar_mp3(preparar(texto_final, pausa), voz, velocidade, volume, tom, out))
                    ok = True
                    break
                except Exception as e:
                    ultimo_erro = e
                    if tentativa < 3:
                        import time
                        time.sleep(2)
            if not ok:
                st.error(f"Falha: {ultimo_erro}. Sem internet? Usa a aba Offline.")
                st.stop()
        st.success("Áudio pronto!")
        st.audio(str(out), format="audio/mp3")
        with open(out, "rb") as f:
            st.download_button("⬇️ Baixar MP3", f, file_name=out.name, mime="audio/mpeg",
                               use_container_width=True, key="dl_mp3")

# ═══════════════ OFFLINE — PIPER ═══════════════
with tab_offline:
    st.caption("Funciona sem internet. Usa o modelo guardado no PC.")
    if not HAS_PIPER:
        st.warning("Modelo offline não encontrado neste ambiente.")
        st.info("No PC local: coloca o ficheiro `.onnx` na pasta `gerador-voz/modelos/` e instala com `pip install piper-tts`. Na web esta aba fica indisponível.")
        st.stop()

    nomes = [m.stem.replace("pt_BR-", "").replace("-", " ").title() for m in MODELOS_PIPER]
    st.subheader("1. Escolhe a voz offline")
    idx = st.selectbox("Voz local", range(len(nomes)), format_func=lambda i: nomes[i], key="voz_piper",
                       label_visibility="collapsed")
    modelo = MODELOS_PIPER[idx]

    @st.cache_resource(show_spinner=False)
    def load_piper(path):
        from piper import PiperVoice
        return PiperVoice.load(str(path))

    st.divider()
    st.subheader("2. Escreve o texto")
    o1, o2, o3 = st.columns(3)
    with o1:
        if st.button("📢 Vendas", key="p1", use_container_width=True):
            st.session_state["tp"] = ROTEIROS["Vendas"]
    with o2:
        if st.button("🪝 Gancho", key="p2", use_container_width=True):
            st.session_state["tp"] = ROTEIROS["Gancho TikTok"]
    with o3:
        if st.button("📚 Aula", key="p3", use_container_width=True):
            st.session_state["tp"] = ROTEIROS["Aula"]

    texto_p = st.text_area("Texto", height=170, key="tp", label_visibility="collapsed",
                           placeholder="Escreve aqui... funciona sem internet.") or ""
    pp = len(texto_p.strip().split()) if texto_p.strip() else 0
    if pp > 0:
        st.caption(f"{len(texto_p)} caracteres · {pp} palavras · ~{round(pp / 2.5)}s")

    st.divider()
    st.subheader("3. Gera o áudio")
    if st.button("💻 Gerar WAV Offline", type="primary", use_container_width=True, key="btn_piper"):
        t = texto_p.strip()
        if not t:
            st.warning("Escreve o texto.")
            st.stop()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = re.sub(r"[^\w\-]+", "_", t[:30]).strip("_")[:30] or "narracao"
        out = SAIDA / f"offline_{ts}_{nome}.wav"
        with st.spinner("A gerar offline..."):
            try:
                pv = load_piper(modelo)
                with wave.open(str(out), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(pv.config.sample_rate)
                    for chunk in pv.synthesize(t):
                        wf.writeframes(np.int16(chunk.audio_float_array * 32767).tobytes())
            except Exception as e:
                st.error(f"Falha: {e}")
                st.stop()
        st.success("Áudio pronto!")
        st.audio(str(out), format="audio/wav")
        with open(out, "rb") as f:
            st.download_button("⬇️ Baixar WAV", f, file_name=out.name, mime="audio/wav",
                               use_container_width=True, key="dl_piper")

st.divider()

# ─── COMO USAR ──────────────────────────────────────────────────────
st.subheader("Como usar no teu vídeo")
st.markdown("""
<div class="howto">
<h4>📱 CapCut / YouCut (telemóvel)</h4>
<ol>
<li>Baixa o MP3/WAV aqui em cima.</li>
<li>Abre o CapCut → Novo projeto → importa o teu vídeo.</li>
<li>Toca em <b>Áudio → Sons → Do dispositivo</b> e escolhe o ficheiro.</li>
<li>Ajusta o volume e exporta.</li>
</ol>
</div>
<div class="howto">
<h4>🎬 TikTok / Reels / YouTube Shorts</h4>
<ul>
<li>Textos curtos (até 300 caracteres) funcionam melhor.</li>
<li>Usa velocidade <b>+10%</b> para ritmo rápido.</li>
<li>Voz <b>Giovanna</b> ou <b>Francisca</b> para prender atenção.</li>
</ul>
</div>
""", unsafe_allow_html=True)

with st.expander("💡 Dicas para uma narração perfeita"):
    st.markdown("""
- **Frases curtas** soam mais naturais. Evita parágrafos longos.
- **Pontuação importa:** vírgulas e pontos criam pausas reais.
- **Números e preços:** escreve por extenso se a voz ler mal (ex: "dois mil novecentos e cinquenta").
- **Testa 2 vozes** antes de decidir.
- **Divide roteiros longos** em partes.
    """)

st.divider()

# ─── HISTÓRICO ──────────────────────────────────────────────────────
st.subheader("Os teus últimos áudios")
ficheiros = sorted(list(SAIDA.glob("*.mp3")) + list(SAIDA.glob("*.wav")),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:5]
if not ficheiros:
    st.caption("Ainda não geraste nenhum áudio. O primeiro aparece aqui.")
for m in ficheiros:
    fmt = "audio/mp3" if m.suffix == ".mp3" else "audio/wav"
    with st.expander(f"🔊 {m.name}"):
        st.audio(str(m), format=fmt)
        with open(m, "rb") as f:
            st.download_button("Baixar", f, file_name=m.name,
                               mime="audio/mpeg" if m.suffix == ".mp3" else "audio/wav",
                               key=f"dl_{m.name}")

st.markdown("""
<div class="footer-minimal">
    AGEA Voz · Narração profissional em pt-BR · Feito para criadores
</div>
""", unsafe_allow_html=True)
