"""LECTOR - OCR forense offline para PDF e imagens.

Gera, para cada arquivo: PDF pesquisavel (_OCR.pdf) e texto (_OCR.txt).
Gera, por lote: relatorio de processamento com SHA-256 dos originais e produtos.
Nenhum dado sai da maquina: OCR local (Tesseract embutido no MuPDF).

Uso: duplo clique (interface) ou  LECTOR.exe arquivo1.pdf foto.jpg ...
"""
import getpass, hashlib, os, platform, queue, sys, threading
from datetime import datetime
import pymupdf

VERSAO = "1.0.0"
IDIOMA = "por+eng"
EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")
MIN_CHARS_NATIVO = 25  # abaixo disso a pagina e tratada como imagem e vai para OCR
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
TESSDATA = os.path.join(BASE, "tessdata")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest().upper()


def processar_arquivo(path, saida, dpi=300, forcar=False, log=print):
    nome = os.path.splitext(os.path.basename(path))[0]
    pdf_out = os.path.join(saida, f"{nome}_OCR.pdf")
    txt_out = os.path.join(saida, f"{nome}_OCR.txt")
    hash_antes = sha256(path)

    src = pymupdf.open(path)
    if src.needs_pass:
        raise ValueError("PDF protegido por senha")
    dst, textos, n_ocr = pymupdf.open(), [], 0
    for i, page in enumerate(src):
        texto = page.get_text() if src.is_pdf else ""
        if forcar or len(texto.strip()) < MIN_CHARS_NATIVO:
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            ocr = pymupdf.open("pdf", pix.pdfocr_tobytes(language=IDIOMA, tessdata=TESSDATA))
            texto = ocr[0].get_text()
            dst.insert_pdf(ocr)
            n_ocr += 1
            metodo = "OCR"
        else:
            dst.insert_pdf(src, from_page=i, to_page=i)
            metodo = "texto nativo"
        textos.append(f"===== PAGINA {i + 1} ({metodo}) =====\n{texto.strip()}\n")
        log(f"  pag. {i + 1}/{len(src)} - {metodo}")
    total = len(src)
    src.close()

    dst.save(pdf_out, garbage=3, deflate=True)
    dst.close()
    with open(txt_out, "w", encoding="utf-8") as f:
        f.write("\n".join(textos))

    hash_depois = sha256(path)
    return {
        "arquivo": path, "paginas": total, "paginas_ocr": n_ocr,
        "sha_original": hash_antes, "integro": hash_antes == hash_depois,
        "produtos": [(p, sha256(p)) for p in (pdf_out, txt_out)],
    }


def processar_lote(arquivos, saida, dpi=300, forcar=False, log=print):
    os.makedirs(saida, exist_ok=True)
    inicio = datetime.now().astimezone()
    linhas, erros = [], 0
    for n, path in enumerate(arquivos, 1):
        log(f"[{n}/{len(arquivos)}] {os.path.basename(path)}")
        try:
            r = processar_arquivo(path, saida, dpi, forcar, log)
            linhas += [
                f"ARQUIVO {n}: {r['arquivo']}",
                f"  SHA-256 original ........: {r['sha_original']}",
                f"  Original inalterado .....: {'SIM' if r['integro'] else 'NAO - VERIFICAR'}",
                f"  Paginas / com OCR .......: {r['paginas']} / {r['paginas_ocr']}",
            ] + [f"  Produto: {os.path.basename(p)}\n    SHA-256: {h}" for p, h in r["produtos"]] + [""]
        except Exception as e:
            erros += 1
            linhas += [f"ARQUIVO {n}: {path}", f"  ERRO: {e}", ""]
            log(f"  ERRO: {e}")
    fim = datetime.now().astimezone()

    rel = os.path.join(saida, f"relatorio_processamento_{inicio:%Y%m%d_%H%M%S}.txt")
    cab = [
        "RELATORIO DE PROCESSAMENTO - EXTRACAO DE TEXTO POR OCR",
        "=" * 60,
        f"Ferramenta ......: LECTOR {VERSAO} (PyMuPDF {pymupdf.VersionBind} / MuPDF {pymupdf.VersionFitz}, Tesseract embutido)",
        f"Idioma OCR ......: {IDIOMA}   Resolucao: {dpi} dpi   OCR forcado: {'sim' if forcar else 'nao'}",
        f"Estacao .........: {platform.node()} - {platform.platform()}",
        f"Usuario do SO ...: {getpass.getuser()}",
        f"Inicio / Fim ....: {inicio:%d/%m/%Y %H:%M:%S %z} / {fim:%d/%m/%Y %H:%M:%S %z}",
        f"Arquivos ........: {len(arquivos)} (erros: {erros})",
        "",
        "OBSERVACAO: o texto obtido por OCR e transcricao automatizada, sujeita a erros de",
        "reconhecimento. Todo trecho utilizado em peca deve ser conferido com o original.",
        "Os arquivos originais foram apenas lidos; o hash SHA-256 foi calculado antes e",
        "depois do processamento para demonstrar a ausencia de alteracao.",
        "=" * 60, "",
    ]
    with open(rel, "w", encoding="utf-8") as f:
        f.write("\n".join(cab + linhas))
    log(f"\nConcluido. Relatorio: {rel}")
    return rel


