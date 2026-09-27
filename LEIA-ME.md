# LECTOR 1.0 — OCR forense offline (PDF e imagens)

## O que faz
- Entrada: PDF, JPG, PNG, TIFF (multipágina), BMP, WEBP — arquivos avulsos ou pasta inteira.
- Páginas com texto digital são copiadas como estão; páginas-imagem passam por OCR (português + inglês).
- Saídas por arquivo: `nome_OCR.pdf` (pesquisável com Ctrl+F, texto selecionável) e `nome_OCR.txt` (separado por página, indicando OCR ou texto nativo).
- Saída por lote: `relatorio_processamento_AAAAMMDD_HHMMSS.txt` com SHA-256 dos originais (antes/depois) e dos produtos, versão do motor, DPI, estação, usuário e horário com fuso.
- 100% offline. Original nunca é alterado.

## Uso
- Duplo clique → Adicionar arquivos/pasta → PROCESSAR → escolher pasta de saída.
- Ou arrastar arquivos sobre o `LECTOR.exe` (saída em `LECTOR_saida`, ao lado do primeiro arquivo).
- "Forçar OCR": use quando o PDF tem camada de texto ruim/corrompida. DPI 400 para letras pequenas.

## Gerar o .exe SEM terminal (GitHub, pelo navegador)
1. Crie conta em https://github.com e um repositório **privado** (New repository → Private).
2. "uploading an existing file" → arraste `lector.py`, `build.bat`, `LEIA-ME.md` → Commit.
3. "Add file → Create new file" → nome: `.github/workflows/build.yml` → cole o conteúdo do arquivo `build.yml` → Commit.
4. Aba **Actions** → "Gerar LECTOR.exe" → aguarde ~3 min (círculo verde) → baixe o artefato **LECTOR** (zip com `LECTOR.exe` e seu hash).

## Alternativa: computador com Python instalado
Duplo clique em `build.bat` → executável em `dist\LECTOR.exe`.
