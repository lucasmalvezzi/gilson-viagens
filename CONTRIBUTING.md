# Contribuindo com o GilsonViagens 🦎✈️

Obrigado pelo interesse em contribuir com o **GilsonViagens**! Este projeto segue padrões rigorosos de engenharia para manter o código limpo, testável e fácil de manter.

---

## 🛠️ Configuração do Ambiente de Desenvolvimento

1. **Clone o repositório:**
   ```powershell
   git clone https://github.com/lucasmalvezzi/gilson-viagens.git
   cd gilson-viagens
   ```

2. **Configure o ambiente virtual Python:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\pip install -r requirements.txt
   .\venv\Scripts\playwright install chromium
   ```

3. **Compile o frontend Angular (opcional se fizer alterações de UI):**
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

---

## 📏 Padrões de Código (Obrigatórios em PRs)

Todas as regras estão documentadas em [`GEMINI.md`](./GEMINI.md):

- **Funções curtas:** entre **4 e 20 linhas**. Divida se ficar maior.
- **Arquivos enxutos:** abaixo de **500 linhas**, separados por responsabilidade única (SRP).
- **Tipagem explícita:** sem `any` no TypeScript e sem `Dict` genérico ou funções sem anotação de tipo no Python (prefira `TypedDict` ou `BaseModel`).
- **Retorno antecipado (Early Returns):** máximo de **2 níveis de indentação** dentro de funções.
- **Nomes específicos:** evite identificadores genéricos como `data`, `handler` ou `Manager`.
- **Injeção de Dependência:** isole bibliotecas externas (Playwright, HTTPX, agendador do SO) atrás de protocolos em `app/gateways/` e injete-as por parâmetro/construtor.
- **Mensagens de Exceção:** devem incluir o valor ofensivo e o formato esperado.

---

## 🧪 Executando os Testes

Toda nova função deve vir acompanhada de teste unitário e toda correção de bug deve ter um teste de regressão usando **Fakes nomeados** (`tests/fakes.py`):

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

## 🚀 Enviando um Pull Request

1. Crie uma branch descritiva: `git checkout -b feat/minha-melhoria`
2. Certifique-se de que todos os testes passam (`.\venv\Scripts\python.exe -m unittest discover -s tests -v`).
3. Caso tenha alterado arquivos em `frontend/src/`, execute `npm run build` dentro de `frontend/`.
4. Abra o Pull Request descrevendo o motivo da alteração.
