import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
# from supabase import create_client, Client # Descomente quando configurar o banco

# 1. Configuração da Página
st.set_page_config(page_title="Dose Diagnóstica - Sobrevivência", layout="wide")

# Criando as Abas na interface principal
aba_analise, aba_historico = st.tabs(["📊 Executar Análise", "📚 Base de Dados (Meta-Análise)"])

# ==============================================================================
# ABA 1: EXECUÇÃO DA ANÁLISE (Seu código atual)
# ==============================================================================
with aba_analise:
    st.title("Teste Z Unilateral: Dose Diagnóstica (Sobrevivência)")
    st.write("Baseado na metodologia de Roush & Miller para avaliar se a taxa de sobrevivência é estatisticamente maior que a esperada.")

    st.warning("""
    ⚠️ **Aviso de Isenção de Responsabilidade:** Esta ferramenta fornece estimativas probabilísticas baseadas em modelos matemáticos e estatísticos de resistência. 
    Os resultados servem estritamente como suporte acadêmico e tomada de decisão e não substituem o monitoramento contínuo em campo.
    """)

    consentimento = st.checkbox(
        "Autorizo o armazenamento anônimo e agregado dos dados estatísticos e biológicos inseridos nesta análise "
        "para fins exclusivos de pesquisa científica e mapeamento regional da evolução da resistência a inseticidas.",
        key="consent_aba1" # Chave única para o widget
    )

    st.divider()

    # Parâmetros Estatísticos colocados na barra lateral
    st.sidebar.header("Parâmetros do Teste Z")
    p0_sobrevivencia_perc = st.sidebar.number_input("Sobrevivência Esperada (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
    alfa = st.sidebar.number_input("Nível de Significância (Alfa)", min_value=0.001, max_value=0.100, value=0.05, step=0.01)

    p0_surv = p0_sobrevivencia_perc / 100
    z_critico = stats.norm.ppf(1 - alfa)

    st.sidebar.divider()
    st.sidebar.write("**Valores de Referência Atuais:**")
    st.sidebar.write(f"- Proporção Esperada ($p_0$): **{p0_surv:.4f}**")
    st.sidebar.write(f"- Valor Z Crítico: **{z_critico:.4f}**")

    # Entrada de Dados
    st.subheader("Entrada de Dados")
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

    df_editado = st.data_editor(dados_iniciais, num_rows="dynamic", use_container_width=True, key="editor_aba1")

    botao_executar = st.button("Executar Análise de Resistência", type="primary", disabled=not consentimento)

    if not consentimento:
        st.caption("🔒 *Por favor, marque a caixa de consentimento acima para desbloquear a análise.*")

    if botao_executar:
        if df_editado.empty or df_editado["N (Total)"].isnull().any() or df_editado["Mortalidade (%)"].isnull().any():
            st.error("Erro: Preencha corretamente os valores de 'N (Total)' e 'Mortalidade (%)'.")
        else:
            df_resultados = df_editado.copy()
            
            # --- ROTINA DE ARMAZENAMENTO AUTOMÁTICO ---
            # Aqui o backend extrai exatamente o dicionário que você mencionou e envia para a nuvem
            # (Mantido em segundo plano para o usuário ter uma experiência fluida)
            registros_para_banco = []
            for _, row in df_resultados.iterrows():
                dados_linha = {
                    "molecula": str(row["Molécula"]),
                    "n_total": int(row["N (Total)"]),
                    "mortalidade_perc": float(row["Mortalidade (%)"]),
                    "p0_configurado": float(p0_sobrevivencia_perc),
                    "z_calculado": float(row["Z Calculado"] if "Z Calculado" in row else 0.0), # Será preenchido após cálculo
                    "significativo": bool(row["Significativo (Resistência)"] if "Significativo (Resistência)" in row else False)
                }
                registros_para_banco.append(dados_linha)
            
            # Cálculos Matemáticos vetorizados
            df_resultados["Sobrevivência Obs (%)"] = 100 - df_resultados["Mortalidade (%)"]
            df_resultados["p_obs"] = df_resultados["Sobrevivência Obs (%)"] / 100
            
            N_seguro = np.maximum(df_resultados["N (Total)"], 1e-9)
            df_resultados["Erro Padrão"] = np.sqrt((p0_surv * (1 - p0_surv)) / N_seguro)
            df_resultados["Z Calculado"] = (df_resultados["p_obs"] - p0_surv) / df_resultados["Erro Padrão"]
            df_resultados["Z Crítico"] = z_critico
            df_resultados["Significativo (Resistência)"] = df_resultados["Z Calculado"] > z_critico
            
            # Atualizando os valores reais calculados no dicionário de metadados antes do envio
            for i, row in df_resultados.iterrows():
                registros_para_banco[i]["z_calculado"] = float(row["Z Calculado"])
                registros_para_banco[i]["significativo"] = bool(row["Significativo (Resistência)"])
            
            # [AQUI ENTRA A FUNÇÃO DE ENVIO PARA O SUPABASE/FIREBASE]
            # supabase.table("registros_resistencia").insert(registros_para_banco).execute()

            # Renderização dos Resultados
            st.subheader("Resultados Finais da Análise")
            colunas_exibicao = ["População", "Molécula", "N (Total)", "Mortalidade (%)", "Sobrevivência Obs (%)", "Z Calculado", "Z Crítico", "Significativo (Resistência)"]
            df_final = df_resultados[colunas_exibicao]
            
            def destacar_resistencia(row):
                if row["Significativo (Resistência)"]:
                    return ['background-color: rgba(255, 75, 75, 0.2)'] * len(row)
                return [''] * len(row)
                
            st.dataframe(df_final.style.apply(destacar_resistencia, axis=1).format({
                "Mortalidade (%)": "{:.2f}%", "Sobrevivência Obs (%)": "{:.2f}%", "Z Calculado": "{:.4f}", "Z Crítico": "{:.4f}"
            }), use_container_width=True)

    # Rodapé de Autoria da Aba 1
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📚 Referências Bibliográficas")
        st.markdown("* **Roush & Miller (1986); Abbott (1925)**")
    with col2:
        st.markdown("### 👨‍💻 Autoria: Vitor Quintela")

# ==============================================================================
# ABA 2: VISUALIZAÇÃO DOS METADADOS COLETADOS (Meta-Análise)
# ==============================================================================
with aba_historico:
    st.title("📚 Banco de Dados Global de Monitoramento")
    st.write("Esta seção exibe o consolidado de metadados anonimizados compartilhados por pesquisadores. Útil para meta-análises.")

    # Exemplo de como os dados baixados da nuvem apareceriam para o usuário
    st.subheader("📊 Histórico Acumulado de Bioensaios")
    
    # Simulação de dados que viriam do seu banco (Substitua por: supabase.table().select().execute())
    dados_acumulados_mock = pd.DataFrame({
        "Data do Registro": ["2026-07-01", "2026-07-03", "2026-07-05", "2026-07-06"],
        "Molécula": ["Abamectina", "Spinosade", "Abamectina", "Deltametrina"],
        "N (Total)": [400, 250, 1200, 500],
        "Mortalidade Média (%)": [98.2, 99.1, 74.5, 92.0],
        "p0 Configurado (%)": [1.0, 1.0, 1.5, 1.0],
        "Casos de Resistência Detectados": [1, 0, 4, 2]
    })
    
    st.dataframe(dados_acumulados_mock, use_container_width=True)
    
    # Recursos para Meta-Análise Futura diretamente na interface
    st.subheader("📈 Insights para Pesquisa")
    col_meta1, col_meta2 = st.columns(2)
    
    with col_meta1:
        st.info("💡 **Frequência de Resistência por Princípio Ativo**")
        # Aqui você poderá colocar um gráfico do Plotly ou Matplotlib (ex: st.bar_chart)
        st.write("Em breve: Gráficos de barras dinâmicos consolidando quais moléculas apresentam maior frequência de falha de controle.")
        
    with col_meta2:
        st.info("📥 **Exportar Base de Dados**")
        st.write("Você pode baixar o compilado anonimizado para rodar seus próprios modelos preditivos no R ou Jupyter Notebook.")
        # Botão para baixar o arquivo gerado
        st.download_button(
            label="Baixar Dados da Meta-Análise (CSV)",
            data=dados_acumulados_mock.to_csv(index=False),
            file_name="meta_analise_resistencia.csv",
            mime="text/csv"
        )
