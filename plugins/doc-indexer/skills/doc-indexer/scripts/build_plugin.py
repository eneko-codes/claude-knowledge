#!/usr/bin/env python3
"""Plugin generator — assembles extracted content into a complete documentation plugin.

Takes the per-page JSON files from extract.py and assembles them into a complete
Claude Code documentation plugin with the standard directory structure:

    plugins/docs-<library>/
    ├── .claude-plugin/plugin.json        # Plugin metadata
    └── skills/<library>-docs/
        ├── SKILL.md                      # Index file Claude reads first
        └── pages/                        # All documentation pages (flat)

The generated SKILL.md is the entry point for Claude — it lists every sub-file
so Claude can navigate to the relevant section based on the user's question.

Usage:
    python3 build_plugin.py <library-name> <extracted-dir> [--version latest] [--source-url URL] [--output-dir DIR]
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_plugin")

# Resolve paths relative to this script's location so the script works
# regardless of the current working directory when invoked.
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"

# All content files go into a single "pages/" directory.
# Category classification from extract.py is kept as metadata for the SKILL.md
# descriptions, but no longer drives directory structure. This avoids the 50%+
# misclassification rate from heuristic-based categorization.
PAGES_DIR = "pages"


def parse_args():
    p = argparse.ArgumentParser(description="Build documentation plugin from extracted content")
    p.add_argument("library_name", help="Library identifier (e.g., react, laravel, htmx)")
    p.add_argument("extracted_dir", help="Directory containing extracted JSON files")
    p.add_argument("--version", default="latest", help="Documentation version label (default: latest)")
    p.add_argument("--source-url", default="", help="Original documentation URL")
    p.add_argument(
        "--output-dir",
        default="",
        help="Output directory (default: ../../plugins/docs-<library> relative to scripts/)",
    )
    p.add_argument(
        "--skill-only",
        action="store_true",
        help="Output just the skill directory (SKILL.md + pages/) without plugin wrapper",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_extracted(extracted_dir):
    """Load all extracted JSON files from the directory.

    Files are sorted alphabetically for deterministic output — the same input
    always produces the same plugin structure, making diffs meaningful.
    """
    pages = []
    for filename in sorted(os.listdir(extracted_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(extracted_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        pages.append(data)
    return pages


# ---------------------------------------------------------------------------
# Filename and grouping utilities
# ---------------------------------------------------------------------------

def sanitize_filename(text):
    """Convert a page title to a safe, readable filename.

    Transforms "Installing sqlc on macOS" → "installing-sqlc-on-macos".
    Truncates at 80 characters to avoid filesystem path length limits
    (especially relevant on Windows where MAX_PATH is 260 characters).
    """
    safe = re.sub(r"[^a-zA-Z0-9._-]", "-", text.lower())
    safe = re.sub(r"-+", "-", safe).strip("-")
    if len(safe) > 80:
        safe = safe[:80].rstrip("-")
    return safe or "untitled"



# ---------------------------------------------------------------------------
# Template handling
# ---------------------------------------------------------------------------

def load_template(name):
    """Load a template file from the templates/ directory.

    Templates use Python's str.format() syntax ({variable_name}) rather than
    Jinja2 to avoid adding an extra dependency. This is sufficient for our
    needs since we're doing simple variable substitution without loops or
    conditionals.
    """
    path = TEMPLATE_DIR / name
    if not path.exists():
        log.error(f"Template not found: {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def render_template(template, **kwargs):
    """Safely render a template string with variable substitution.

    Python's str.format() fails on strings containing literal braces (e.g.,
    Go code like `func main() {`). We use sequential str.replace() instead,
    which only substitutes known placeholders and ignores literal braces.
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def generate_section_file(page, library_name, template=None):
    """Generate a markdown sub-file for a single documentation page."""
    if template is None:
        template = load_template("section_template.md")
    title = page.get("title", "Untitled")
    url = page.get("url", "")
    markdown = page.get("markdown", "")
    warnings = page.get("warnings", [])

    # Format warnings as a blockquote section if any exist
    warnings_block = ""
    if warnings:
        warnings_block = "\n\n> **Warnings:**\n" + "\n".join(f"> - {w}" for w in warnings)

    return render_template(
        template,
        title=title,
        source_url=url,
        content=markdown,
        warnings=warnings_block,
    )




