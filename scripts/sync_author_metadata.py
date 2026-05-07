import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / f"author_consistency_audit_{dt.date.today().isoformat()}.json"
REPORT = ROOT / f"author_metadata_sync_report_{dt.date.today().isoformat()}.md"


def read_text(path):
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="ignore")
        except Exception:
            pass
    return ""


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def latex_escape(value):
    return (
        value.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )


def braced_value(command, text):
    match = re.search(r"\\" + command + r"\s*(?:\[[^\]]*\])?\s*\{", text)
    if not match:
        return ""
    start = match.end()
    depth = 1
    pos = start
    while pos < len(text) and depth:
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
        pos += 1
    return text[start : pos - 1].strip() if depth == 0 else ""


def clean_latex(value):
    value = re.sub(r"\\(?:textbf|textit|emph|uppercase)\s*\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\[A-Za-z]+(?:\[[^\]]*\])?", " ", value)
    value = re.sub(r"[{}$^_\\]", " ", value)
    return re.sub(r"\s+", " ", value).strip(" ,;:.")


def main_title_and_journal(path):
    text = read_text(path)
    title = clean_latex(braced_value("title", text))
    journal = clean_latex(braced_value("journal", text))
    if not journal:
        match = re.search(r"\\begin\{letter\}\{[^{}]*?\\\\\s*([^{}\\\\]+)\\\\", text, flags=re.S)
        if match:
            journal = clean_latex(match.group(1))
    return title, journal


def author_lines_authblk(authors):
    lines = []
    for idx, author in enumerate(authors, start=1):
        suffix = ""
        if idx == 1:
            suffix = r"\thanks{Corresponding author.}"
        lines.append(rf"\author[1]{{{latex_escape(author)}{suffix}}}")
    return "\n".join(lines)


def author_lines_plain(authors):
    return r"{\large " + r"\\[4pt] ".join(latex_escape(author) for author in authors) + "}"


def sync_title_page(path, authors, journal):
    text = read_text(path)
    original = text
    changed = []

    # Replace normal LaTeX author command blocks.
    author_line_pattern = re.compile(
        r"(?ms)^(?:\\author(?:\[[^\]]*\])?\{.*?\}\s*)+"
    )
    match = author_line_pattern.search(text)
    if match:
        text = text[: match.start()] + author_lines_authblk(authors) + "\n" + text[match.end() :]
        changed.append("authors")
    else:
        # Replace a simple centered author line such as {\large Quan Wen}.
        plain_match = re.search(r"\{\\large\s+([^{}]+?)\}", text)
        if plain_match:
            text = text[: plain_match.start()] + author_lines_plain(authors) + text[plain_match.end() :]
            changed.append("authors")
        else:
            center_match = re.search(r"(?m)^\s*\{\\large\s+[^\n]*\}\s*(?:\\\\\[[0-9.]+em\])?\s*$", text)
            if center_match:
                replacement = author_lines_plain(authors) + r"\\[1em]"
                text = text[: center_match.start()] + replacement + text[center_match.end() :]
                changed.append("authors")
            else:
                author_section = re.search(
                    r"(\\noindent\\textbf\{Authors?:\}\s*(?:\\vspace\{[^{}]+\}\s*)?)(.*?)(?=\\vspace\{1\.5em\}|\\noindent\\textbf\{Affiliations?:\})",
                    text,
                    flags=re.S,
                )
                if author_section:
                    body = "\n\n".join(rf"\noindent {latex_escape(author)}" for author in authors) + "\n\n"
                    text = text[: author_section.start(2)] + body + text[author_section.end(2) :]
                    changed.append("authors")
                else:
                    section_author = re.search(
                        r"(\\section\*\{Authors?\}\s*)(.*?)(?=\\section\*\{Affiliations?\}|\\section\*\{Corresponding Author\})",
                        text,
                        flags=re.S,
                    )
                    if section_author:
                        body = "\\\\\n".join(latex_escape(author) for author in authors) + "\n\n"
                        text = text[: section_author.start(2)] + body + text[section_author.end(2) :]
                        changed.append("authors")
                    else:
                        insert = "\n\\section*{Authors}\n" + "；".join(latex_escape(a) for a in authors) + "\n"
                        text = text.replace(r"\maketitle", r"\maketitle" + insert, 1)
                        if text != original:
                            changed.append("authors")

    if journal:
        escaped_journal = latex_escape(journal)
        text, count = re.subn(
            r"(\\textbf\{(?:Submitted to|Journal):\}\s*)(?:\\textit\{)?[^\\\n]+(?:\})?",
            rf"\1{escaped_journal}",
            text,
            count=1,
        )
        if count:
            changed.append("journal")

    if text != original:
        write_text(path, text)
    return changed


