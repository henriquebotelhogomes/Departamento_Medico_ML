"""Monta subconjunto balanceado do dataset Mendeley e exclui duplicatas vs Test/.

- Le o zip em _mendeley_raw/dataset.zip (sem extrair tudo).
- Classifica cada imagem por palavra-chave no caminho:
    0=Covid-19, 1=Normal, 2=Pneumonia viral, 3=Pneumonia bacteriana
- Exclui imagens perceptualmente iguais (dHash) as do Test/ atual (evita leakage).
- Amostra ate N_POR_CLASSE por classe em Dataset_mendeley/{0,1,2,3}.
"""
import os, sys, io, zipfile, random, hashlib
from collections import defaultdict
from PIL import Image
import numpy as np

ZIP_PATH = r"C:\Projetos\Departamento_Medico_ML\_mendeley_raw\dataset.zip"
OUT_DIR = r"C:\Projetos\Departamento_Medico_ML\Dataset_mendeley"
TEST_DIR = r"C:\Projetos\Departamento_Medico_ML\Test"
N_POR_CLASSE = 1200
SEED = 42
IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

random.seed(SEED)


def classificar(caminho):
    """Classifica pela pasta-pai imediata (evita contaminacao do nome da raiz).

    Ordem: termos especificos primeiro (bacterial/viral pneumonia) antes de
    normal/covid, e ignora o segmento raiz do zip.
    """
    partes = [s for s in caminho.replace("\\", "/").split("/") if s]
    # pasta-pai imediata do arquivo (ultimo diretorio antes do nome)
    pai = partes[-2].lower() if len(partes) >= 2 else ""
    for chave in (pai,):
        if "bacter" in chave:
            return "3"
        if "viral" in chave:
            return "2"
        if "normal" in chave:
            return "1"
        if "covid" in chave:
            return "0"
    return None


def dhash_bytes(raw, hash_size=8):
    """dHash perceptual (robusto a re-encode/resize) a partir de bytes."""
    try:
        img = Image.open(io.BytesIO(raw)).convert("L").resize((hash_size + 1, hash_size))
    except Exception:
        return None
    a = np.asarray(img, dtype=np.int16)
    diff = a[:, 1:] > a[:, :-1]
    bits = 0
    for b in diff.flatten():
        bits = (bits << 1) | int(b)
    return bits


def main():
    if not os.path.exists(ZIP_PATH):
        print("ERRO: zip nao encontrado.", flush=True)
        sys.exit(1)

    # 1) hashes das imagens de Test/ (para excluir duplicatas)
    print("Calculando hashes perceptuais do Test/ ...", flush=True)
    test_hashes = set()
    for raiz, _, arqs in os.walk(TEST_DIR):
        for a in arqs:
            if a.lower().endswith(IMG_EXT):
                with open(os.path.join(raiz, a), "rb") as f:
                    h = dhash_bytes(f.read())
                    if h is not None:
                        test_hashes.add(h)
    print(f"  {len(test_hashes)} hashes de teste", flush=True)

    # 2) candidatos por classe
    print("Lendo indice do zip ...", flush=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        entradas = [n for n in z.namelist()
                    if n.lower().endswith(IMG_EXT) and not n.endswith("/")]
        por_classe = defaultdict(list)
        for n in entradas:
            c = classificar(n)
            if c:
                por_classe[c].append(n)
        print("  candidatos:", {k: len(v) for k, v in sorted(por_classe.items())}, flush=True)

        for c in ("0", "1", "2", "3"):
            os.makedirs(os.path.join(OUT_DIR, c), exist_ok=True)

        resumo = {}
        dup_total = 0
        for c in ("0", "1", "2", "3"):
            cands = por_classe.get(c, [])
            random.shuffle(cands)
            salvos, dups_test, dups_int = 0, 0, 0
            hashes_classe = set()
            for n in cands:
                if salvos >= N_POR_CLASSE:
                    break
                try:
                    raw = z.read(n)
                except Exception:
                    continue  # pula arquivo corrompido (CRC invalido)
                h = dhash_bytes(raw)
                if h is None:
                    continue
                if h in test_hashes:
                    dups_test += 1
                    continue
                if h in hashes_classe:
                    dups_int += 1
                    continue
                hashes_classe.add(h)
                ext = os.path.splitext(n)[1].lower()
                with open(os.path.join(OUT_DIR, c, f"{c}_{salvos:04d}{ext}"), "wb") as fo:
                    fo.write(raw)
                salvos += 1
            dup_total += dups_test
            resumo[c] = dict(salvos=salvos, dups_test=dups_test, dups_internas=dups_int,
                             candidatos=len(cands))
            print(f"  classe {c}: salvos={salvos}  dups_test={dups_test}  "
                  f"dups_internas={dups_int}  candidatos={len(cands)}", flush=True)

    print("\n=== RESUMO ===", flush=True)
    print("Duplicatas com Test/ excluidas (total):", dup_total, flush=True)
    for c, r in resumo.items():
        print(f"  {c}: {r}", flush=True)
    print("PRONTO.", flush=True)


if __name__ == "__main__":
    main()