def generate_skill_md(library_name, versioned_library, plugin_name, pages, source_url, version, file_listing):
    """Generate the SKILL.md index file for the documentation plugin.

    SKILL.md is the most important file in the plugin — it's what Claude reads
    first when the skill is activated. It contains:
    - Frontmatter with trigger phrases for skill activation (version-aware)
    - Source URL and version metadata
    - Directory structure overview
    - Quick reference for the most common API functions
    - Complete file listing so Claude knows where to find every piece of content
    """
    template = load_template("SKILL_template.md")

    # No quick reference section — it was noise with out-of-context signatures
    quick_ref = ""

    # Simple page count summary
    category_summary = f"- **{PAGES_DIR}/**: {len(pages)} documentation pages\n"

    # Build version-specific trigger phrases for the SKILL.md description.
    # When versioned, include phrases like "laravel 11 docs" so Claude picks
    # the right version. When "latest", omit version from triggers.
    if version and version != "latest":
        version_triggers = (
            f'"{library_name} {version}", "{library_name} {version} docs", '
            f'"{library_name} version {version}"'
        )
    else:
        version_triggers = ""

    return render_template(
        template,
        library_name=library_name,
        versioned_library=versioned_library,
        plugin_name=plugin_name,
        library_name_title=library_name.replace("-", " ").title(),
        version=version,
        version_triggers=version_triggers,
        source_url=source_url,
        total_pages=len(pages),
        category_summary=category_summary,
        quick_reference=quick_ref,
        file_listing=file_listing,
    )


def generate_plugin_json(plugin_name, library_name, version, source_url):
    """Generate .claude-plugin/plugin.json for the documentation plugin.

    This is the plugin metadata file that Claude Code reads to identify and
    load the plugin. It must contain name, description, version, and author.
    Uses plugin_name (version-aware) for the "name" field so versioned plugins
    have distinct identities (e.g., "laravel-11-docs" vs "laravel-12-docs").
    """
    template = load_template("plugin_json_template.json")
    return render_template(
        template,
        plugin_name=plugin_name,
        library_name=library_name,
        library_name_title=library_name.replace("-", " ").title(),
        version=version,
        source_url=source_url,
    )


# ---------------------------------------------------------------------------
# Main build pipeline
# ---------------------------------------------------------------------------

