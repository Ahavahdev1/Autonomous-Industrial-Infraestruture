import streamlit as st
import json
import os
import time
import codecs

st.set_page_config(layout="wide", page_title="MEA Sovereign Dashboard")

st.title("🛡️ MEA Sovereign Control Engine | Telemetry Monitor")
st.markdown("---")

def get_telemetry():
    # Procura pelo arquivo de telemetria disponível
    files = ["aeroporto_telemetria.json", "porto_telemetria.json"]
    for f_path in files:
        if os.path.exists(f_path):
            with open(f_path, "r", encoding="utf-8") as f:
                return json.load(f), f_path
    return None, None

col1, col2 = st.columns([2, 1])

data, source_file = get_telemetry()

with col1:
    st.subheader(f"Monitoramento: {source_file}")
    if data:
        # Detecta automaticamente a lista de itens (guindastes ou aeronaves)
        key_list = "guindastes" if "guindastes" in data else "aeronaves"
        items = data.get(key_list, [])
        
        for item in items:
            # Cria um resumo dinâmico baseado no que existe no JSON
            name = item.get("id", "Desconhecido")
            status = item.get("status", "N/A")
            val = item.get("combustivel", item.get("temperatura_motor", 0))
            
            status_emoji = "🟢" if status in ["ATIVO", "APROXIMACAO"] else "⚠️" if "ALERTA" in status else "🔴"
            st.info(f"{status_emoji} **{name}** | Status: {status} | Valor: {val:.1f}")
            st.progress(min(max(val / 100, 0), 1.0))
            
        # Exibe métricas de resiliência se existirem
        if "metricas_resiliencia" in data:
            st.markdown("### 📊 Métricas de Resiliência")
            m = data["metricas_resiliencia"]
            st.metric("Eventos de Caos", m["eventos_de_caos"])
            st.metric("Intervenções IA", m["intervencoes_ia"])

with col2:
    st.subheader("Monitor de Segurança SRE")
    if data and any(s in str(data) for s in ["EMERGENCIA", "FALHA", "COLAPSADO"]):
        st.error("🚨 ALERTA DE SEGURANÇA ATIVO")
    else:
        st.success("✅ SISTEMA ÍNTEGRO")

st.subheader("Fluxo de Log do Sistema")
log_placeholder = st.empty()

while True:
    log_path = "app.log"
    if os.path.exists(log_path):
        with codecs.open(log_path, "r", "utf-8", errors='ignore') as f:
            logs = f.readlines()[-15:]
            log_placeholder.code("".join(logs), language="bash")
    time.sleep(1)
    st.rerun()