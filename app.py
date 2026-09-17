"""AGEA — Gerador de Voz Neural pt-BR"""
import asyncio
import re
from datetime import datetime
from pathlib import Path

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
    <span class="tag">15 vozes pt-BR · MP3 · Grátis</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="steps">
    <div class="step"><div class="n">1</div><div class="t">Escolhe a voz</div><div class="d">15 vozes femininas e masculinas</div></div>
    <div class="step"><div class="n">2</div><div class="t">Escreve o texto</div><div class="d">Cola o roteiro ou usa um modelo</div></div>
    <div class="step"><div class="n">3</div><div class="t">Gera e baixa</div><div class="d">Ouve, baixa o MP3 e usa no vídeo</div></div>
</div>
""", unsafe_allow_html=True)

if not HAS_EDGE:
    st.error("Biblioteca edge-tts não instalada.")
    st.stop()

# ─── 1. VOZ ─────────────────────────────────────────────────────────
st.subheader("1. Escolhe a voz")
nome_voz = st.selectbox("Voz", list(VOZES.keys()), index=0, key="voz_neural", label_visibility="collapsed")
voz = VOZES[nome_voz]
st.caption("Ouve a dica: Francisca para vendas, Antonio para autoridade, Giovanna para TikTok.")

st.divider()

# ─── 2. TEXTO ───────────────────────────────────────────────────────
st.subheader("2. Escreve o texto")
st.caption("Usa um modelo pronto ou escreve o teu roteiro. Máximo 8000 caracteres.")
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
    duracao = round(palavras / 2.5)
    st.markdown(f"""
    <div class="stats">
        <div class="stat"><div class="num">{len(texto_final)}</div><div class="label">caracteres</div></div>
        <div class="stat"><div class="num">{palavras}</div><div class="label">palavras</div></div>
        <div class="stat"><div class="num">~{duracao}s</div><div class="label">áudio</div></div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("👆 Escolhe um modelo acima ou escreve o teu texto para começar.")

st.divider()

# ─── 3. AJUSTES ─────────────────────────────────────────────────────
st.subheader("3. Ajusta (opcional)")
with st.expander("Velocidade, volume, tom e estilo", expanded=False):
    velocidade = st.slider("Velocidade", -30, 30, 0, 5, format="%+d%%", key="vel_neural",
                           help="+10% ritmo TikTok · -10% tom de aula")
    cv1, cv2 = st.columns(2)
    with cv1:
        volume = st.slider("Volume", -30, 30, 0, 5, format="%+d%%", key="vol_neural")
    with cv2:
        tom = st.slider("Tom", -20, 20, 0, 5, format="%+dHz", key="tom_neural")
    pausa = st.selectbox("Estilo de pausas", ["Automática", "Mais pausada (aula)", "Direta (anúncio)"], key="pausa_neural")

st.divider()

# ─── 4. GERAR ───────────────────────────────────────────────────────
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
        st.warning("Texto muito longo. Divide em partes de 8000 caracteres.")
        st.stop()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome = re.sub(r"[^\w\-]+", "_", texto_final[:30]).strip("_")[:30] or "narracao"
    out = SAIDA / f"{ts}_{nome}.mp3"
    with st.spinner("A gerar voz... 5 a 15 segundos."):
        try:
            asyncio.run(gerar_mp3(preparar(texto_final, pausa), voz, velocidade, volume, tom, out))
        except Exception as e:
            st.error(f"Falha: {e}. Verifica a internet e tenta de novo.")
            st.stop()
    st.success("Áudio pronto! Ouve abaixo e baixa.")
    st.audio(str(out), format="audio/mp3")
    with open(out, "rb") as f:
        st.download_button("⬇️ Baixar MP3", f, file_name=out.name, mime="audio/mpeg",
                           use_container_width=True, key="dl_mp3")
    st.caption("Guarda o MP3 no telemóvel ou PC para usar no editor de vídeo.")

st.divider()

# ─── COMO USAR ──────────────────────────────────────────────────────
st.subheader("Como usar no teu vídeo")
st.markdown("""
<div class="howto">
<h4>📱 CapCut / YouCut (telemóvel)</h4>
<ol>
<li>Baixa o MP3 aqui em cima.</li>
<li>Abre o CapCut → Novo projeto → importa o teu vídeo.</li>
<li>Toca em <b>Áudio → Sons → Do dispositivo</b> e escolhe o MP3.</li>
<li>Ajusta o volume e exporta.</li>
</ol>
</div>
<div class="howto">
<h4>🎬 TikTok / Reels / YouTube Shorts</h4>
<ul>
<li>Textos curtos (até 300 caracteres) funcionam melhor.</li>
<li>Usa velocidade <b>+10%</b> para ritmo rápido.</li>
<li> Voz <b>Giovanna</b> ou <b>Francisca</b> para prender atenção.</li>
</ul>
</div>
""", unsafe_allow_html=True)

with st.expander("💡 Dicas para uma narração perfeita"):
    st.markdown("""
- **Frases curtas** soam mais naturais. Evita parágrafos longos.
- **Pontuação importa:** vírgulas e pontos criam pausas reais.
- **Números e preços:** escreve por extenso se a voz ler mal (ex: "dois mil novecentos e cinquenta").
- **Testa 2 vozes** antes de decidir. A mesma frase muda muito de voz para voz.
- **Divide roteiros longos** em partes e gera um MP3 por parte.
    """)

st.divider()

# ─── HISTÓRICO ──────────────────────────────────────────────────────
st.subheader("Os teus últimos áudios")
mp3s = sorted(SAIDA.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
if not mp3s:
    st.caption("Ainda não geraste nenhum áudio nesta sessão. O primeiro aparece aqui.")
for m in mp3s:
    with st.expander(f"🔊 {m.name}"):
        st.audio(str(m), format="audio/mp3")
        with open(m, "rb") as f:
            st.download_button("Baixar", f, file_name=m.name, mime="audio/mpeg", key=f"dl_{m.name}")

st.markdown("""
<div class="footer-minimal">
    AGEA Voz · Narração profissional em pt-BR · Feito para criadores
</div>
""", unsafe_allow_html=True)