def build_plugin(args):
    """Orchestrate the full plugin build from extracted content.

    Pipeline:
    1. Load all extracted JSON files
    2. Create plugin directory structure
    3. Generate content sub-files (one .md per page in pages/)
    4. Generate SKILL.md (entry point with file index and sub-topic descriptions)
    5. Generate plugin.json (metadata)
    """
    library = args.library_name
    extracted_dir = args.extracted_dir
    version = args.version
    source_url = args.source_url

    # Version-aware naming: when version is not "latest", insert it between
    # the library name and the "-docs" suffix so multiple versions can coexist.
    # e.g., "laravel" + "11" → plugin "laravel-11-docs", skill "laravel-11-docs"
    # e.g., "laravel" + "latest" → plugin "laravel-docs", skill "laravel-docs"
    # This groups versions alphabetically (laravel-11-docs, laravel-12-docs).
    if version and version != "latest":
        plugin_name = f"{library}-{version}-docs"
        versioned_library = f"{library}-{version}"
    else:
        plugin_name = f"{library}-docs"
        versioned_library = library

    # Default output location: alongside other plugins in the monorepo.
    # scripts/ → doc-indexer skill → doc-indexer plugin → plugins/ → docs-<lib>/
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = SCRIPT_DIR.parent.parent.parent.parent / plugin_name

    log.info(f"Building plugin '{plugin_name}' v{version}")
    log.info(f"Reading from: {extracted_dir}")
    log.info(f"Writing to: {output_dir}")

    # Load all extracted pages
    pages = load_extracted(extracted_dir)
    if not pages:
        log.error("No extracted pages found")
        sys.exit(1)

    log.info(f"Loaded {len(pages)} pages")

    log.info(f"  Total: {len(pages)} pages (flat structure)")

    # Set up the directory structure.
    # In skill-only mode, output_dir IS the skill directory (SKILL.md + pages/).
    # In plugin mode, output_dir contains the full plugin structure.
    skill_name = f"{versioned_library}-docs"

    if args.skill_only:
        skill_dir = output_dir
        plugin_meta_dir = None
    else:
        skill_dir = output_dir / "skills" / skill_name
        plugin_meta_dir = output_dir / ".claude-plugin"
        plugin_meta_dir.mkdir(parents=True, exist_ok=True)

    # Track all generated files for the SKILL.md file listing
    file_listing_lines = []
    written_files = []

    # Generate content sub-files — all files go into a single pages/ directory.
    # No category-based subdirectories; SKILL.md provides topic navigation.
    content_dir = skill_dir / PAGES_DIR
    content_dir.mkdir(parents=True, exist_ok=True)

    used_filenames = {}

    section_template = load_template("section_template.md")

    for page in pages:
        title = page.get("title", "Untitled")
        filename = sanitize_filename(title) + ".md"

        # Detect filename collisions
        if filename.lower() in used_filenames:
            base = sanitize_filename(title)
            counter = 2
            while f"{base}-{counter}.md".lower() in used_filenames:
                counter += 1
            filename = f"{base}-{counter}.md"
            log.warning(f"  Filename collision: '{title}' → {filename}")

        used_filenames[filename.lower()] = True

        filepath = content_dir / filename
        content = generate_section_file(page, library, section_template)
        filepath.write_text(content, encoding="utf-8")

        # Build rich file listing with H2 headings as sub-topics
        h2_headings = [h["text"] for h in page.get("headings", []) if h.get("level") == 2]
        if h2_headings:
            # Show up to 8 key sub-topics
            topics = ", ".join(h2_headings[:8])
            if len(h2_headings) > 8:
                topics += f", ... (+{len(h2_headings) - 8} more)"
            file_listing_lines.append(f"- `{PAGES_DIR}/{filename}` — {title}: {topics}")
        else:
            file_listing_lines.append(f"- `{PAGES_DIR}/{filename}` — {title}")

        written_files.append(f"{PAGES_DIR}/{filename}")

    log.info(f"Wrote {len(written_files)} content files")

    # Generate SKILL.md — the entry point Claude reads when the skill activates.
    # The file listing is sorted alphabetically for consistent, scannable output.
    file_listing = "\n".join(sorted(file_listing_lines))
    skill_content = generate_skill_md(library, versioned_library, plugin_name, pages, source_url, version, file_listing)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    log.info(f"Wrote {skill_path}")

    # Generate plugin.json metadata (skip in skill-only mode)
    if plugin_meta_dir is not None:
        plugin_json_content = generate_plugin_json(plugin_name, library, version, source_url)
        plugin_json_path = plugin_meta_dir / "plugin.json"
        plugin_json_path.write_text(plugin_json_content, encoding="utf-8")
        log.info(f"Wrote {plugin_json_path}")

    # Final summary
    log.info("=" * 60)
    if args.skill_only:
        log.info(f"Skill built successfully: {output_dir}")
        log.info(f"Total files: {len(written_files) + 1} (content + SKILL.md)")
    else:
        log.info(f"Plugin built successfully: {output_dir}")
        log.info(f"Total files: {len(written_files) + 2} (content + SKILL + plugin.json)")
    log.info(f"Skill name: {skill_name}")


def main():
    args = parse_args()
    build_plugin(args)


if __name__ == "__main__":
    main()
