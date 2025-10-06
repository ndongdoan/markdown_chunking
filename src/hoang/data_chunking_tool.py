import re
from pathlib import Path
from unidecode import unidecode
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


def slugify(text):
    text_ascii = unidecode(text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text_ascii).strip("-").lower()
    return slug[:80] if slug else "untitled"


def chunk_markdown_by_headings(file_content):
    """
    Split by H2 sections (lines starting with '## ').
    """
    lines = file_content.splitlines()
    chunks, current_chunk_lines, inside_article = [], [], False
    for line in lines:
        if line.startswith("## "):
            if current_chunk_lines:
                chunks.append("\n".join(current_chunk_lines).strip())
            current_chunk_lines = [line]
            inside_article = True
        elif inside_article:
            current_chunk_lines.append(line)
    if current_chunk_lines:
        chunks.append("\n".join(current_chunk_lines).strip())
    return [c for c in chunks if c.strip()]


def split_large_chunk(chunk, max_bytes):
    """
    If a single chunk exceeds max_bytes, try to split it by '### ' subheadings,
    then by paragraphs, then by byte wrapping.
    """
    if len(chunk.encode("utf-8")) <= max_bytes:
        return [chunk]

    # 1) Split by '### '
    parts, lines, temp = [], chunk.splitlines(), []
    for line in lines:
        if line.startswith("### ") and temp:
            parts.append("\n".join(temp).strip())
            temp = [line]
        else:
            temp.append(line)
    if temp:
        parts.append("\n".join(temp).strip())

    if len(parts) > 1:
        refined = []
        for p in parts:
            refined.extend(split_large_chunk(p, max_bytes))
        return refined

    # 2) Split by paragraphs
    paragraphs = chunk.split("\n\n")
    current, out = [], []

    def flush_current():
        if current:
            out.append("\n\n".join(current).strip())

    for para in paragraphs:
        tentative = ("\n\n".join(current + [para])).strip()
        if len(tentative.encode("utf-8")) > max_bytes:
            flush_current()
            current = [para]
            if len(para.encode("utf-8")) > max_bytes:
                out.extend(hard_wrap_by_bytes(para, max_bytes))
                current = []
        else:
            current.append(para)
    flush_current()

    final = []
    for piece in out:
        if len(piece.encode("utf-8")) > max_bytes:
            final.extend(hard_wrap_by_bytes(piece, max_bytes))
        else:
            final.append(piece)
    return [p for p in final if p.strip()]


def hard_wrap_by_bytes(text, max_bytes):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces, buf = [], ""
    for s in sentences:
        candidate = (buf + " " + s).strip() if buf else s
        if len(candidate.encode("utf-8")) <= max_bytes:
            buf = candidate
        else:
            if buf:
                pieces.append(buf)
            if len(s.encode("utf-8")) > max_bytes:
                pieces.extend(char_wrap_by_bytes(s, max_bytes))
                buf = ""
            else:
                buf = s
    if buf:
        pieces.append(buf)
    return pieces


def char_wrap_by_bytes(text, max_bytes):
    out, buf = [], []
    for ch in text:
        buf.append(ch)
        if len("".join(buf).encode("utf-8")) > max_bytes:
            last = buf.pop()
            piece = "".join(buf)
            if piece:
                out.append(piece)
            buf = [last]
    if buf:
        out.append("".join(buf))
    return out


def get_cluster_labels(clusters, n_terms=3):
    cluster_texts = [" ".join(chunks) for chunks in clusters.values()]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=None, max_df=0.7)

    try:
        tfidf_matrix = vectorizer.fit_transform(cluster_texts)
        feature_names = np.array(vectorizer.get_feature_names_out())
        dense = tfidf_matrix.toarray()
    except ValueError:
        return {cid: f"Chủ đề #{cid+1}" for cid in clusters.keys()}

    labels = {}
    for i in range(len(clusters)):
        row = dense[i]
        if row.size == 0 or not np.any(row):
            labels[i] = f"Chủ đề #{i+1}"
            continue
        top_term_indices = row.argsort()[-n_terms:][::-1]
        top_terms = feature_names[top_term_indices]
        labels[i] = " ".join(top_terms)
    return labels


def build_file_bytes(chunks, title_raw):
    header = f"# CHỦ ĐỀ: {title_raw.upper()}\n\n"
    body = "\n\n---\n\n".join(chunks)
    content = header + body
    return len(content.encode("utf-8")), content


def compute_cluster_sizes_bytes(clusters, cluster_titles):
    per_cluster_sizes = {}
    per_cluster_contents = {}
    for cid, chs in clusters.items():
        title = cluster_titles.get(cid, f"chủ đề {cid+1}")
        size_b, content = build_file_bytes(chs, title)
        per_cluster_sizes[cid] = size_b
        per_cluster_contents[cid] = content
    max_size = max(per_cluster_sizes.values()) if per_cluster_sizes else 0
    return max_size, per_cluster_sizes, per_cluster_contents


def save_clusters_to_files(clusters, cluster_titles, output_folder):
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    print(f"\n--- ĐANG XUẤT FILE RA THƯ MỤC: {output_folder} ---")

    for cluster_id, chunks in clusters.items():
        title_raw = cluster_titles.get(cluster_id, f"chủ đề {cluster_id+1}")
        filename_slug = slugify(title_raw)
        filename = f"{cluster_id+1:02d}-{filename_slug}.md"
        filepath = Path(output_folder) / filename

        _, content = build_file_bytes(chunks, title_raw)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"    [OK] Đã tạo file: {filename}")
        except Exception as e:
            print(f"    [LỖI] Không thể ghi file {filename}: {e}")


