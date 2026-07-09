# Padrão de Governança de Checks

1) Obrigatórios para merge em `main`: `validar-bases` (e demais checks de qualidade que validem conteúdo/integração).
2) Obrigatórios condicionais: testes/lint só quando houver alteração em código (não apenas docs/ops).
3) Informativos (não bloqueantes): deploy de preview e jobs de observabilidade/telemetria em branches de PR.
4) GitHub Pages: deploy somente em `main` (ou manual), nunca bloqueando PR de feature branch.
5) Regra de proteção: exigir branch atualizada + pelo menos 1 aprovação + todos checks obrigatórios verdes.
6) Exceções: qualquer bypass deve ser raro, justificado no comentário de merge e registrado no histórico da PR.
