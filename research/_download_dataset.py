"""Baixa o dataset curado do Mendeley (9xkhgts2s6, v4) via endpoint oficial.

Fluxo: public-api/zip/.../download/4  -> 302 -> URL S3 presigned -> zip (3.49 GB).
Suporta retomada (Range) e valida o SHA-256 conhecido.
"""
import os, sys, time, hashlib, urllib.request, urllib.error, ssl

DEST_DIR = r"C:\Projetos\Departamento_Medico_ML\_mendeley_raw"
ZIP_PATH = os.path.join(DEST_DIR, "dataset.zip")
os.makedirs(DEST_DIR, exist_ok=True)

DOWNLOAD_URL = "https://data.mendeley.com/public-api/zip/9xkhgts2s6/download/4"
SHA256_ESPERADO = "cda852586b954a52bf184dd72d70a2f9a427d04e52e1bfa13e8c913be54b87dc"
TAMANHO_ESPERADO = 3747510717

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def resolver_url_s3():
    """Segue o 302 e devolve a URL S3 presigned."""
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=ctx, timeout=90) as r:
        return r.geturl()


def baixar():
    ja_baixado = os.path.getsize(ZIP_PATH) if os.path.exists(ZIP_PATH) else 0
    if ja_baixado >= TAMANHO_ESPERADO:
        print(f"Zip ja existe com {ja_baixado/1e6:.0f} MB; pulando download.", flush=True)
        return
    url_s3 = resolver_url_s3()
    print(f"URL S3 resolvida (presigned). Retomando de {ja_baixado/1e6:.0f} MB.", flush=True)
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if ja_baixado:
        headers["Range"] = f"bytes={ja_baixado}-"
    req = urllib.request.Request(url_s3, headers=headers)
    modo = "ab" if ja_baixado else "wb"
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        total = TAMANHO_ESPERADO
        baixado = ja_baixado
        t0 = time.time()
        ultimo = 0
        with open(ZIP_PATH, modo) as f:
            while True:
                chunk = resp.read(1 << 20)  # 1 MB
                if not chunk:
                    break
                f.write(chunk)
                baixado += len(chunk)
                if baixado - ultimo >= (50 << 20):  # a cada 50 MB
                    ultimo = baixado
                    pct = 100 * baixado / total
                    vel = (baixado - ja_baixado) / 1e6 / max(time.time() - t0, 1e-6)
                    print(f"  {pct:5.1f}%  ({baixado/1e6:.0f}/{total/1e6:.0f} MB)  {vel:.1f} MB/s", flush=True)
    print(f"Download concluido: {os.path.getsize(ZIP_PATH)/1e6:.0f} MB", flush=True)


def verificar_sha256():
    print("Verificando SHA-256...", flush=True)
    h = hashlib.sha256()
    with open(ZIP_PATH, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    digest = h.hexdigest()
    ok = digest == SHA256_ESPERADO
    print(f"  SHA-256: {digest}", flush=True)
    print(f"  {'OK - integridade confirmada' if ok else 'FALHA - hash divergente!'}", flush=True)
    return ok


if __name__ == "__main__":
    # Loop resiliente: retoma automaticamente a cada queda de conexao
    MAX_TENTATIVAS = 200
    tentativa = 0
    while True:
        tentativa += 1
        atual = os.path.getsize(ZIP_PATH) if os.path.exists(ZIP_PATH) else 0
        if atual >= TAMANHO_ESPERADO:
            break
        print(f"[tentativa {tentativa}] retomando de {atual/1e6:.0f} MB", flush=True)
        try:
            baixar()
        except Exception as e:
            print(f"  queda: {e!r} - nova tentativa em 3s", flush=True)
            time.sleep(3)
        if tentativa >= MAX_TENTATIVAS:
            print("ERRO: excedeu numero maximo de tentativas", flush=True)
            sys.exit(1)
    if not verificar_sha256():
        print("ERRO: hash divergente apos download completo", flush=True)
        sys.exit(2)
    print("PRONTO.", flush=True)
