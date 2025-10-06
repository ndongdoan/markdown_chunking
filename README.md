# Markdown Chunking

## Cấu Trúc Repo

Thư mục src chứa script, được chia thành 2 folder nhỏ:

- dong: Phương án của Đông
- hoang: Phương án của Hoàng

## Thuật Toán

### Phương án 1: Traditional Chunking

Phương án này có mỗi file chứa 4 bài viết (có thể tùy ý điều chỉnh lại). Các file được tách dựa trên heading và credit cuối bài.

#### Mô tả các hàm, biến
- `slugify` : Tạo title cho các file nhỏ được tách ra
- `chunk_markdown_by_headings` : Logic chính để tách file theo `## ` (H2)
- `split_large_chunk` : Tự động chia nhỏ phần vượt quá giới hạn bytes (dùng `###`, đoạn, rồi tới hard-wrap)
- `normalize_corpus_to_size` : Đảm bảo không có chunk nào > giới hạn trước khi phân cụm
- `get_cluster_labels` : Đặt tiêu đề cụm dựa trên TF‑IDF (top 3 cụm từ)
- `cluster_with_k` : Phân cụm K‑Means theo embedding
- `choose_k_by_max_file_size` : Tăng K cho đến khi tất cả file ≤ giới hạn
- `save_clusters_to_files` : Ghi các cụm ra thư mục
- Biến chính: `articles` (ẩn trong pipeline), `inside_article`, `group_count` (ẩn), ... tương đương như sơ đồ
### Workflow (Mermaid)

```mermaid
flowchart TD
    A[Đọc file Markdown] --> B[Chia file thành danh sách dòng]
    B --> C{Dòng bắt đầu bằng '## '?}
    C -- Không --> D[Thêm dòng vào bài hiện tại]
    C -- Có --> E{Đang trong bài?}
    E -- Có --> F[Lưu bài trước nếu có, tạo bài mới]
    E -- Không --> G[Bắt đầu bài mới]
    D --> H{Dòng chứa credit?}
    H -- Có --> F
    H -- Không --> B
    F --> I[Lưu bài vào danh sách, reset biến]
    B --> J{Hết file?}
    J -- Có --> K[Thêm bài cuối vào danh sách]
    K --> L[Gom nhóm bài theo group_size (nếu dùng)]
    L --> M[Giải thuật phân cụm KMeans với embeddings]
    M --> N[Tạo tiêu đề bằng TF-IDF]
    N --> O[Kiểm tra kích thước từng file]
    O -- >|> max| P[Tăng K và phân cụm lại]
    O -- ≤ max --> Q[In thông báo hoàn tất & ghi ra file]
```
## Tính năng chính
- Xử lý **toàn bộ thư mục** `.md` (có thể đệ quy).
- **Giới hạn kích thước** mỗi file theo bytes: `--max-size` (mặc định **1 KB** để test nhanh).
- **Embedding đa ngôn ngữ**: `paraphrase-multilingual-MiniLM-L12-v2`.
- **Tiêu đề chủ đề tự động** bằng TF‑IDF.
- Xuất Markdown **sạch, dễ đọc**.

---

## Cài đặt

```bash
pip install -U sentence-transformers scikit-learn unidecode numpy
```

---

## Cách dùng (CLI)

```bash
python -m cluster_markdown.main input/ clustered-output --max-size 1024 --recursive
# hoặc sau khi đóng gói:
# markdown-cluster input/ clustered-output --max-size 1024 --recursive
```

- `--max-size`: giới hạn bytes / file (ví dụ `1*1024*1024` = 1 MB)
- `--recursive`: quét đệ quy thư mục con
- `--pattern`: mẫu glob (mặc định `*.md`)

> **Lưu ý:** `1 * 1024` = **1 KB**. Để dùng 1 MB, đặt `--max-size 1048576` hoặc `1*1024*1024` trong code.

---

## Cấu trúc thư mục gợi ý

```
.
├── cluster_markdown/
│   ├── __init__.py
│   └── main.py
├── input/
│   ├── sample1.md
│   └── sample2.md
├── README.md
└── requirements.txt
```
---

#### Một số điểm cần cải thiện

- Một số file gốc không dùng heading dạng ```##``` mà dùng placeholder
- Có thể dùng CUDA hoặc CPU accelartion để tăng tốc độ xử lí
