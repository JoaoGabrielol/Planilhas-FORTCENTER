# 📊 Ferramenta de Análise Financeira de Despesas

Este projeto oferece uma interface interativa para análise detalhada de despesas financeiras, auxiliando na gestão e visualização dos gastos da sua organização.

---

## 🚀 Principais Funcionalidades
- **Filtros Dinâmicos:** Explora despesas por período, grupo, tipo ou usuário com um painel de filtros intuitivo.
- **Visualizações de Gráficos:** Monte gráficos interativos em tempo real para análise de despesas por categoria e usuário.
- **Relatórios Personalizáveis:** Exporte dados filtrados em formato Excel diretamente pelo aplicativo.
- **Segurança e Automação:** Integração com Microsoft Graph para obter planilhas diretamente do OneDrive, utilizando autenticação OAuth2.
- **Padronização Automática:** Processa os dados para uniformizar textos e tratar valores numéricos inconsistentes.

---

## ⚙️ Configuração

### 1️⃣ Configurar Variáveis de Ambiente
Crie um arquivo `.env` no diretório do projeto com as seguintes informações:

```plaintext
id_do_cliente=<SEU_CLIENT_ID>
segredo=<SEU_CLIENT_SECRET>
tenant_id=<SEU_TENANT_ID>
drive_id=<SEU_DRIVE_ID>
