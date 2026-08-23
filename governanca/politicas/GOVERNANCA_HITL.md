# Politica de Governanca Human-in-the-Loop

## Controles obrigatorios

- `main` deve exigir Pull Request antes de merge.
- Deve existir ao menos uma aprovacao humana para alteracoes.
- A aprovacao mais recente deve ser invalidada quando novo codigo for enviado.
- Conversas de revisao devem ser resolvidas antes do merge.
- O agente nao deve possuir bypass de ruleset ou branch protection.
- PRs do agente devem identificar o commit e a evidencia que originaram a proposta.
- Mudancas em `.github/`, `agente_governanca/` e `governanca/politicas/` exigem
  revisao de CODEOWNER quando esse recurso estiver habilitado.

## Separacao de privilegios

Analises de commits nao confiaveis devem usar token somente leitura e nao devem
receber secrets. Analises de Pull Request com acesso ao modelo devem executar o
codigo do governador vindo da branch protegida e tratar o checkout da PR apenas
como dados, sem instalar dependencias nem executar scripts desse checkout.

## Excecoes

Uma excecao deve registrar proprietario, justificativa, risco residual, controles
compensatorios e data de expiracao. O agente pode recomendar uma excecao, mas nao
pode aprova-la.
