#!/usr/bin/env python3
"""Coverage validator for generated documentation skills.

Runs a suite of checks to verify that the generated skill is complete
and structurally sound.

Checks performed:
  1. SKILL.md exists, has YAML frontmatter, and has substantial content
  2. Content files exist (at least one .md file besides SKILL.md)
  3. Link resolution: all file paths in SKILL.md resolve to existing files
  4. No empty files: every .md file has real content (not just a heading)

Exit codes:
  0 — all checks passed
  1 — one or more checks failed

Usage:
    python3 validate.py <skill-dir>
"""

import argparse
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("validate")


def parse_args():
    p = argparse.ArgumentParser(description="Validate generated documentation skill")
    p.add_argument("skill_dir", help="Path to the generated skill directory (contains SKILL.md + pages/)")
    return p.parse_args()


class ValidationResult:
    """Accumulates check results and generates a formatted report."""

    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []

    def add_check(self, name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        self.checks.append((name, status, detail))
        if not passed:
            self.errors.append(f"{name}: {detail}")

    def add_warning(self, message):
        self.warnings.append(message)

    @property
    def passed(self):
        return len(self.errors) == 0

    def report(self):
        lines = ["=" * 60, "VALIDATION REPORT", "=" * 60, ""]

        for name, status, detail in self.checks:
            icon = "+" if status == "PASS" else "-"
            line = f"  [{icon}] {name}"
            if detail:
                line += f" — {detail}"
            lines.append(line)

        if self.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  [!] {w}")

        lines.append("")
        lines.append("-" * 60)
        if self.passed:
            lines.append("RESULT: ALL CHECKS PASSED")
        else:
            lines.append(f"RESULT: {len(self.errors)} CHECK(S) FAILED")
            for err in self.errors:
                lines.append(f"  - {err}")

        lines.append("=" * 60)
        return "\n".join(lines)


def collect_md_files(skill_dir):
    """Recursively collect all .md files in the skill directory except SKILL.md."""
    files = {}
    for md_file in skill_dir.rglob("*.md"):
        rel = md_file.relative_to(skill_dir)
        if str(rel) == "SKILL.md":
            continue
        files[str(rel)] = md_file
    return files


def check_skill_md(skill_dir, result):
    """Verify that SKILL.md exists, has YAML frontmatter, and has enough content."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.add_check("SKILL.md exists", False)
        return None

    content = skill_md.read_text(encoding="utf-8")

    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            result.add_check("SKILL.md has frontmatter", True)
        else:
            result.add_check("SKILL.md has frontmatter", False, "Frontmatter not closed")
    else:
        result.add_check("SKILL.md has frontmatter", False, "No frontmatter found")

    if len(content) > 500:
        result.add_check("SKILL.md has substantial content", True, f"{len(content)} chars")
    else:
        result.add_check("SKILL.md has substantial content", False, f"Only {len(content)} chars")

    return content


def check_link_resolution(skill_md_content, skill_dir, result):
    """Verify that every file path referenced in SKILL.md resolves to an existing file."""
    if skill_md_content is None:
        return

    path_pattern = re.compile(r"`([a-zA-Z_][\w/-]*\.md)`")
    referenced = path_pattern.findall(skill_md_content)

    if not referenced:
        result.add_warning("No file paths found in SKILL.md to check")
        return

    broken = []
    for ref in referenced:
        full_path = skill_dir / ref
        if not full_path.exists():
            broken.append(ref)

    if broken:
        result.add_check(
            "Link resolution",
            False,
            f"{len(broken)} broken references: {broken[:5]}",
        )
    else:
        result.add_check(
            "Link resolution",
            True,
            f"All {len(referenced)} referenced paths resolve",
        )


def check_empty_files(md_files, result):
    """Verify that no content files are empty or suspiciously short."""
    empty = []
    placeholder = []
    for rel_path, filepath in md_files.items():
        content = filepath.read_text(encoding="utf-8").strip()
        if not content:
            empty.append(rel_path)
        elif len(content) < 200:
            placeholder.append(rel_path)

    if empty:
        result.add_check("No empty files", False, f"{len(empty)} empty files: {empty[:5]}")
    else:
        result.add_check("No empty files", True, f"All {len(md_files)} files have content")

    if placeholder:
        result.add_warning(f"{len(placeholder)} files with very short content (<200 chars): {placeholder[:5]}")


def main():
    args = parse_args()
    skill_dir = Path(args.skill_dir).resolve()

    if not skill_dir.exists():
        log.error(f"Skill directory does not exist: {skill_dir}")
        sys.exit(1)

    result = ValidationResult()

    if not (skill_dir / "SKILL.md").exists():
        log.error(f"No SKILL.md found in {skill_dir}")
        result.add_check("Skill directory exists", False)
        print(result.report())
        sys.exit(1)
    result.add_check("Skill directory exists", True, str(skill_dir.name))

    md_files = collect_md_files(skill_dir)
    result.add_check("Content files found", len(md_files) > 0, f"{len(md_files)} markdown files")

    skill_md_content = check_skill_md(skill_dir, result)
    check_link_resolution(skill_md_content, skill_dir, result)
    check_empty_files(md_files, result)

    print(result.report())
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
