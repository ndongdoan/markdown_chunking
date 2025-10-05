import re
from pathlib import Path
from unidecode import unidecode 

"""
end_pattern: pattern kết thúc bài (nếu có)
group_size: số bài viết trong 1 file, có thể thay đổi
"""
END_PATTERN = re.compile(r"Bệnh viện Nguyễn Tri Phương", re.IGNORECASE)
GROUP_SIZE = 4


def is_new_article(line: str) -> bool:
    """Xác định heading là bài mới hay mục con"""
    if not line.startswith("## "):
        return False
    
    clean = line.strip().lower()

    """ Các dòng dùng '##' mà là mục con luôn in đậm hoặc có đánh số thứ tự """
    if re.match(r"^##\s*\*\*\s*(?:\d+\.)?", clean):
        return False
    
    return True

# Lowercase, bỏ dấu, thay space/ký tự lạ bằng "-"
# Tạo title cho file output
def slugify(text: str) -> str:
    text_ascii = unidecode(text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text_ascii).strip("-").lower()
    return slug

def split_markdown(input_path: str, output_folder: str, group_size = GROUP_SIZE):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    articles = []
    current_article = []
    article_title = None
    inside_article = False

    for line in lines:
        """ Tìm heading ## """
        if line.startswith("## "):
            """ Là mục con hay tiêu đề ? """
            if is_new_article(line):
                """ Nếu bài trước đó chưa được lưu -> Lưu lại và reset current_article"""
                if inside_article and current_article:
                    articles.append((article_title, current_article))
                    current_article = []

                """ Lấy bài mới """
                article_title = line.strip("# ").strip()
                inside_article = True
                current_article = [line]
            else:
                current_article.append(line)
        else:
            if inside_article:
                current_article.append(line)
                # Tìm credit cuối bài
                if END_PATTERN.search(line):
                    articles.append((article_title, current_article))
                    current_article = []
                    article_title = None
                    inside_article = False

    """ Thêm bài cuối vào list articles """
    if current_article:
        articles.append((article_title, current_article))

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    group_count = 0
    for i in range(0, len(articles), group_size):
        group = articles[i : i + group_size]
        group_count += 1

        first_title = group[0][0] or f"group-{group_count}"
        cleaned_title = slugify(first_title)
        filename = f"{group_count:03d}-{cleaned_title}.md"
        output_path = Path(output_folder) / filename

        joined_article = "".join("".join(content) for _, content in group)
        output_path.write_text(joined_article, encoding="utf-8")

    print(f"✅ Tách hoàn tất: {len(articles)} bài → {group_count} file trong {output_folder}")

if __name__ == "__main__":
    #thay bằng tên file md gốc
    input_path = "original-markdown-file-path"

     #thay bằng tên output folder
    output_folder = "output-folder-path"
    split_markdown(input_path, output_folder)
