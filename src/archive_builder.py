from pathlib import Path

OUTPUT_DIR = Path("../archives")


def build_archive():
    OUTPUT_DIR.mkdir(exist_ok=True)

    html = """
<!DOCTYPE html>
<html>
<head>
    <title>ChatGPT Archive Builder</title>
</head>
<body>
    <h1>ChatGPT Archive Builder</h1>
    <p>If you're reading this, the project is alive.</p>
</body>
</html>
"""

    output_file = OUTPUT_DIR / "index.html"
    output_file.write_text(html, encoding="utf-8")

    print(f"Archive generated: {output_file}")


if __name__ == "__main__":
    build_archive()