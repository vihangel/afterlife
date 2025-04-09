<!-- @format -->

# 📊 Comentários Analyzer: Instagram Scraper para Análise de Identidade Pós-Morte

Este projeto realiza o **scraping de comentários públicos** de postagens do Instagram, com o objetivo de auxiliar estudos sobre os **efeitos da Inteligência Artificial na recriação de identidades digitais póstumas**. Ele extrai, organiza e salva comentários relevantes de vídeos/reels/postagens, que serão posteriormente analisados.

## 🎯 Objetivo

Coletar comentários para analisar interações sociais em torno de conteúdos postados após a morte de uma pessoa ou em homenagem a ela, observando **respostas emocionais, padrões de linguagem, sentimentos coletivos** e possíveis usos de IA para simulação de presença.

---

## 📚 Sobre o Projeto de Pesquisa

Este scraper é parte de uma pesquisa mais ampla sobre como tecnologias de IA e memória digital interagem com o luto e as homenagens online. A coleta se concentra em casos onde há repercussão social e emocional, como o vídeo analisado em:

📌 `trend_abraco_anacarolinaoliveira_oficial.csv`  
📎 `https://www.instagram.com/reel/DFWILfKS-L_/?igsh=dXFhNnVoOXgzMHc%3D`

---

## ⚙️ Tecnologias Utilizadas

- **Python 3.13+**
- **Selenium** com WebDriver
- **ChromeDriver** via `webdriver-manager`
- **Ambiente virtual** com `venv`
- Exportação em `.csv`

---

## 🧩 Estrutura do Projeto

```
comentarios-analyzer/
├── scraping/
│   ├── instagram_scraper.py     # Funções de extração e scroll
│   ├── instagram_scraper_bs.py  # Versão baseada em BeautifulSoup (legado)
│   └── main.py                  # Script principal de execução
├── data/
│   ├── instagram_comments_bs.csv         # Resultado da coleta atual
│   └── trend_abraco_anacarolinaoliveira_oficial.csv  # Exemplo de dados coletados
├── script/
│   └── run.sh                   # Script para rodar o scraper
├── venv/                        # Ambiente virtual Python
├── requirements.txt             # Dependências
└── .env                         # (opcional) variáveis de ambiente
```

---

## 📥 Como Usar

### 1. Clone o repositório e instale as dependências:

```bash
git clone https://github.com/vihangel/comentarios-analyzer.git
cd comentarios-analyzer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Execute o script principal

```bash
python scraping/main.py
```

Você será solicitado a inserir uma URL de post do Instagram. Exemplo:

```
📎 Cole aqui a URL do post do Instagram: https://www.instagram.com/reel/DFWILfKS-L_/?igsh=dXFhNnVoOXgzMHc%3D
```

Os comentários serão extraídos e salvos no diretório `data/`.

---

## 🔐 Observações

- O script depende de estar **logado em uma sessão ativa** do Instagram no Chrome, configurada previamente via `user-data-dir`.
- **Apenas comentários públicos** são coletados.
- Este projeto é utilizado exclusivamente para fins **educacionais e de pesquisa acadêmica**. Não deve ser usado para coleta de dados sem consentimento.

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Sinta-se à vontade para colaborar ou adaptar conforme seu interesse acadêmico.
