import re
from pathlib import Path
from unidecode import unidecode 

# Lowercase, bỏ dấu, thay space/ký tự lạ bằng "-"
# Tạo title cho file output
def slugify(text):
    text_ascii = unidecode(text)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text_ascii).strip("-").lower()
    return slug

def split_markdown(input_file, output_folder):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    end_pattern = re.compile(r"Bệnh viện Nguyễn Tri Phương", re.IGNORECASE)

    articles = []
    current_article = []
    article_title = None
    inside_article = False

    for line in lines:
        # Tìm heading "##"
        if line.startswith("## "):
            if not inside_article or article_title is None:
                if current_article:
                    articles.append((article_title, current_article))
                    current_article = []

                # Lấy bài mới
                article_title = line.strip("# ").strip()
                inside_article = True
                current_article = [line]
            else:
                current_article.append(line)
        else:
            if inside_article:
                current_article.append(line)
                # Tìm credit cuối bài
                if end_pattern.search(line):
                    articles.append((article_title, current_article))
                    current_article = []
                    article_title = None
                    inside_article = False

    # Bài cuối không có credit?
    if current_article:
        articles.append((article_title, current_article))

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    for idx, (title, content) in enumerate(articles, start=1):
        if not title:
            title = f"untitled-{idx}"
        filename = f"{idx:02d}-{slugify(title)}.md"
        filepath = Path(output_folder) / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(content)
        print(f"Đã xuất: {filename}")

# --- chạy thử ---
if __name__ == "__main__":
    input_file = "benh-truyen-nhiem.md"
    output_folder = "chunks_output_benh_truyen_nhiem"
    split_markdown(input_file, output_folder)
