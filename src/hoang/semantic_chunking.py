import re
import os
from pathlib import Path
from unidecode import unidecode
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer


def slugify(text):
    text_ascii = unidecode(text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text_ascii).strip("-").lower()
    return slug[:80] if slug else "untitled"

def chunk_markdown_by_headings(file_content):
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
    return chunks

def get_cluster_labels(clusters, n_terms=3):
    cluster_texts = [" ".join(chunks) for chunks in clusters.values()]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=None, max_df=0.7)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(cluster_texts)
        feature_names = np.array(vectorizer.get_feature_names_out())
    except ValueError:
        return {cid: f"Chủ đề #{cid+1}" for cid in clusters.keys()}

    labels = {}
    for i, _ in enumerate(clusters):
        row = tfidf_matrix.toarray()[i]
        top_term_indices = row.argsort()[-n_terms:][::-1]
        top_terms = feature_names[top_term_indices]
        labels[i] = " ".join(top_terms)
        
    return labels

def save_clusters_to_files(clusters, cluster_titles, output_folder):
    """Lưu nội dung của từng cụm vào các file markdown riêng biệt."""
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    print(f"\n--- ĐANG XUẤT FILE RA THƯ MỤC: {output_folder} ---")

    for cluster_id, chunks in clusters.items():
        title_raw = cluster_titles.get(cluster_id, f"chủ đề {cluster_id+1}")
        filename_slug = slugify(title_raw)
        filename = f"{cluster_id+1:02d}-{filename_slug}.md"
        filepath = Path(output_folder) / filename

        file_content = f"# CHỦ ĐỀ: {title_raw.upper()}\n\n"
        file_content += "\n\n---\n\n".join(chunks)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)
            print(f"    [OK] Đã tạo file: {filename}")
        except Exception as e:
            print(f"    [LỖI] Không thể ghi file {filename}: {e}")

def cluster_and_save_file(input_file, optimal_k, output_folder):
    """Hàm chính thực hiện tất cả các bước: phân cụm, đặt tên, và lưu file."""
    print(f"--- BẮT ĐẦU XỬ LÝ VỚI SỐ CỤM CỐ ĐỊNH K={optimal_k} ---")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file '{input_file}'")
        return
        
    corpus = chunk_markdown_by_headings(content)
    if len(corpus) < optimal_k:
        print(f"LỖI: Số chunk ({len(corpus)}) ít hơn số cụm yêu cầu ({optimal_k}).")
        return

    print("    - Đang tạo embeddings...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(corpus, show_progress_bar=True)
    print(f"    - Đang phân cụm với K = {optimal_k}...")
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
    kmeans.fit(embeddings)

    clusters = {i: [] for i in range(optimal_k)}
    for i, label in enumerate(kmeans.labels_):
        clusters[label].append(corpus[i])
    cluster_titles = get_cluster_labels(clusters)
    save_clusters_to_files(clusters, cluster_titles, output_folder)


if __name__ == "__main__":
    INPUT_FILE = "benh-truyen-nhiem.md"
    OUTPUT_FOLDER = "benh-truyen-nhiem-10-Output"
    OPTIMAL_NUMBER_OF_TOPICS = 10
    cluster_and_save_file(INPUT_FILE, OPTIMAL_NUMBER_OF_TOPICS, OUTPUT_FOLDER)