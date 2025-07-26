import os

# --- Configurações ---

# Diretórios e arquivos a serem completamente ignorados em qualquer nível
EXCLUDE_ITEMS = {
    'venv', '__pycache__', '.git', '.idea', 
    '.vscode', '.mypy_cache', '.pytest_cache', 
    'node_modules',
    # Adicionado para ignorar o próprio script e o arquivo de saída
    os.path.basename(__file__), 
    'estrutura_projeto.txt'
}

# Nome do arquivo de saída
OUTPUT_FILE = 'estrutura_projeto.txt'

def gerar_arvore(diretorio_raiz, prefixo=''):
    """
    Função recursiva que gera a representação em árvore de um diretório,
    respeitando a lista de exclusão EXCLUDE_ITEMS.
    """
    try:
        # Pega todos os itens, filtra os excluídos e depois ordena
        itens = sorted([item for item in os.listdir(diretorio_raiz) if item not in EXCLUDE_ITEMS])
    except FileNotFoundError:
        return [] # Retorna vazio se o diretório não for encontrado

    linhas_saida = []
    for i, item in enumerate(itens):
        caminho_completo = os.path.join(diretorio_raiz, item)
        # Determina o conector do galho da árvore
        conector = '└── ' if i == len(itens) - 1 else '├── '
        
        if os.path.isdir(caminho_completo):
            # Adiciona a linha para o diretório
            linhas_saida.append(f"{prefixo}{conector}{item}/")
            # Define o prefixo para os itens dentro deste diretório
            novo_prefixo = prefixo + ('    ' if i == len(itens) - 1 else '│   ')
            # Chama a função recursivamente para o subdiretório
            linhas_saida.extend(gerar_arvore(caminho_completo, novo_prefixo))
        else:
            # Adiciona a linha para o arquivo
            linhas_saida.append(f"{prefixo}{conector}{item}")
            
    return linhas_saida

def main():
    """
    Função principal que orquestra a geração da estrutura do projeto.
    """
    # Define o diretório raiz como o local onde o script está
    raiz = os.path.abspath(os.path.dirname(__file__))
    print(f"Analisando a estrutura a partir de: {raiz}")

    # A primeira linha é o nome da pasta raiz
    linhas_finais = [f"{os.path.basename(raiz)}/"]
    
    # Gera a árvore a partir da raiz, usando um prefixo inicial
    linhas_finais.extend(gerar_arvore(raiz, prefixo=''))

    # Remove a primeira linha duplicada que pode ser gerada pela recursão
    # e garante que o nome do script não apareça
    linhas_finais[1:] = [linha for linha in linhas_finais[1:] if os.path.basename(__file__) not in linha]


    # Salva o resultado no arquivo de saída
    try:
        # Atualiza a constante EXCLUDE_ITEMS para garantir que o nome do script seja ignorado
        EXCLUDE_ITEMS.add(os.path.basename(__file__))
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Recria a árvore para garantir que a lista de exclusão atualizada seja usada
            linhas_para_salvar = [f"{os.path.basename(raiz)}/"]
            linhas_para_salvar.extend(gerar_arvore(raiz, prefixo=''))
            f.write('\n'.join(linhas_para_salvar))

        print(f"\nEstrutura do projeto salva com sucesso em: {OUTPUT_FILE}")
    except IOError as e:
        print(f"\nErro ao salvar o arquivo: {e}")

if __name__ == '__main__':
    # Atualiza o nome do script na lista de exclusão antes de tudo
    EXCLUDE_ITEMS.add(os.path.basename(__file__))
    main()