# ------------------------------
# Clustering core (size-constrained)
# ------------------------------

def cluster_with_k(corpus, embeddings, k, random_state=42):
    kmeans = KMeans(n_clusters=k, random_state=random_state, n_init='auto')
    labels = kmeans.fit_predict(embeddings)
    clusters = {i: [] for i in range(k)}
    for i, lab in enumerate(labels):
        clusters[lab].append(corpus[i])
    return clusters


def choose_k_by_max_file_size(corpus, embeddings, max_bytes, k_min=1):
    if not corpus:
        raise ValueError("Corpus is empty after chunking.")

    overs = [i for i, c in enumerate(corpus) if len(c.encode("utf-8")) > max_bytes]
    if overs:
        print("CẢNH BÁO: Có chunk vượt giới hạn trước khi phân cụm; đã cố gắng chia nhỏ.")

    n = len(corpus)
    for k in range(max(k_min, 1), n + 1):
        clusters = cluster_with_k(corpus, embeddings, k)
        titles = get_cluster_labels(clusters)
        max_size, sizes, contents = compute_cluster_sizes_bytes(clusters, titles)
        print(f"    - Thử K={k}: file lớn nhất ~ {max_size} bytes")
        if max_size <= max_bytes:
            return k, clusters, titles, sizes, contents

    print("CẢNH BÁO: K=n vẫn vượt giới hạn. Xuất theo K=n và cảnh báo.")
    k = n
    clusters = {i: [corpus[i]] for i in range(n)}
    titles = get_cluster_labels(clusters)
    max_size, sizes, contents = compute_cluster_sizes_bytes(clusters, titles)
    return k, clusters, titles, sizes, contents


def normalize_corpus_to_size(corpus, max_bytes):
    normalized = []
    for c in corpus:
        parts = split_large_chunk(c, max_bytes)
        normalized.extend(parts)
    return normalized


def cluster_and_save_file_size_constrained(input_file, output_folder, max_file_size_bytes, model=None):
    """
    Process a single file: chunk → normalize → embed → search K → save.
    """
    print(f"--- XỬ LÝ: {input_file} (giới hạn {max_file_size_bytes} bytes) ---")
    try:
        content = Path(input_file).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file '{input_file}'")
        return False

    corpus = chunk_markdown_by_headings(content)
    if not corpus:
        print("LỖI: Không trích được phần nào (thiếu '## ' ?). Bỏ qua.")
        return False

    corpus = normalize_corpus_to_size(corpus, max_file_size_bytes)

    if model is None:
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("    - Đang tạo embeddings...")
    embeddings = model.encode(corpus, show_progress_bar=False)

    print("    - Đang tìm K tối thiểu để mọi file <= giới hạn...")
    k, clusters, titles, sizes, _ = choose_k_by_max_file_size(
        corpus, embeddings, max_file_size_bytes
    )

    save_clusters_to_files(clusters, titles, output_folder)

    offenders = {cid: sz for cid, sz in sizes.items() if sz > max_file_size_bytes}
    if offenders:
        print("\n[CẢNH BÁO] Một số file vẫn vượt giới hạn:")
        for cid, sz in offenders.items():
            print(f"  - Cluster {cid+1}: {sz} bytes (> {max_file_size_bytes})")
    else:
        print("[OK] Tất cả file trong cụm đều ≤ giới hạn.")
    return True


# ------------------------------
# NEW: Process a folder
# ------------------------------

def process_folder(input_folder, output_root, max_file_size_bytes, recursive=False, pattern="*.md"):
    """
    Process all Markdown files in a folder.
      - Creates one subfolder per file inside output_root: <stem>-Output
      - Set recursive=True to scan subfolders via rglob
    """
    input_folder = Path(input_folder)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    files = list(input_folder.rglob(pattern) if recursive else input_folder.glob(pattern))
    if not files:
        print(f"Không tìm thấy file phù hợp ({pattern}) trong: {input_folder}")
        return

    print(f"Đã tìm thấy {len(files)} file. Bắt đầu xử lý...\n")
    # Load the model once for all files
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    processed, failed = 0, 0
    for f in files:
        # Output subfolder per input file
        out_dir = output_root / (f.stem + "-Output")
        ok = cluster_and_save_file_size_constrained(
            input_file=f,
            output_folder=out_dir,
            max_file_size_bytes=max_file_size_bytes,
            model=model
        )
        if ok:
            processed += 1
        else:
            failed += 1
        print("-" * 60)

    print(f"\nHoàn tất. Thành công: {processed}, Lỗi: {failed} (Tổng: {len(files)}).")


# ------------------------------
# Script entry
# ------------------------------
if __name__ == "__main__":
    # Ví dụ cấu hình:
    INPUT_FOLDER = "input"              
    OUTPUT_ROOT = "clustered-output"     
    MAX_FILE_SIZE_BYTES = 1 * 1024 
    RECURSIVE = True                      

    process_folder(
        input_folder=INPUT_FOLDER,
        output_root=OUTPUT_ROOT,
        max_file_size_bytes=MAX_FILE_SIZE_BYTES,
        recursive=RECURSIVE,
        pattern="*.md"
    )
