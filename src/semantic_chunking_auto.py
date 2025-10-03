import re
import os
from pathlib import Path
from unidecode import unidecode
import numpy as np
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer

# --- PHẦN 1: CÁC HÀM TIỆN ÍCH CƠ BẢN ---

def slugify(text):
    text_ascii = unidecode(text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text_ascii).strip("-").lower()
    # Giới hạn độ dài slug để tránh lỗi tên file quá dài
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
    print(f"    - Đã chia văn bản thành {len(chunks)} chunk.")
    return chunks


def find_optimal_k(embeddings, max_k):
    k_range = range(2, min(max_k + 1, len(embeddings)))
    silhouette_scores = []
    
    print(f"    - Đang thử nghiệm K từ 2 đến {k_range.stop - 1}...")
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
        kmeans.fit(embeddings)
        score = silhouette_score(embeddings, kmeans.labels_)
        silhouette_scores.append(score)
        print(f"      K={k} -> Silhouette={score:.3f}")

    if not silhouette_scores:
        print("    - Không đủ dữ liệu để tìm K tối ưu. Mặc định K=1.")
        return 1, [], []
        
    optimal_k = k_range[np.argmax(silhouette_scores)]
    print(f"    => ĐIỂM CAO NHẤT: K={optimal_k} (Silhouette={max(silhouette_scores):.3f})")
    return optimal_k, k_range, silhouette_scores

def get_cluster_labels(clusters, n_terms=3):
    cluster_texts = [" ".join(chunks) for chunks in clusters.values()]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=None, max_df=0.8)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(cluster_texts)
        feature_names = np.array(vectorizer.get_feature_names_out())
    except ValueError:
        return {cid: f"chủ đề {cid+1}" for cid in clusters.keys()}

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
            print(f"    [OK] Đã tạo file: {filename} (chứa {len(chunks)} đoạn)")
        except Exception as e:
            print(f"    [LỖI] Không thể ghi file {filename}: {e}")

def process_document_auto_cluster(input_file, output_folder, max_clusters_to_test=10):
    print(f"--- BẮT ĐẦU XỬ LÝ FILE: {input_file} ---")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file tại '{input_file}'")
        return
    corpus = chunk_markdown_by_headings(content)
    if len(corpus) <= 1:
        print("LỖI: Văn bản không đủ chunk để phân cụm.")
        return

    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(corpus, show_progress_bar=True)

    optimal_k, k_range, scores = find_optimal_k(embeddings, max_clusters_to_test)

    final_kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
    final_kmeans.fit(embeddings)
    clusters = {i: [] for i in range(optimal_k)}
    for i, label in enumerate(final_kmeans.labels_):
        clusters[label].append(corpus[i])

    cluster_titles = get_cluster_labels(clusters)

    save_clusters_to_files(clusters, cluster_titles, output_folder)
    

if __name__ == "__main__":
    INPUT_FILE = "benh-truyen-nhiem.md" 
    OUTPUT_FOLDER = "benh-truyen-nhiem_Output"
    MAX_CLUSTERS_TO_TEST = 10
    process_document_auto_cluster(INPUT_FILE, OUTPUT_FOLDER, MAX_CLUSTERS_TO_TEST)