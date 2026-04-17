Análise de Sobrevivência de Insetos para Indicação de Resistência
#
# Este script R realiza uma análise estatística para identificar populações de insetos
# que apresentam uma taxa de sobrevivência significativamente maior que 1% após
# a exposição a diferentes moléculas (inseticidas). Uma sobrevivência acima deste
# limiar é considerada um forte indicativo de potencial evolução de resistência.
#
# O script segue os seguintes passos:
# 1. Preparação do Ambiente: Instala e carrega pacotes necessários, e define o diretório de trabalho.
# 2. Carregamento e Tratamento dos Dados: Lê o arquivo de entrada e garante que os dados
#    estejam no formato correto para análise.
# 3. Definição dos Parâmetros do Teste Z: Configura o limiar de sobrevivência e o nível
#    de significância para o teste estatístico.
# 4. Função para o Teste Z: Define a lógica de cálculo do Teste Z para proporções.
# 5. Execução da Análise: Aplica a função do Teste Z a cada linha dos seus dados.
# 6. Visualização e Interpretação dos Resultados: Exibe os resultados finais e fornece
#    um guia para entender o que cada coluna significa, especialmente a coluna
#    'significativo'.
