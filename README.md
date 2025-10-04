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

A([Bắt đầu chương trình]) --> B[Đọc file thành list dòng]
B --> C[Khởi tạo biến: articles, current_article, article_title=None, inside_article=False]

C --> D{Duyệt từng dòng}

D -->|Dòng bắt đầu bằng "## "| E{inside_article == False?}
E -->|Yes| F[Bắt đầu bài mới<br/>- Nếu có bài cũ thì lưu<br/>- Reset biến<br/>- Lấy title mới<br/>- inside_article=True]
E -->|No| G[Heading con trong bài hiện tại<br/>→ Append vào current_article]

D -->|Dòng thường| H{inside_article == True?}
H -->|No| D
H -->|Yes| I[Append vào current_article]

I --> J{Dòng có chứa 'Bệnh viện NTP'?}
J -->|Yes| K[Kết thúc bài<br/>- Append vào articles<br/>- Reset biến<br/>- inside_article=False]
J -->|No| D

K --> D

D --> L[Hết vòng lặp]
L --> M{Còn current_article?}
M -->|Yes| N[Append vào articles]
M -->|No| O[Tiếp tục]

N --> O

O --> P[Loop qua articles<br/>- Slugify title<br/>- Xuất mỗi bài = 1 file]
P --> Q([Kết thúc])
```

#### Một số điểm cần cải thiện

- Có phương án ngắt bài/file tổng quát để áp dụng cho dataset lớn hơn
- Gom 3-5 bài vào cùng 1 file để giảm số lượng file nhỏ