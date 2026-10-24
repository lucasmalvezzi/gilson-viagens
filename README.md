# 🦎✈️ GilsonViagens — Monitor Open Source de Passagens Aéreas

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-4ade80.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-38b6ff.svg)](https://www.python.org/)
[![Angular 22](https://img.shields.io/badge/Angular-22-f43f5e.svg)](https://angular.dev/)
[![Playwright Stealth](https://img.shields.io/badge/Scraper-Playwright%20Stealth-4ade80.svg)](https://playwright.dev/python/)

O **GilsonViagens** é uma aplicação **open source** local para monitorar automaticamente preços de passagens aéreas no **Google Flights** e receber alertas instantâneos no **Telegram** quando o valor atingir a sua meta.

Projetado para rodar na sua própria máquina (sem custos de nuvem), ele conta com **agendamento individual por busca** e integração opcional com o **Agendador de Tarefas do Windows (`schtasks.exe`)**, permitindo que as buscas rodem em segundo plano **mesmo com o servidor web fechado**.

---

## ✨ Principais Funcionalidades

- **🎯 Monitoramento Inteligente de Trechos:**
  - Autocomplete com **+75 aeroportos nacionais e internacionais** (busca por cidade, estado ou código IATA).
  - Busca por **Intervalo Personalizado de Datas** (com frequência configurável: a cada $N$ dias, diário ou apenas fins de semana) ou por **Mês de Foco**.
  - Calculadora em tempo real de estimativa de chamadas e tempo de varredura.
  - Filtro opcional de **apenas voos diretos (sem escalas)**.
- **⏰ Horários por Busca & Execução Sem Servidor:**
  - Configure um ou mais horários diários exclusivos para cada busca ativa (ex: `08:00, 14:00, 20:00`).
  - Modo **Windows Offline (`schtasks.exe`)**: executa o script standalone [`run_scheduled_search.py`](./run_scheduled_search.py) em 2º plano sem precisar manter o servidor FastAPI aberto.
- **📲 Alertas Instantâneos no Telegram:**
  - Envia notificação formatada com trecho, datas de ida/volta, preço alvo vs. menor preço encontrado e link direto para compra no Google Flights.
- **📈 Histórico Agrupado por Rota:**
  - Acordeões organizados por trecho mostrando o menor preço histórico atingido e todas as coletas realizadas.
- **🛠️ Console de Diagnóstico em Tempo Real (Aba Avançado):**
  - Terminal integrado com live-tail dos logs estruturados (`JSONL`), filtros por severidade (`INFO`, `WARNING`, `ERROR`), busca textual e exportação `.log`.

---

## 🚀 Instalação Passo a Passo (Do Zero)

### 1. Pré-requisitos
- **Python 3.11+** instalado
- **Node.js 20+** (apenas se desejar recompilar o frontend Angular)

### 2. Clonar e instalar dependências
```powershell
git clone https://github.com/lucasmalvezzi/gilson-viagens.git
cd gilson-viagens

# Criar ambiente virtual e instalar pacotes Python
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt

# Instalar o navegador Chromium usado pelo Playwright
.\venv\Scripts\playwright install chromium
```

### 3. Compilar o Frontend Angular
```powershell
cd frontend
npm install
npm run build
cd ..
```

### 4. Iniciar o GilsonViagens
Dê duplo clique em [`iniciar.bat`](./iniciar.bat) ou execute no terminal:
```powershell
.\venv\Scripts\python.exe main.py
```
Acesse no navegador: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🪟 Usando o Agendador sem o Servidor Rodando

Cada busca ativa pode ter seus próprios horários (ex: `09:00, 18:00`) e ser marcada com **"🪟 Rodar no Agendador do Windows"**. Também é possível executar o coletor diretamente via CLI a qualquer momento:

```powershell
# Executar apenas uma busca específica pelo ID:
.\venv\Scripts\python.exe run_scheduled_search.py --config-id 1

# Executar todas as buscas ativas cadastradas:
.\venv\Scripts\python.exe run_scheduled_search.py --all
```

---

## 🧪 Testes Automatizados

O projeto possui uma suíte de testes unitários e de regressão **F.I.R.S.T** utilizando Fakes nomeados (sem depender de rede ou navegador real):

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

## 🤝 Como Contribuir

Contribuições são muito bem-vindas! Leia o nosso [Guia de Contribuição (`CONTRIBUTING.md`)](./CONTRIBUTING.md) e os padrões de código em [`GEMINI.md`](./GEMINI.md) antes de abrir um Pull Request.

---

## 📄 Licença (Copyleft / Recíproca)

Distribuído sob a licença **GNU General Public License v3.0 (GPL-3.0)**. Qualquer modificação ou trabalho derivado distribuído deve permanecer código aberto sob a mesma licença GPL-3.0. Veja o arquivo [`LICENSE`](./LICENSE) para mais detalhes.
