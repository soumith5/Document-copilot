from pathlib import Path

import sec2md

path = Path("../data/downloads/2025/aapl_10-k_2025-10-31_0000320193-25-000079.htm")
html = path.read_text(encoding="utf-8")

parser = sec2md.Parser(html)
pages = parser.get_pages()

print(f"Pages: {len(pages)}")

sections = sec2md.extract_sections(pages, filing_type="10-K")
print(f"\nSections found: {len(sections)}")
for section in sections:
    print(
        f"  {section.part} {section.item}: {section.item_title} "
        f"(pages {section.page_range}, {section.tokens} tokens)"
    )