def cover_author_block(authors):
    author_text = "; ".join(latex_escape(a) for a in authors)
    return (
        "% AUTHOR_SYNC_START\n"
        "\\vspace{0.8em}\n\n"
        "\\noindent\\textbf{Author information:} "
        + author_text
        + ". All listed authors have approved the manuscript and agree with its submission.\n\n"
        "% AUTHOR_SYNC_END"
    )


def sync_cover_letter(path, authors):
    text = read_text(path)
    original = text
    block = cover_author_block(authors)
    pattern = re.compile(r"% AUTHOR_SYNC_START.*?% AUTHOR_SYNC_END", flags=re.S)
    if pattern.search(text):
        text = pattern.sub(block, text)
    else:
        inserted = False
        for marker in (r"\closing{", "We look forward", "Sincerely,"):
            index = text.find(marker)
            if index != -1:
                text = text[:index].rstrip() + "\n\n" + block + "\n\n" + text[index:].lstrip()
                inserted = True
                break
        if not inserted:
            text = text.replace(r"\end{document}", block + "\n\n" + r"\end{document}", 1)
    if text != original:
        write_text(path, text)
        return ["authors"]
    return []


def mentioned_journals(path):
    text = read_text(path)
    found = []
    for pattern in (
        r"\\textbf\{Submitted to:\}\s*(?:\\textit\{)?([^\\\n{}]+)",
        r"\\textbf\{Journal:\}\s*(?:\\textit\{)?([^\\\n{}]+)",
        r"\\begin\{letter\}\{[^{}]*?\\\\\s*([^{}\\\\]+)\\\\",
        r"\\textit\{([^{}]{4,80})\}",
    ):
        for match in re.finditer(pattern, text, flags=re.S):
            value = clean_latex(match.group(1))
            if value and value not in found:
                found.append(value)
    return found


def norm(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def journal_status(current, files):
    if not current:
        return "主稿未提取当前期刊"
    mismatches = []
    for path in files:
        journals = mentioned_journals(path)
        if journals and not any(norm(current) == norm(item) for item in journals):
            mismatches.append(f"{path.name}: {'; '.join(journals)}")
    return "一致" if not mismatches else "；".join(mismatches)


def main():
    records = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = [
        "# 作者与期刊元数据同步报告",
        "",
        f"生成日期：{dt.date.today().isoformat()}",
        "",
        "| 论文 | 修改 title page | 修改 cover letter | 主稿当前期刊 | title/cover 期刊核对 |",
        "|---|---|---|---|---|",
    ]
    changed_files = []
    for record in records:
        authors = record.get("main_authors") or []
        if not authors:
            continue
        main_path = Path(record["main"])
        _, current_journal = main_title_and_journal(main_path)
        title_changes = []
        cover_changes = []
        title_paths = [Path(p) for p in record.get("title_files", [])]
        cover_paths = [Path(p) for p in record.get("cover_files", [])]

        if "title page 与主稿不一致" in record.get("result", ""):
            for path in title_paths:
                changes = sync_title_page(path, authors, current_journal)
                if changes:
                    title_changes.append(f"{path.name}({','.join(changes)})")
                    changed_files.append(str(path))

        if "cover letter 与主稿不一致" in record.get("result", ""):
            for path in cover_paths:
                changes = sync_cover_letter(path, authors)
                if changes:
                    cover_changes.append(f"{path.name}({','.join(changes)})")
                    changed_files.append(str(path))

        journal_check = journal_status(current_journal, title_paths + cover_paths)
        rows.append(
            "| "
            + record.get("title", "").replace("|", "\\|")
            + " | "
            + ("；".join(title_changes) if title_changes else "未改")
            + " | "
            + ("；".join(cover_changes) if cover_changes else "未改")
            + " | "
            + (current_journal or "未提取")
            + " | "
            + journal_check.replace("|", "\\|")
            + " |"
        )

    rows += ["", "## 修改文件", ""]
    rows += [f"- `{path}`" for path in sorted(set(changed_files))] or ["- 无"]
    REPORT.write_text("\n".join(rows), encoding="utf-8")
    print(REPORT)
    print(f"changed_files={len(set(changed_files))}")


if __name__ == "__main__":
    main()
