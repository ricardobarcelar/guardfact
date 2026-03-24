import streamlit as st
from guardrail_service import VerifiedGuardrail

st.set_page_config(page_title="PJC-MT: Verificador de Factualidade", layout="wide")

st.title("🛡️ Guardrail de Factualidade Conformal")
st.subheader("Análise de Integridade de Documentos Policiais - Delegacia de Estelionato")

col1, col2 = st.columns(2)

with col1:
    contexto = st.text_area("Contexto (Boletim de Ocorrência Original):", height=300)
with col2:
    produzido = st.text_area("Texto Produzido por IA (Relatório/Resumo):", height=300)

if st.button("Verificar Factualidade"):
    if contexto and produzido:
        with st.spinner("Auditando via framework MACI..."):
            guard = VerifiedGuardrail()
            result = guard.verify_document(contexto, produzido)
            
            if result["status"] == "APPROVED":
                st.success(f"✅ Documento íntegro! Risco detectado: {result['risk_score']*100:.2f}%")
            else:
                st.error(f"⚠️ Alucinação Detectada! Risco {result['risk_score']*100:.2f}% excede o limiar de {result['threshold_used']}.")
            
            st.json(result)
    else:
        st.warning("Por favor, preencha ambos os campos.")