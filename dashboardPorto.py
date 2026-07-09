import streamlit as st
import json
import os
import time
import codecs

st.set_page_config(layout="wide", page_title="MEA Industrial Dashboard")

st.title("🛡️ MEA Industrial | Sovereign Control Engine")
st.markdown("---")

def get_porto():
    # Caminho absoluto para evitar erros de diretório
    path = os.path.join(os.getcwd(), "porto_telemetria.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        return None
    return None

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Estado Físico do Pátio (Live)")
    porto = get_porto()
    
    if porto:
        for g in porto["guindastes"]:
            status_emoji = "🟢" if g["status"] == "ATIVO" else "⚠️" if "ALERTA" in g["status"] else "🔴"
            st.info(f"{status_emoji} **{g['id']}** | Status: {g['status']} | Temp: {g['temperatura_motor']:.1f}°C")
            progresso = min(max(g['temperatura_motor'] / 100, 0), 1.0)
            st.progress(progresso)
    else:
        st.warning("Aguardando telemetria...")

with col2:
    st.subheader("Monitor de Segurança SRE")
    st.markdown("### Protocolo Sovereign Gate")
    if porto and porto.get("status_global") == "SISTEMA_COLAPSADO_PARALISAÇÃO_TOTAL":
        st.error("🚨 SISTEMA EM COLAPSO")
    else:
        st.success("✅ SISTEMA ÍNTEGRO")

st.subheader("Fluxo de Log do Sistema")
log_placeholder = st.empty()

# Loop de atualização do Dashboard
while True:
    log_path = os.path.join(os.getcwd(), "app.log")
    if os.path.exists(log_path):
        try:
            # Modo de leitura tolerante
            with codecs.open(log_path, "r", "utf-8", errors='ignore') as f:
                logs = f.readlines()[-15:]
                log_placeholder.code("".join(logs), language="bash")
        except Exception:
            log_placeholder.text("Aguardando sincronização de log...")
    else:
        log_placeholder.text("Aguardando arquivo de log (app.log)...")
    
    time.sleep(1)
    st.rerun()