def expandir(caminhos):
    out = []
    for c in caminhos:
        if os.path.isdir(c):
            out += sorted(os.path.join(c, f) for f in os.listdir(c) if f.lower().endswith(EXTS))
        elif c.lower().endswith(EXTS):
            out.append(c)
    return out


def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title(f"LECTOR {VERSAO} - OCR forense offline")
    root.geometry("720x520")
    arquivos, q = [], queue.Queue()
    dpi, forcar = tk.IntVar(value=300), tk.BooleanVar(value=False)

    lista = tk.Listbox(root, height=8)
    logbox = tk.Text(root, height=14, state="disabled", bg="#111", fg="#9f9")

    def add(novos):
        for a in expandir(novos):
            if a not in arquivos:
                arquivos.append(a)
                lista.insert("end", a)

    def log(msg):
        q.put(msg)

    def poll():
        while not q.empty():
            msg = q.get()
            if msg == "__FIM__":
                btn.config(state="normal")
                continue
            logbox.config(state="normal"); logbox.insert("end", msg + "\n")
            logbox.see("end"); logbox.config(state="disabled")
        root.after(150, poll)

    def iniciar():
        if not arquivos:
            return messagebox.showwarning("LECTOR", "Adicione ao menos um arquivo.")
        saida = filedialog.askdirectory(title="Pasta de saida (nao use a pasta dos originais)")
        if not saida:
            return
        btn.config(state="disabled")
        def run():
            try:
                processar_lote(list(arquivos), saida, dpi.get(), forcar.get(), log)
                os.startfile(saida) if os.name == "nt" else None
            finally:
                log("__FIM__")
        threading.Thread(target=run, daemon=True).start()

    barra = tk.Frame(root); barra.pack(fill="x", padx=8, pady=6)
    tk.Button(barra, text="Adicionar arquivos", command=lambda: add(filedialog.askopenfilenames(
        filetypes=[("PDF e imagens", " ".join("*" + e for e in EXTS))]))).pack(side="left")
    tk.Button(barra, text="Adicionar pasta", command=lambda: add([filedialog.askdirectory()])).pack(side="left", padx=4)
    tk.Button(barra, text="Limpar", command=lambda: (arquivos.clear(), lista.delete(0, "end"))).pack(side="left")
    tk.Label(barra, text="  DPI:").pack(side="left")
    ttk.Combobox(barra, textvariable=dpi, values=(200, 300, 400), width=5, state="readonly").pack(side="left")
    tk.Checkbutton(barra, text="Forcar OCR em todas as paginas", variable=forcar).pack(side="left", padx=6)
    lista.pack(fill="x", padx=8)
    btn = tk.Button(root, text="PROCESSAR", bg="#1d3557", fg="white", command=iniciar)
    btn.pack(fill="x", padx=8, pady=6)
    logbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    poll()
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:  # modo linha de comando / arrastar arquivos sobre o .exe
        arqs = expandir(sys.argv[1:])
        if not arqs:
            sys.exit("Nenhum PDF/imagem valido informado.")
        processar_lote(arqs, os.path.join(os.path.dirname(os.path.abspath(arqs[0])), "LECTOR_saida"))
    else:
        gui()
