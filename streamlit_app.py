
import os
import json
import re
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from docx import Document
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Orquestrador Pedagógico",
    page_icon="🎓",
    layout="wide",
)

# -----------------------------
# Aparência
# -----------------------------
st.markdown("""
<style>
    .block-container {max-width: 1200px; padding-top: 2rem; padding-bottom: 3rem;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .muted {color:#6b7280;}
    .status-ok {padding:.75rem 1rem; border:1px solid #d1fae5; border-radius:10px; background:#f0fdf4;}
    .status-warn {padding:.75rem 1rem; border:1px solid #fde68a; border-radius:10px; background:#fffbeb;}
    .fixed-box {padding:.9rem 1rem; border:1px solid #e5e7eb; border-radius:10px; background:#f9fafb;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utilidades
# -----------------------------
def extract_text(uploaded_file):
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                pass
        return "\n".join(parts)

    if name.endswith(".docx"):
        doc = Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)

    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="ignore")

    return ""

def compact_text(text, max_chars=60000):
    text = re.sub(r"\n{3,}", "\n\n", text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[DOCUMENTO TRUNCADO NO MVP]"

def clean_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)

def make_instruction(modelo, curso, disciplina, carga, creditos, etapa, docs):
    fontes_esperadas = (
        "matriz curricular, perfil do egresso, DCNs e matriz de referência do ENADE"
        if modelo == "UCA"
        else "matriz curricular, perfil do egresso e ementário"
    )

    docs_text = "\n\n".join(
        f"===== {label.upper()} =====\n{compact_text(content)}"
        for label, content in docs.items()
        if content.strip()
    )

    return f"""
Você é o núcleo interno de um Orquestrador Pedagógico para Ensino Superior.

TIPO: {modelo}
CURSO: {curso}
DISCIPLINA (IMUTÁVEL): {disciplina}
CARGA HORÁRIA (IMUTÁVEL): {carga}
CRÉDITOS (IMUTÁVEL): {creditos}
ETAPA/PERÍODO/TRIMESTRE: {etapa or "não informado"}

FONTES OBRIGATÓRIAS ESPERADAS:
{fontes_esperadas}

REGRAS ABSOLUTAS:
1. Não altere, corrija, traduza ou complete por inferência o nome da disciplina, a carga horária ou os créditos.
2. A disciplina deve ter EXATAMENTE 16 capítulos.
3. Os 16 capítulos devem formar uma progressão conceitual e cognitiva lógica; não podem ser 16 unidades independentes.
4. O título de cada capítulo deve ser específico. Proibidos títulos genéricos como "Introdução à disciplina", "Conceitos gerais", "Noções básicas" ou equivalentes.
5. O sumário expandido de cada capítulo deve ser um parágrafo em texto corrido, articulando conceitos centrais, teoria-prática e relevância formativa.
6. Não inclua metodologia de ensino nem avaliação no Plano de Ensino.
7. Linguagem formal, acadêmica, clara e acessível.
8. Para UCA, articule apenas os elementos pertinentes da matriz, perfil do egresso, DCNs e ENADE. Não tente colocar todas as competências do curso em uma única disciplina.
9. Para U4, não imponha automaticamente estruturas regulatórias brasileiras. Considere matriz, perfil do egresso e ementário em contexto acadêmico estadunidense.
10. Referências bibliográficas: EXATAMENTE 5 básicas + 5 complementares.
11. Toda referência deve ser REAL, EXISTENTE e VERIFICÁVEL. Use a Google Search grounding disponível para confirmar autor, título, edição/editora quando aplicável e ano. NÃO invente dados. Se não puder confirmar uma obra, não a use.
12. Referências em ABNT. Para UCA, predomínio de obras em português, salvo clássicos/obras estrangeiras indispensáveis. Para U4, use referências adequadas ao contexto acadêmico do programa.
13. Calibre complexidade e autonomia à posição curricular informada e às evidências documentais.
14. Se houver divergência documental, não resolva por adivinhação: registre em alertas.
15. Objetivos: UM texto corrido, integrando conhecimentos, competências e habilidades esperados.
16. Ementa: UM parágrafo corrido, padrão PPC, coerente com os 16 capítulos.
17. Não acrescente seções visíveis de metodologia ou avaliação.

DOCUMENTOS FORNECIDOS:
{docs_text}

RETORNE SOMENTE JSON VÁLIDO, sem markdown, exatamente nesta estrutura:

{{
  "diagnostico": {{
    "papel_da_disciplina": "texto curto",
    "etapa_formativa": "texto curto",
    "documentos_considerados": ["..."],
    "alertas": ["..."]
  }},
  "plano": {{
    "objetivos": "texto corrido",
    "ementa": "parágrafo único",
    "capitulos": [
      {{
        "numero": 1,
        "titulo": "título",
        "sumario_expandido": "parágrafo"
      }}
    ],
    "bibliografia_basica": [
      {{
        "abnt": "referência em ABNT",
        "url_verificacao": "https://..."
      }}
    ],
    "bibliografia_complementar": [
      {{
        "abnt": "referência em ABNT",
        "url_verificacao": "https://..."
      }}
    ]
  }},
  "rastreabilidade": [
    {{
      "capitulo": 1,
      "funcao_pedagogica": "por que este capítulo existe",
      "competencias_habilidades": ["..."],
      "fontes_documentais": ["..."]
    }}
  ],
  "auditoria": {{
    "dados_imutaveis_preservados": true,
    "quantidade_capitulos": 16,
    "progressao_validada": true,
    "bibliografia_basica_verificada": 5,
    "bibliografia_complementar_verificada": 5,
    "coerencia_global": true,
    "observacoes": ["..."]
  }}
}}

A lista "capitulos" deve conter exatamente 16 objetos, numerados de 1 a 16.
A lista "rastreabilidade" deve conter exatamente 16 objetos, um para cada capítulo.
"""

def render_plan(data, disciplina, carga, creditos):
    plano = data["plano"]

    st.subheader(disciplina)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Carga horária:** {carga}")
    with c2:
        st.markdown(f"**Créditos:** {creditos}")

    st.divider()
    st.markdown("## 1. Objetivos da Disciplina")
    st.write(plano["objetivos"])

    st.markdown("## 2. Ementa da Disciplina")
    st.write(plano["ementa"])

    st.markdown("## 3. Sumário / Conteúdo Programático")
    st.markdown("### 3.1. Listagem inicial — 16 capítulos")
    for cap in plano["capitulos"]:
        st.markdown(f"**{cap['numero']}. {cap['titulo']}**")

    st.markdown("### 3.2. Desenvolvimento dos 16 capítulos")
    for cap in plano["capitulos"]:
        st.markdown(f"#### Capítulo {cap['numero']} — {cap['titulo']}")
        st.write(cap["sumario_expandido"])

    st.markdown("## 4. Referências Bibliográficas")
    st.markdown("### 4.1. Bibliografia básica")
    for ref in plano["bibliografia_basica"]:
        st.markdown(f"- {ref['abnt']}")
        if ref.get("url_verificacao"):
            st.caption(f"Verificação: {ref['url_verificacao']}")

    st.markdown("### 4.2. Bibliografia complementar")
    for ref in plano["bibliografia_complementar"]:
        st.markdown(f"- {ref['abnt']}")
        if ref.get("url_verificacao"):
            st.caption(f"Verificação: {ref['url_verificacao']}")

# -----------------------------
# Estado
# -----------------------------
for key, default in {
    "resultado": None,
    "etapa_atual": 1,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------------
# Cabeçalho
# -----------------------------
st.title("Orquestrador Pedagógico")
st.caption("MVP online — construção e auditoria de Plano de Ensino")

with st.sidebar:
    st.markdown("### Configuração")
    try:
        cloud_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        cloud_key = ""

    api_key = cloud_key or os.getenv("GEMINI_API_KEY", "")
    if api_key:
        st.success("Chave gratuita do Gemini configurada no ambiente.")
    else:
        api_key = st.text_input(
            "Gemini API Key",
            value="",
            type="password",
            help="Crie gratuitamente no Google AI Studio e, no Streamlit, prefira salvá-la em Secrets.",
        )
    model = st.selectbox(
        "Modelo",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
        index=0,
    )
    st.caption("O MVP usa o nível gratuito do Gemini e Google Search grounding para apoiar a verificação das referências.")

tab1, tab2, tab3 = st.tabs(["1. Disciplina", "2. Documentos", "3. Resultado"])

with tab1:
    st.markdown("### Dados da disciplina")
    col1, col2 = st.columns(2)
    with col1:
        modelo = st.radio("Modelo acadêmico", ["UCA", "U4"], horizontal=True)
        curso = st.text_input("Curso", placeholder="Ex.: Pedagogia")
        disciplina = st.text_input("Nome da disciplina", placeholder="Nome oficial")
    with col2:
        carga = st.text_input("Carga horária", placeholder="Ex.: 60 h")
        creditos = st.number_input("Créditos", min_value=0.0, step=0.5, format="%.1f")
        etapa = st.text_input(
            "Período / trimestre",
            placeholder="Ex.: 6º trimestre",
            help="Usado para calibrar complexidade e autonomia.",
        )

    st.markdown("#### Campos institucionais bloqueados após a geração")
    st.markdown(
        f"""
        <div class="fixed-box">
        <b>Nome da disciplina</b>, <b>carga horária</b> e <b>créditos</b> são tratados
        como dados imutáveis pelo Orquestrador.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab2:
    st.markdown("### Base documental")
    st.caption("No MVP, os documentos são enviados manualmente. A versão seguinte poderá consultá-los diretamente no Google Drive.")

    matriz = st.file_uploader("Matriz curricular", type=["pdf", "docx", "txt", "md"], key="matriz")
    perfil = st.file_uploader("Perfil do egresso", type=["pdf", "docx", "txt", "md"], key="perfil")

    if modelo == "UCA":
        dcn = st.file_uploader("DCNs do curso", type=["pdf", "docx", "txt", "md"], key="dcn")
        enade = st.file_uploader("Matriz de Referência do ENADE", type=["pdf", "docx", "txt", "md"], key="enade")
        ementario = None
        obrigatorios = [matriz, perfil, dcn, enade]
    else:
        ementario = st.file_uploader("Ementário do curso", type=["pdf", "docx", "txt", "md"], key="ementario")
        dcn = enade = None
        obrigatorios = [matriz, perfil, ementario]

    completos = all(x is not None for x in obrigatorios)
    if completos:
        st.markdown('<div class="status-ok">✓ Documentação obrigatória carregada.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warn">Documentação incompleta. O botão de geração permanecerá bloqueado.</div>', unsafe_allow_html=True)

    st.markdown("")
    dados_ok = bool(curso.strip() and disciplina.strip() and carga.strip() and creditos > 0)
    gerar = st.button(
        "Gerar Plano de Ensino",
        type="primary",
        use_container_width=True,
        disabled=not (completos and dados_ok and api_key.strip()),
    )

    if gerar:
        docs = {
            "Matriz curricular": extract_text(matriz),
            "Perfil do egresso": extract_text(perfil),
        }
        if modelo == "UCA":
            docs["DCNs"] = extract_text(dcn)
            docs["Matriz de Referência do ENADE"] = extract_text(enade)
        else:
            docs["Ementário"] = extract_text(ementario)

        instruction = make_instruction(
            modelo=modelo,
            curso=curso,
            disciplina=disciplina,
            carga=carga,
            creditos=creditos,
            etapa=etapa,
            docs=docs,
        )

        try:
            with st.spinner("Analisando documentos, estruturando 16 capítulos e verificando referências..."):
                client = genai.Client(api_key=api_key.strip())
                grounding_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )
                response = client.models.generate_content(
                    model=model,
                    contents=instruction,
                    config=types.GenerateContentConfig(
                        tools=[grounding_tool],
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                data = clean_json(response.text)

            # Auditoria mínima no lado da aplicação
            caps = data.get("plano", {}).get("capitulos", [])
            basicas = data.get("plano", {}).get("bibliografia_basica", [])
            comp = data.get("plano", {}).get("bibliografia_complementar", [])

            errors = []
            if len(caps) != 16:
                errors.append(f"Foram retornados {len(caps)} capítulos; o obrigatório é 16.")
            if len(basicas) != 5:
                errors.append(f"Foram retornadas {len(basicas)} referências básicas; o obrigatório é 5.")
            if len(comp) != 5:
                errors.append(f"Foram retornadas {len(comp)} referências complementares; o obrigatório é 5.")

            st.session_state.resultado = {
                "data": data,
                "disciplina": disciplina,
                "carga": carga,
                "creditos": creditos,
                "modelo": modelo,
                "curso": curso,
                "errors": errors,
            }

            if errors:
                st.warning("A geração terminou, mas a auditoria automática encontrou pendências. Consulte a aba Resultado.")
            else:
                st.success("Plano gerado e aprovado nas verificações estruturais do MVP.")
        except Exception as e:
            st.error(f"Não foi possível concluir a geração: {e}")

with tab3:
    if not st.session_state.resultado:
        st.info("Preencha os dados, carregue os documentos e clique em “Gerar Plano de Ensino”.")
    else:
        result = st.session_state.resultado
        data = result["data"]

        if result["errors"]:
            st.error("Pendências estruturais encontradas:")
            for err in result["errors"]:
                st.write(f"• {err}")

        subtabs = st.tabs(["Plano de Ensino", "Diagnóstico", "Rastreabilidade", "Auditoria"])

        with subtabs[0]:
            render_plan(data, result["disciplina"], result["carga"], result["creditos"])

        with subtabs[1]:
            diag = data.get("diagnostico", {})
            st.markdown("### Diagnóstico curricular")
            st.markdown(f"**Papel da disciplina:** {diag.get('papel_da_disciplina', '')}")
            st.markdown(f"**Etapa formativa:** {diag.get('etapa_formativa', '')}")
            st.markdown("**Documentos considerados:**")
            for item in diag.get("documentos_considerados", []):
                st.write(f"• {item}")
            alertas = diag.get("alertas", [])
            if alertas:
                st.markdown("**Alertas:**")
                for item in alertas:
                    st.warning(item)
            else:
                st.success("Nenhum alerta documental informado.")

        with subtabs[2]:
            st.markdown("### Rastreabilidade dos 16 capítulos")
            for item in data.get("rastreabilidade", []):
                with st.expander(f"Capítulo {item.get('capitulo')}"):
                    st.markdown(f"**Função pedagógica:** {item.get('funcao_pedagogica','')}")
                    st.markdown("**Competências / habilidades:**")
                    for x in item.get("competencias_habilidades", []):
                        st.write(f"• {x}")
                    st.markdown("**Fontes documentais:**")
                    for x in item.get("fontes_documentais", []):
                        st.write(f"• {x}")

        with subtabs[3]:
            aud = data.get("auditoria", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Capítulos", aud.get("quantidade_capitulos", "—"))
            c2.metric("Bibliografia básica", aud.get("bibliografia_basica_verificada", "—"))
            c3.metric("Bibliografia complementar", aud.get("bibliografia_complementar_verificada", "—"))

            checks = {
                "Dados imutáveis preservados": aud.get("dados_imutaveis_preservados"),
                "Progressão validada": aud.get("progressao_validada"),
                "Coerência global": aud.get("coerencia_global"),
            }
            for label, ok in checks.items():
                if ok:
                    st.success(f"✓ {label}")
                else:
                    st.warning(f"⚠ {label}")

            for obs in aud.get("observacoes", []):
                st.write(f"• {obs}")

        st.download_button(
            "Baixar resultado completo em JSON",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name="orquestracao_plano_ensino.json",
            mime="application/json",
            use_container_width=True,
        )
