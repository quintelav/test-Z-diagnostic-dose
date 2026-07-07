import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
from datetime import datetime # NOVA IMPORTAÇÃO: Para capturar a data/hora atual
# from supabase import create_client, Client # Descomente quando configurar o banco privado

# 1. Configuração da Página e Títulos
st.set_page_config(page_title="Dose Diagnóstica - Sobrevivência", layout="wide")
st.title("Teste Z Unilateral: Dose Diagnóstica (Sobrevivência)")
st.write("Baseado na metodologia de Roush & Miller para avaliar se a taxa de sobrevivência é estatisticamente maior que a esperada.")

# 2. Seção de Avisos, LGPD e Consentimento
st.warning("""
⚠️ **Aviso de Isenção de Responsabilidade:** Esta ferramenta fornece estimativas probabilísticas baseadas em modelos matemáticos e estatísticos de resistência. 
Os resultados servem estritamente como suporte acadêmico e tomada de decisão e não substituem o monitoramento contínuo em campo.
""")

# Caixa de consentimento para liberação do sistema
consentimento = st.checkbox(
    "Autorizo o armazenamento anônimo e agregado dos dados estatísticos e biológicos inseridos nesta análise "
    "para fins exclusivos de pesquisa científica e mapeamento da evolução da resistência a inseticidas."
)

