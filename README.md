# Projeto de Web Scraping: Coleta de Dados de Produtos - Baldor

## Objetivo
Este projeto tem como finalidade automatizar a coleta de informações técnicas e recursos de produtos industriais disponibilizados no site da [Baldor](https://www.baldor.com). Foram extraídos dados como nome, descrição, especificações ("specs"), lista de materiais ("BOM") e arquivos associados como manuais, imagens e CADs.

## Tecnologias Utilizadas
- **Python 3.12**
- **Selenium WebDriver**
- **Google Chrome (via ChromeDriver)**
- **Bibliotecas complementares:** `requests`, `json`, `os`, `time`, `re`

## Estrutura do Projeto
```
output/
├── assets/
│   └── M123456/
│       ├── manual.pdf
│       ├── cad.dwg
│       └── img.jpg
├── M123456.json
├── M123457.json
...
```
Cada produto é salvo em um arquivo `.json` contendo:
```json
{
  "product_id": "M123456",
  "name": "3-Phase AC Motor",
  "description": "TEFC, 2 HP, 1800 RPM",
  "specs": {
    "hp": "2",
    "voltage": "230/460",
    "rpm": "1800",
    "frame": "145T"
  },
  "bom": [
    {
      "part_number": "123-456",
      "description": "Cooling Fan",
      "quantity": 1
    }
  ],
  "assets": {
    "manual": "output/assets/M123456/manual.pdf",
    "cad": "output/assets/M123456/cad.dwg",
    "image": "output/assets/M123456/img.jpg"
  }
}
```

## Como Executar o Projeto
1. Clone este repositório
2. Instale as dependências:
```bash
pip install selenium requests
```
3. Certifique-se de ter o Chrome e o `chromedriver` compatível instalado
4. Execute o script principal:
```bash
python main.py
```

## Funcionalidades
- Raspagem de produtos de três categorias diferentes
- Tratamento de falhas comuns (elementos ausentes, timeouts, arquivos indisponíveis)
- Estrutura organizada para exportação de dados reutilizáveis
- Download direto de assets (PDF, imagens, CAD)

## Aprendizados
Esse projeto me permitiu lidar com desafios reais de automação de coleta de dados em ambientes dinâmicos, tratamento de erros em tempo real e manipulação de arquivos baixados por código. Também aprofundei meu conhecimento em expressões regulares, manipulação de JSON e estruturação de projetos escaláveis.

## Possíveis Melhorias Futuras
- Melhorar a robustez na coleta do arquivo CAD
- Implementar logging estruturado
- Salvar em banco de dados (ex: SQLite ou PostgreSQL)
- Interface gráfica para seleção de categorias

## Contato
**Millena Ramos**  
[LinkedIn](https://www.linkedin.com/in/millena-tamarindo-ramos/?originalSubdomain=br)  
