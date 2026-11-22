#!/usr/bin/env python3
"""Baixa e imprime os números usados em index.html.

Uso: python3 scripts/atualizar_dados.py [ano_ibge] [ano_wid_patrimonio] [ano_wid_renda]
Exemplo: python3 scripts/atualizar_dados.py 2025 2024 2025

- IBGE (SIDRA): limites dos percentis da renda domiciliar per capita (tabela 7526)
  e distribuição da massa de rendimento (tabela 7530).
- WID: extrai só os arquivos do Brasil do pacote completo (≈800 MB) usando
  requisições HTTP com Range, sem baixar o pacote inteiro.

Os resultados saem no terminal para serem copiados para as constantes
IBGE, WID_TAIL e WEALTH em index.html.
"""
import csv
import io
import json
import sys
import tempfile
import urllib.request
import zipfile

ANO_IBGE = sys.argv[1] if len(sys.argv) > 1 else "2025"
ANO_WEALTH = sys.argv[2] if len(sys.argv) > 2 else "2024"
ANO_RENDA_WID = sys.argv[3] if len(sys.argv) > 3 else "2025"
WID_ZIP = "https://wid.world/bulk_download/wid_all_data.zip"


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def ibge():
    lim = get_json(f"https://apisidra.ibge.gov.br/values/t/7526/n1/all/v/10838/p/{ANO_IBGE}/c1019/all")
    pares = [[0, 0]]
    for r in lim[1:]:
        if r["D4N"].startswith("P"):
            pares.append([int(r["D4N"][1:]), int(r["V"])])
    print(f"IBGE {ANO_IBGE} limites (tabela 7526):")
    print("  const IBGE = " + json.dumps(pares, separators=(",", ":")) + ";")
    massa = get_json(f"https://apisidra.ibge.gov.br/values/t/7530/n1/all/v/10826/p/{ANO_IBGE}/c1042/all")
    print(f"IBGE {ANO_IBGE} massa acumulada (tabela 7530):")
    for r in massa[1:]:
        print(f"  {r['D4N']}: {r['V']}%")


class HttpRange(io.RawIOBase):
    """Arquivo somente leitura sobre HTTP Range, para o zipfile ler só o que precisa."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        head = urllib.request.Request(url, method="HEAD")
        self.size = int(urllib.request.urlopen(head, timeout=60).headers["Content-Length"])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(b), self.size) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        data = urllib.request.urlopen(req, timeout=120).read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def thresholds(rows, var, year):
    """Limiar de cada g-percentil pXpY com largura <= 1 (ex.: p50p51, p99.9p99.91)."""
    out = {}
    for r in rows:
        if r[1] == var and r[3] == year:
            a, b = r[2][1:].split("p")
            if float(b) - float(a) <= 1.0001 and r[2] != "p0p100":
                out[float(a)] = float(r[4])
    return dict(sorted(out.items()))


def wid():
    zf = zipfile.ZipFile(io.BufferedReader(HttpRange(WID_ZIP), buffer_size=1 << 20))
    with tempfile.TemporaryFile("w+", encoding="utf-8") as tmp:
        nome = next(n for n in zf.namelist() if n.endswith("WID_data_BR.csv"))
        with zf.open(nome) as f:
            tmp.write(f.read().decode("utf-8"))
        tmp.seek(0)
        rows = [r for r in csv.reader(tmp, delimiter=";") if r[1] in ("thweal992j", "tptinc992j", "shweal992j")]

    w = thresholds(rows, "thweal992j", ANO_WEALTH)
    keep = [p for p in w if p == int(p)
            or (99 < p and round(p * 10) == p * 10)
            or (99.9 < p and round(p * 100) == p * 100)
            or (99.99 < p and round(p * 1000) == p * 1000)]
    tabela = [[int(p) if p == int(p) else p, round(w[p])] for p in keep]
    print(f"\nWID patrimônio por adulto {ANO_WEALTH} (thweal992j, R$ do último ano):")
    print("  const WEALTH = " + json.dumps(tabela, separators=(",", ":")) + ";")

    s = {r[2]: float(r[4]) for r in rows if r[1] == "shweal992j" and r[3] == ANO_WEALTH}
    print("  fatias: 50% de baixo {:.1%}, 50-90 {:.1%}, 90-99 {:.1%}, 1% {:.1%}".format(
        s["p0p50"], s["p50p90"], s["p90p100"] - s["p99p100"], s["p99p100"]))

    i = thresholds(rows, "tptinc992j", ANO_RENDA_WID)
    base = i[99.94]
    tail = [[p, round(i[p] / base, 3)] for p in i if p > 99.94]
    print(f"\nWID renda pré-imposto {ANO_RENDA_WID} (tptinc992j), limiar ÷ limiar do P99,94:")
    print("  const WID_TAIL = " + json.dumps(tail, separators=(",", ":")) + ";")


if __name__ == "__main__":
    ibge()
    wid()