# --- NOVOS CAMPOS: Inserção de Metadados de Localização ---
# O campo só fica ativo se o usuário der o consentimento
opcoes_regioes = [
    "Não Informado", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", 
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

# Você também pode personalizar a lista acima para macrorregiões específicas (ex: "Nordeste", "Matopiba", "Cerrado")
macrorregiao = st.selectbox(
    "📍 Selecione a Macrorregião/Estado de origem das populações:",
    options=opcoes_regioes,
    disabled=not consentimento,
    help="Essa informação é crucial para o mapeamento geográfico da resistência em meta-análises."
)

st.divider()

# 3. Barra Lateral (Parâmetros do Teste Estatístico)
st.sidebar.header("Parâmetros do Teste Z")
p0_sobrevivencia_perc = st.sidebar.number_input("Sobrevivência Esperada (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
alfa = st.sidebar.number_input("Nível de Significância (Alfa)", min_value=0.001, max_value=0.100, value=0.05, step=0.01)

# Conversão dos parâmetros para o cálculo
p0_surv = p0_sobrevivencia_perc / 100
z_critico = stats.norm.ppf(1 - alfa)

st.sidebar.divider()
st.sidebar.write("**Valores de Referência Atuais:**")
st.sidebar.write(f"- Proporção Esperada ($p_0$): **{p0_surv:.4f}**")
st.sidebar.write(f"- Valor Z Crítico: **{z_critico:.4f}**")

# 4. Entrada de Dados
st.subheader("Entrada de Dados")
st.info("💡 Você pode fazer o upload de um arquivo CSV ou colar os dados do Excel diretamente na tabela abaixo. O arquivo CSV deve conter as colunas: População, Molécula, N (Total) e Mortalidade (%).")

arquivo_csv = st.file_uploader("Carregar arquivo CSV", type=["csv"])

if arquivo_csv is not None:
    dados_iniciais = pd.read_csv(arquivo_csv)
else:
    dados_iniciais = pd.DataFrame({
        "População": ["Pop1", "Pop1", "Pop2", "Pop2"],
        "Molécula": ["Abamectina", "Abamectina", "Abamectina", "Abamectina"],
        "N (Total)": [100, 100, 100, 100],
        "Mortalidade (%)": [99.5, 95.0, 80.0, 99.0]
    })

df_editado = st.data_editor(dados_iniciais, num_rows="dynamic", use_container_width=True)

# 5. Botão de Execução
botao_executar = st.button(
    "Executar Análise de Resistência", 
    type="primary", 
    disabled=not consentimento,
    help="Você precisa aceitar os termos de consentimento para habilitar a execução."
)

if not consentimento:
    st.caption("🔒 *Por favor, marque a caixa de consentimento acima para desbloquear a análise.*")

# 6. Processamento, Cálculo e Salvamento Oculto (Backend)
if botao_executar:
    if df_editado.empty or df_editado["N (Total)"].isnull().any() or df_editado["Mortalidade (%)"].isnull().any():
        st.error("Erro: Preencha corretamente os valores de 'N (Total)' e 'Mortalidade (%)'.")
    else:
        df_resultados = df_editado.copy()
        
        # Lógica matemática vetorizada
        df_resultados["Sobrevivência Obs (%)"] = 100 - df_resultados["Mortalidade (%)"]
        df_resultados["p_obs"] = df_resultados["Sobrevivência Obs (%)"] / 100
        
        N_seguro = np.maximum(df_resultados["N (Total)"], 1e-9)
        df_resultados["Erro Padrão"] = np.sqrt((p0_surv * (1 - p0_surv)) / N_seguro)
        df_resultados["Z Calculado"] = (df_resultados["p_obs"] - p0_surv) / df_resultados["Erro Padrão"]
        df_resultados["Z Crítico"] = z_critico
        df_resultados["Significativo (Resistência)"] = df_resultados["Z Calculado"] > z_critico
        
        # --- ROTINA DE BACKEND COM DATA E MACROREGIÃO ---
        try:
            # Captura a data e hora exata da execução no formato ISO (AAAA-MM-DD HH:MM:SS)
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            registros_para_banco = []
            for _, row in df_resultados.iterrows():
                dados_linha = {
                    "data_registro": data_atual,          # NOVO CAMPO AUTOMÁTICO
                    "macrorregiao": str(macrorregiao),    # NOVO CAMPO VIA SELECTBOX
                    "molecula": str(row["Molécula"]),
                    "n_total": int(row["N (Total)"]),
                    "mortalidade_perc": float(row["Mortalidade (%)"]),
                    "p0_configurado": float(p0_sobrevivencia_perc),
                    "z_calculado": float(row["Z Calculado"]),
                    "significativo": bool(row["Significativo (Resistência)"])
                }
                registros_para_banco.append(dados_linha)
            
            # Envia para a tabela do seu banco privado na nuvem
            # supabase.table("registros_resistencia").insert(registros_para_banco).execute()
            pass
        except Exception:
            pass

        # Renderização dos resultados na tela para o usuário
        st.subheader("Resultados Finais da Análise")
        colunas_exibicao = [
            "População", "Molécula", "N (Total)", "Mortalidade (%)", 
            "Sobrevivência Obs (%)", "Z Calculado", "Z Crítico", "Significativo (Resistência)"
        ]
        df_final = df_resultados[colunas_exibicao]
        
        def destacar_resistencia(row):
            if row["Significativo (Resistência)"]:
                return ['background-color: rgba(255, 75, 75, 0.2)'] * len(row)
            return [''] * len(row)
            
        st.dataframe(
            df_final.style.apply(destacar_resistencia, axis=1)
                         .format({
                             "Mortalidade (%)": "{:.2f}%", 
                             "Sobrevivência Obs (%)": "{:.2f}%",
                             "Z Calculado": "{:.4f}",
                             "Z Crítico": "{:.4f}"
                         }), 
            use_container_width=True
        )
        
        # Guia Rápido de Interpretação
        st.divider()
        st.markdown("### 🔍 Guia de Interpretação")
        st.write(
            "As linhas destacadas em vermelho e marcadas como **TRUE** indicam que o *Z Calculado* é maior que o *Z Crítico*. "
            "Isso significa que a proporção de sobrevivência observada é **estatisticamente maior** que o limiar definido. "
            "Essas populações são fortes candidatas para investigações adicionais de resistência."
        )

# 7. Referências e Autoria (Rodapé permanente)
st.divider() 
col1, col2 = st.columns(2) 

with col1:
    st.markdown("### 📚 Referências Bibliográficas")
    st.markdown("""
    * **Teste Z Unilateral (Dose Diagnóstica):** Roush, R. T., & Miller, G. L. (1986). *Journal of Economic Entomology*, 79(2), 293-298.
    * **Correção de Mortalidade:** Abbott, W. S. (1925). *Journal of Economic Entomology*, 18(2), 265-267.
    """)
    
with col2:
    st.markdown("### 👨‍💻 Autoria e Manutenção")
    st.info("**Desenvolvido e mantido por: Vitor Quintela**")
    st.markdown("📧 Contato: *quintelav@gmail.com* | 🔗 [Meu LinkedIn](https://www.linkedin.com/in/vitorquintelas/)")
