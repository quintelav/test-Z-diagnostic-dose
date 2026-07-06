import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats

# 1. Configuração da Página
st.set_page_config(page_title="Dose Diagnóstica - Sobrevivência", layout="wide")
st.title("Teste Z Unilateral: Dose Diagnóstica (Sobrevivência)")
st.write("Baseado na metodologia de Roush & Miller para avaliar se a taxa de sobrevivência é estatisticamente maior que a esperada.")

# 2. Barra Lateral (Parâmetros do Teste Estatístico)
st.sidebar.header("Parâmetros do Teste Z")
p0_sobrevivencia_perc = st.sidebar.number_input("Sobrevivência Esperada (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
alfa = st.sidebar.number_input("Nível de Significância (Alfa)", min_value=0.001, max_value=0.100, value=0.05, step=0.01)

# Conversão dos parâmetros para o cálculo
p0_surv = p0_sobrevivencia_perc / 100
z_critico = stats.norm.ppf(1 - alfa) # Calcula o Z Crítico para o teste unilateral à direita

st.sidebar.divider()
st.sidebar.write("**Valores de Referência Atuais:**")
st.sidebar.write(f"- Proporção Esperada ($p_0$): **{p0_surv:.4f}**")
st.sidebar.write(f"- Valor Z Crítico: **{z_critico:.4f}**")

# 3. Entrada de Dados (Tabela Editável)
st.subheader("Entrada de Dados")
st.info("💡 Você pode fazer o upload de um arquivo CSV ou colar os dados do Excel diretamente na tabela abaixo. O arquivo CSV deve conter as colunas: População, Molécula, N (Total) e Mortalidade (%).")

# --- NOVA PARTE: Botão de Upload de CSV ---
arquivo_csv = st.file_uploader("Carregar arquivo CSV", type=["csv"])

# Lógica condicional: Usa o CSV se existir, caso contrário, usa o padrão
if arquivo_csv is not None:
    # O Streamlit lê o arquivo CSV inserido pelo usuário
    dados_iniciais = pd.read_csv(arquivo_csv)
else:
    # DataFrame padrão baseado na estrutura do seu script R
    dados_iniciais = pd.DataFrame({
        "População": ["Pop1", "Pop1", "Pop2", "Pop2"],
        "Molécula": ["Abamectina", "Abamectina", "Abamectina", "Abamectina"],
        "N (Total)": [100, 100, 100, 100],
        "Mortalidade (%)": [99.5, 95.0, 80.0, 99.0]
    })

# A tabela editável continua funcionando da mesma forma, mas agora aceita a fonte de dados dinâmica
df_editado = st.data_editor(dados_iniciais, num_rows="dynamic", use_container_width=True)

# 4. Processamento e Cálculo
if st.button("Executar Análise de Resistência", type="primary"):
    
    # Validação básica
    if df_editado.empty or df_editado["N (Total)"].isnull().any() or df_editado["Mortalidade (%)"].isnull().any():
        st.error("Erro: Preencha corretamente os valores de 'N (Total)' e 'Mortalidade (%)'.")
    else:
        df_resultados = df_editado.copy()
        
        # Lógica matemática vetorizada baseada no script R
        # 1. Proporção de sobrevivência observada
        df_resultados["Sobrevivência Obs (%)"] = 100 - df_resultados["Mortalidade (%)"]
        df_resultados["p_obs"] = df_resultados["Sobrevivência Obs (%)"] / 100
        
        # 2. Erro Padrão
        # Adicionado um pequeno limite inferior no N para evitar divisão por zero, caso ocorra erro de digitação
        N_seguro = np.maximum(df_resultados["N (Total)"], 1e-9)
        df_resultados["Erro Padrão"] = np.sqrt((p0_surv * (1 - p0_surv)) / N_seguro)
        
        # 3. Z Calculado
        df_resultados["Z Calculado"] = (df_resultados["p_obs"] - p0_surv) / df_resultados["Erro Padrão"]
        
        # 4. Significância (Z Calculado > Z Crítico)
        df_resultados["Z Crítico"] = z_critico
        df_resultados["Significativo (Resistência)"] = df_resultados["Z Calculado"] > z_critico
        
        # 5. Organização para exibição
        colunas_exibicao = [
            "População", "Molécula", "N (Total)", "Mortalidade (%)", 
            "Sobrevivência Obs (%)", "Z Calculado", "Z Crítico", "Significativo (Resistência)"
        ]
        df_final = df_resultados[colunas_exibicao]
        
        # Renderização dos resultados
        st.subheader("Resultados Finais da Análise")
        
        # Estilização da tabela para destacar as linhas com resistência significativa
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
        
        # 5. Guia Rápido de Interpretação
        st.divider()
        st.markdown("### 🔍 Guia de Interpretação")
        st.write(
            "As linhas destacadas em vermelho e marcadas como **TRUE** indicam que o *Z Calculado* é maior que o *Z Crítico*. "
            "Isso significa que a proporção de sobrevivência observada é **estatisticamente maior** que o limiar definido (ex: **1%**). "
            "Essas populações são fortes candidatas para investigações adicionais de resistência."
        )
        # (O código anterior termina aqui, logo após o Guia de Interpretação)

        # 6. Referências e Autoria
        st.divider() # Adiciona uma linha horizontal para separar as seções
        
        col1, col2 = st.columns(2) # Divide o espaço final em duas colunas
        
        with col1:
            st.markdown("### 📚 Referências Bibliográficas")
            st.markdown("""
            Os cálculos estatísticos e correções realizados neste aplicativo são baseados nas seguintes literaturas:
            
            * **Teste Z Unilateral (Dose Diagnóstica):** Roush, R. T., & Miller, G. L. (1986). Considerations for design of insecticide resistance monitoring programs. *Journal of Economic Entomology*, 79(2), 293-298.
            * **Correção de Mortalidade:** Abbott, W. S. (1925). A method of computing the effectiveness of an insecticide. *Journal of Economic Entomology*, 18(2), 265-267.
            """)
            
        with col2:
            st.markdown("### 👨‍💻 Autoria e Manutenção")
            st.info("""
            **Desenvolvido e mantido por: Vitor Quintela**
            
            Este aplicativo foi criado para facilitar e padronizar a análise da evolução da resistência a inseticidas. 
            """)
            # Opcional: Você pode adicionar seu e-mail ou link para o Lattes/LinkedIn abaixo
            st.markdown("📧 Contato: *quintelav@gmail.com*")
            st.markdown("🔗 [Meu LinkedIn https://www.linkedin.com/in/vitorquintelas/)")
