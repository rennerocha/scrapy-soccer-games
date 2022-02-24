import scrapy
from scrapy.loader import ItemLoader
from soccer_games.items import SoccerGamesItem


def tratar_hora(hora):
    # Deixar data no padrão do projeto
    if not hora:
        return "00:00"
    return hora


def tratar_data(data):
    if not data:
        return "00/00/0000"
    return data


def rodada_jogo(nome_campeonato, numero_jogo, numero_jogos=10):
    # Usa o número do jogo para descobrir de qual rodada é. O numero_jogos é quantidade de jogos por rodada do campeonato.
    if "Copa do Nordeste" in nome_campeonato:
        numero_jogos = 8
    rodada = numero_jogo // numero_jogos
    if numero_jogo % numero_jogos != 0:
        rodada += 1
    return rodada


def obter_local(response):
    local = response.xpath(
        "//strong[contains(text(), 'Local')]/following-sibling::span/text()"
    ).get()

    local = local.split(" - ")
    if "a definir" in local[0].lower():
        local *= 3

    return local


serie_a = [
    f"https://www.cbf.com.br/amp/futebol-brasileiro/competicoes/campeonato-brasileiro-serie-a/2022/00{i+1}"
    for i in range(380)
]
serie_b = [
    f"https://www.cbf.com.br/amp/futebol-brasileiro/competicoes/campeonato-brasileiro-serie-b/2022/00{i+1}"
    for i in range(380)
]
serie_c = [
    f"https://www.cbf.com.br/amp/futebol-brasileiro/competicoes/campeonato-brasileiro-serie-c/2022/00{i+1}"
    for i in range(190)
]


class CbfGamesSpider(scrapy.Spider):
    name = "cbf_games"
    allowed_domains = ["cbf.com.br"]

    def start_requests(self):
        for idx in range(64):
            numero_jogo = idx + 1

            yield scrapy.Request(
                f"https://www.cbf.com.br/amp/futebol-brasileiro/competicoes/copa-nordeste-masculino/2022/00{numero_jogo}",
                cb_kwargs={
                    "numero_jogo": numero_jogo
                }
            )

    def parse(self, response, numero_jogo):
        jogo = ItemLoader(item=SoccerGamesItem(), response=response)
        jogo.add_xpath("nome_campeonato", "//strong/text()[1]")

        jogo.add_value("numero_jogo", numero_jogo)
        jogo.add_css(
            "time_mandante", ".jogo-equipe-nome-completo::text", lambda v: v[0]
        )
        jogo.add_css(
            "time_visitante",
            ".jogo-equipe-nome-completo::text",
            lambda v: v[1],
        )

        local_jogo = obter_local(response)
        jogo.add_value("estadio_jogo", local_jogo[0])
        jogo.add_value("cidade_jogo", local_jogo[1])
        jogo.add_value("estado_jogo", local_jogo[2])

        data_jogo = tratar_data(response.css(".col-xs-6 span::text").get())
        hora_jogo = tratar_hora(response.css(".col-xs-6 .text-6::text").get())

        jogo.add_value("data_jogo", data_jogo.replace("/", "-"))
        jogo.add_value("hora_jogo", hora_jogo)

        jogo.add_value(
            "rodada_jogo",
            rodada_jogo(jogo.get_output_value("nome_campeonato"), numero_jogo),
        )

        return jogo.load_item()
