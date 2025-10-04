# Markdown Chunking

## Cấu Trúc Repo

Thư mục src chứa script, được chia thành 2 folder nhỏ:

- dong: Phương án của Đông
- hoang: Phương án của Hoàng

## Thuật Toán

### Phương án 1: Traditional Chunking

Phương án này chia mỗi file tương ứng với 1 bài viết. Mốc bắt đầu bài viết là các heading và để tách file hiện tại là credit "Bệnh viện NTP" hoặc mục lục ở cuối mỗi bài.

#### Mô tả các function

```slugify(text)```: Tạo title cho các file nhỏ được tách ra

```split_markdown(input_file, output_folder)```: Logic chính để chia file

- Đọc file md
- ```end_pattern```: Pattern để xác định cuối bài
- ```articles```: Lưu trữ tất cả bài viết đã được tách ra
- ```current_article```: Lưu trữ bài viết hiện tại
- ```article_title```: Title cho bài viết hiện tại
- ```inside_article```: Bool để xác định có đang ở trong bài viết hay không

#### Workflow

```mermaid
flowchart TD
A[Đọc toàn bộ nội dung file Markdown] --> B[Chia nội dung thành danh sách dòng]
B --> C{Dòng bắt đầu bằng '## ' ?}
C -- Có --> D{Đang ở trong bài khác?}
D -- Có --> E[Lưu bài hiện tại vào danh sách articles]
D -- Không --> F[Tạo bài mới và gán article_title]
E --> F
F --> G[Thêm dòng hiện tại vào current_article]
C -- Không --> H{inside_article == True ?}
H -- Có --> I[Thêm dòng vào current_article]
I --> J{Dòng chứa credit (end_pattern) ?}
J -- Có --> K[Lưu bài vào danh sách articles, reset biến]
J -- Không --> L[Tiếp tục đọc dòng kế tiếp]
H -- Không --> L
K --> L
L --> M{Hết file ?}
M -- Có --> N[Thêm bài cuối cùng nếu còn sót]
M -- Không --> C
N --> O[Ghi từng bài ra file Markdown riêng]
O --> P[Hoàn tất quá trình chunking]
```

#### Một số điểm cần cải thiện

- Có phương án ngắt bài/file tổng quát để áp dụng cho dataset lớn hơn
- Gom 3-5 bài vào cùng 1 file để giảm số lượng file nhỏ