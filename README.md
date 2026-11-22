# Calculadora de Privilégios

Página web que mostra onde a renda e o patrimônio de uma casa estão na distribuição brasileira, comparados aos 50% com menos renda, ao 1% e ao 0,1% mais ricos.

Versão publicada: https://claude.ai/artifact/AWRzGqQ8SyLeW8BicrDPs9

## O que tem

- **Renda:** a pessoa informa a renda mensal da casa e quantas pessoas vivem dela. A página calcula a renda domiciliar per capita e mostra percentil, decil e faixa, uma pirâmide em seis camadas (dos 50% de menor renda ao 0,01% mais rico) com o marcador "você", a grade "se o Brasil fosse 100 pessoas", as fatias da renda e, opcionalmente, a curva detalhada percentil por percentil.
- **Patrimônio:** imóveis, veículos, investimentos, outros bens e dívidas, divididos pelo número de adultos. Mesma leitura, com a pirâmide da riqueza e dados do UBS.
- Na pirâmide, a largura de cada camada é proporcional ao tamanho do grupo em escala logarítmica, para que o topo continue visível.
- Página única em HTML, CSS e JavaScript, sem dependências além de fontes do Google Fonts. Funciona no celular, com tema claro e escuro. Nada do que é digitado sai do navegador.

## Como rodar

Abra `index.html` no navegador. Para servir localmente:

```bash
python3 -m http.server 8000
```

## Fontes dos dados

| Fonte | Ano | Uso |
|---|---|---|
| IBGE, PNAD Contínua, Rendimento de todas as fontes ([SIDRA 7526](https://sidra.ibge.gov.br/tabela/7526), [7530](https://sidra.ibge.gov.br/tabela/7530), [7531](https://sidra.ibge.gov.br/tabela/7531)) | 2025 | Limites P5 a P99 da renda domiciliar per capita e fatias da renda |
| Ministério da Fazenda, apresentação do PL nº 1.087/2025, com dados da Receita Federal (IRPF) | 2025 | Topo da renda: ~141 mil pessoas (0,06% da população) acima de R$ 600 mil/ano |
| [World Inequality Database](https://wid.world/country/brazil/), atualização de 2026 | 2024 (patrimônio), 2025 (renda) | Limites de patrimônio líquido por adulto e formato da cauda da renda acima de R$ 50 mil/mês |
| [UBS Global Wealth Report 2026](https://www.ubs.com/global/en/wealthmanagement/insights/global-wealth-report.html) | fim de 2025 | Adultos abaixo de US$ 10 mil, milionários em dólar, Gini da riqueza |

## Método

- Os percentis são aproximações, interpolados entre os limites publicados: em linha reta até o P99 e em escala logarítmica no 1% do topo.
- Entre o P99 do IBGE (R$ 15.214) e R$ 50 mil/mês, a curva segue uma distribuição de Pareto ligando o IBGE ao dado da Receita. Acima disso, segue as proporções entre os percentis do topo do WID.
- A renda por pessoa da casa é tratada como equivalente à renda individual da Receita. A PNAD subestima as rendas altas.
- O patrimônio do WID é por adulto (20 anos ou mais), com divisão igual dentro do casal.
- Valores em reais de 2025, sem correção pela inflação posterior.

## Atualizar os dados

```bash
python3 scripts/atualizar_dados.py 2025 2024 2025
```

Os argumentos são o ano da PNAD, o ano do patrimônio no WID e o ano da renda no WID. O script consulta a API do SIDRA e extrai só os arquivos do Brasil do pacote do WID (sem baixar os ~800 MB inteiros), e imprime as constantes `IBGE`, `WEALTH` e `WID_TAIL` para colar em `index.html`. O dado da Receita (`TOP_V`, `TOP_SHARE`) e os números do UBS são atualizados à mão, a partir dos documentos citados.
