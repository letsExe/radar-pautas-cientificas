# Radar de Pautas Científicas

Ferramenta de apoio à prospecção de pautas jornalísticas a partir de publicações científicas de pesquisadores da UNILA.

O sistema monitora publicações recentes em bases públicas (OpenAlex) e usa um modelo de linguagem (LLM), acessado por API, para avaliar o potencial de cada artigo para divulgação, segundo critérios de noticiabilidade: interesse público, relevância social, novidade, proximidade regional e comunicabilidade.

**A IA não escreve a matéria nem decide a pauta.** Ela destaca pesquisas que poderiam passar despercebidas, justifica a nota e sugere enfoques para a pré-apuração. A decisão de transformar o artigo em pauta e a apuração continuam sendo do jornalista.

> Projeto desenvolvido para a disciplina de Aplicações em Inteligência Artificial do Mestrado em Gestão, Tecnologia e Sustentabilidade da Unioeste (Foz do Iguaçu).

**Status:** em desenvolvimento.

## Como funciona

```
OpenAlex -> Python (orquestração) -> LLM via API
                  |                      |
                  +----> Supabase <------+
                            |
                        Streamlit
```

1. **Coleta:** o Python consulta a API do OpenAlex e recupera as publicações vinculadas à UNILA (título, resumo, autores, data, DOI, periódico, área).
2. **Análise:** título, resumo e metadados são enviados a uma LLM junto com uma rubrica de critérios. A LLM devolve uma nota e uma justificativa por critério, além de possíveis enfoques.
3. **Armazenamento:** artigos, análises e validações ficam no Supabase (PostgreSQL), mantendo o histórico.
4. **Visualização:** a interface em Streamlit exibe o ranking por score, filtros e os detalhes de cada análise, e permite que jornalistas registrem se concordam ou discordam da IA.

## Tecnologias

- Python
- API do OpenAlex (pública e gratuita)
- LLM via API (Gemini ou DeepSeek)
- Supabase (PostgreSQL)
- Streamlit

## Estrutura do repositório

Será detalhada à medida que o projeto for construído.

## Licença

A definir.
