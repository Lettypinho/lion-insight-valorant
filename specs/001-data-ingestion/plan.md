# PLAN 001 — Ingestão de Dados

## Estratégia
1. Mapear os padrões de nomes de arquivos.
2. Criar loader de JSON.
3. Criar parser de metadados do filename.
4. Criar estrutura normalizada mínima.
5. Relacionar equipes externas com Red/Blue.
6. Gerar estruturas de consulta.
7. Validar contagens contra o inventário preliminar.
8. Adicionar cache.

## Riscos
- nomes fora do padrão;
- equipes com nomes semelhantes;
- caracteres especiais;
- campos ausentes;
- diferenças de schema.
