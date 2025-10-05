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
A[Đọc file Markdown] --> B[Chia file thành danh sách dòng]
B --> C{Dòng bắt đầu bằng '## '?}
C -- Không --> D[Thêm dòng vào bài hiện tại (nếu đang trong bài)]
D --> E{Dòng chứa credit?}
E -- Có --> F[Lưu bài vào danh sách, reset biến]
E -- Không --> B
C -- Có --> G{is_new_article?}
G -- Có --> H[Lưu bài trước (nếu có), tạo bài mới]
G -- Không --> I[Thêm dòng vào bài hiện tại]
H --> B
I --> B
F --> B
B -->|Hết file| J{Còn bài đang viết dở?}
J -- Có --> K[Thêm bài cuối vào danh sách]
J -- Không --> L[Gom nhóm các bài theo group_size]
K --> L
L --> M[Ghi nhóm bài ra file .md]
M --> N[In thông báo hoàn tất]
```

#### Một số điểm cần cải thiện

- Có phương án ngắt bài/file tổng quát để áp dụng cho dataset lớn hơn
- Gom 3-5 bài vào cùng 1 file để giảm số lượng file nhỏ