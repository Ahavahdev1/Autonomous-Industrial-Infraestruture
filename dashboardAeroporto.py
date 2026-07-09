import streamlit as st
import json
import os
import time
import codecs

st.set_page_config(layout="wide", page_title="MEA Aerodrome Control")

st.title("✈️ MEA Aerodrome | Sovereign Control Engine")
st.markdown("---")

def get_aeroporto_data():
    # Agora lê os dados do Aeroporto
    path = os.path.join(os.getcwd(), "aeroporto_telemetria.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        return None
    return None

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Estado de Pista e Aproximação")
    data = get_aeroporto_data()
    
    if data and "aeronaves" in data:
        for ac in data["aeronaves"]:
            # Status Emojis
            status_emoji = "🟢" if ac["status"] == "APROXIMACAO" else "⚠️" if ac["status"] == "PRIORIDADE_MAXIMA" else "🔴"
            
            st.info(f"{status_emoji} **{ac['id']}** | Status: {ac['status']} | Combustível: {ac['combustivel']:.1f}%")
            
            # Barra de progresso do combustível
            progresso = min(max(ac['combustivel'] / 100, 0), 1.0)
            st.progress(progresso)
    else:
        st.warning("Aguardando telemetria do aeroporto...")

with col2:
    st.subheader("Monitor de Segurança SRE")
    st.markdown("### Protocolo Sovereign Gate")
    
    # Verifica se há emergências no JSON
    if data and any(ac["status"] == "EMERGENCIA_TOTAL" for ac in data["aeronaves"]):
        st.error("🚨 ALERTA DE EMERGÊNCIA ATIVO")
    else:
        st.success("✅ SISTEMA ÍNTEGRO")

st.subheader("Fluxo de Log do Sistema")
log_placeholder = st.empty()

# Loop de atualização do Dashboard
while True:
    log_path = os.path.join(os.getcwd(), "app.log")
    if os.path.exists(log_path):
        try:
            # Leitura tolerante para não travar o dashboard
            with codecs.open(log_path, "r", "utf-8", errors='ignore') as f:
                logs = f.readlines()[-15:]
                log_placeholder.code("".join(logs), language="bash")
        except Exception:
            log_placeholder.text("Aguardando sincronização de log...")
    else:
        log_placeholder.text("Aguardando arquivo de log (app.log)...")
    
    time.sleep(1)
    st.rerun()