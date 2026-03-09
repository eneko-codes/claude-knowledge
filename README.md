<div align="center">

# knowledge

**Index any documentation locally and use it as a Claude Code skill.**

Each plugin is a skill with an index — Claude sees every available page
and navigates directly to the right file. No searching, no guessing.

No extra API calls. No latency. Pre-built docs ready to install, or index your own in minutes.

[Available Docs](#available-documentation) ·
[Install](#installation) ·
[Request Docs](#request-a-library) ·
[Index Your Own](#index-your-own-docs) ·
[Why Skills?](#why-skills-instead-of-mcp)

</div>

---

## Available Documentation

| Plugin | Library | Pages |
|:-------|:--------|------:|
| *coming soon* | Laravel, React, Go | — |

> **Don't see your library?** [Request it](https://github.com/eneko-codes/knowledge/issues/new?template=doc-request.yml) — no setup needed, just fill out the form. Or [index your own](#index-your-own-docs) in minutes.

---

## Installation

**1. Add the marketplace** *(one-time)*

```bash
claude /plugin marketplace add https://github.com/eneko-codes/knowledge
```

**2. Install a docs plugin**

```bash
claude /plugin install react-docs@knowledge
```

**3. Ask Claude**

```
How do React Server Components work?
What hooks are available for managing state?
Show me how to use Suspense for data fetching
```

That's it. Claude reads the docs from local files — instant answers, no extra network calls.

> [!TIP]
> **Add a CLAUDE.md instruction so Claude always uses the docs skill.**
>
> Whether you installed a pre-built plugin or generated one with `doc-indexer`, add a line to your project's `CLAUDE.md` telling Claude to use it:
>
> ```markdown
> When working with React, use the react-docs skill to look up documentation.
> ```
>
> Without this, Claude may rely on training data instead of the indexed docs. The instruction ensures Claude reaches for the skill first — giving you accurate, version-specific answers every time.

### Versioned documentation

Multiple versions of the same library coexist side by side:

```bash
claude /plugin install laravel-11-docs@knowledge
claude /plugin install laravel-12-docs@knowledge
```

Claude picks the right version based on context, or you can ask about a specific one.

---

## Request a Library

Want docs for a library that isn't listed? **[Open a request](https://github.com/eneko-codes/knowledge/issues/new?template=doc-request.yml)** with the library name and documentation URL. No tooling needed on your end — we'll index it and add it to the marketplace.

---

## Index Your Own Docs

The `doc-indexer` plugin lets you generate documentation plugins for **any** site — useful for private docs, niche libraries, or libraries not yet in the marketplace.

```bash
claude /plugin install doc-indexer@knowledge
```

Then tell Claude:

```
Index the sqlc docs
```

or with a specific URL:

```
Index the documentation at https://docs.sqlc.dev/en/stable/ for sqlc
```

If you don't provide a URL, Claude searches for the official docs and confirms with you before crawling.

### What happens

Claude runs a 7-step pipeline:

1. **Crawl** — visits every page on the docs site using a stealth Chromium browser
2. **Extract** — converts each page to structured markdown with code blocks preserved
3. **Summarize** — shows you what was found, grouped by topic
4. **You choose** — you pick which topics to include from a numbered list
5. **Filter** — Claude reviews each page and removes noise (blog posts, archive listings, empty pages). You approve the final list before proceeding
6. **Build** — assembles the filtered content into a plugin with a flat `pages/` directory and a rich SKILL.md index listing sub-topics per file
7. **Validate** — checks structural integrity, then re-visits every source page and compares against the generated markdown (title, headings, code blocks, content length). Mismatches are flagged with screenshots.

Example interaction for a large library:

```
Extracted 287 pages from Laravel 12 documentation.

Topics detected:
 1. Eloquent ORM (42 pages)
 2. Routing (18 pages)
 3. Authentication (24 pages)
 4. Blade Templates (15 pages)
 5. Validation (12 pages)
 6. Queues & Jobs (16 pages)
 ...

Which topics do you want to include? (e.g., "1, 2, 3, 5" or "all")
```

You type `1, 2, 3, 5` and Claude builds a focused plugin with just those topics — no bloat.

### Scope

Choose where to install the generated plugin:

| Scope | Who gets the docs | Use when |
|:------|:------------------|:---------|
| **project** | Whole team (committed to git) | The library is used by the project |
| **user** | Just you, all projects | General-purpose library you use everywhere |

<details>
<summary><strong>Prerequisites</strong></summary>

<br>

doc-indexer requires **Python 3.8+** and downloads a Chromium browser (~200MB) for crawling. Pre-built docs plugins have **no prerequisites**.

**macOS** — Python comes pre-installed on macOS 12.3+.

```bash
brew install python@3.12          # Homebrew
```

**Linux**

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install python3 python3-venv python3-pip

# Fedora / RHEL
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

**Windows**

```powershell
winget install Python.Python.3.12       # winget (recommended)
choco install python --version=3.12     # Chocolatey
scoop install python                    # Scoop
```

**Playwright system libraries** *(Linux only)*

```bash
sudo npx playwright install-deps chromium
```

</details>

<details>
<summary><strong>First-time setup</strong></summary>

<br>

Creates a Python venv and downloads Chromium:

**macOS / Linux**

```bash
cd ~/.claude/plugins/cache/knowledge/*/plugins/doc-indexer/skills/doc-indexer/scripts
bash setup.sh
```

**Windows (PowerShell)**

```powershell
cd $env:USERPROFILE\.claude\plugins\cache\knowledge\*\plugins\doc-indexer\skills\doc-indexer\scripts
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

</details>

<details>
<summary><strong>How the pipeline works</strong></summary>

<br>

```
crawl.py  ──>  extract.py  ──>  [Claude reviews & filters]  ──>  build_plugin.py  ──>  validate.py  ──>  verify.py
 (URLs)        (markdown)       (user picks topics,                (plugin files)       (structure)       (accuracy)
                                 noise removed)
```

**`crawl.py`** — Stealth Chromium browser with anti-fingerprint patches. BFS-crawls from the root URL. Outputs `sitemap.json` with titles, headings, and status for every page.

**`extract.py`** — Finds the main content area via 15 CSS selector heuristics, strips navigation/UI/tab labels/TOC noise, converts to markdown. Resumable — skips already-extracted pages on re-run.

**Claude review** — Reads extracted content, groups by topic, asks user which topics to keep. Then filters out noise: blog posts, archive listings, empty pages, duplicates. User approves the final list.

**`build_plugin.py`** — Writes all pages into a flat `pages/` directory. Generates SKILL.md index with H2 sub-topic descriptions per file.

**`validate.py`** — Structural checks: plugin.json fields, SKILL.md frontmatter, file paths resolve, no empty files.

**`verify.py`** — Accuracy check: re-visits every source URL with Playwright, compares title, heading count, code block count, and content length against the generated markdown. Full-page screenshots of mismatched pages.

</details>

<details>
<summary><strong>CLI Reference</strong></summary>

<br>

**crawl.py** — Discover documentation pages via BFS crawl

```
python3 crawl.py <root-url> [options]

  --output FILE            Output sitemap path (default: sitemap.json)
  --max-depth N            Max link-follow depth from root (default: 10)
  --max-pages N            Stop after N pages, 0 = unlimited (default: 0)
  --delay SECS             Base delay between requests (default: 0.5)
  --same-path-prefix       Only follow links under the root URL's path
```

**extract.py** — Fetch pages and convert to structured markdown

```
python3 extract.py <sitemap.json> [options]

  --output DIR             Output directory for JSON files (default: extracted/)
  --delay SECS             Base delay between requests (default: 0.5)
  --force                  Re-extract even if output file already exists
  --guess-languages        Use Pygments to guess language for unannotated code blocks
```

**build_plugin.py** — Assemble extracted content into a Claude Code plugin

```
python3 build_plugin.py <library-name> <extracted-dir> [options]

  --version LABEL          Documentation version label (default: latest)
  --source-url URL         Original documentation URL
  --output-dir DIR         Plugin output directory
```

**validate.py** — Check plugin structural integrity

```
python3 validate.py <plugin-dir> [options]

  --sitemap FILE           Cross-reference against original sitemap.json
```

**verify.py** — Compare generated content against live source pages

```
python3 verify.py <plugin-dir> [options]

  --delay SECS             Base delay between requests (default: 0.5)
  --screenshot-dir DIR     Save full-page screenshots of mismatched pages
```

</details>

<details>
<summary><strong>Troubleshooting</strong></summary>

<br>

**Playwright fails to install Chromium** — Ensure internet access and ~200MB disk space. On Linux: `sudo npx playwright install-deps chromium`

**Crawl gets blocked (403/429)** — Increase the delay: `python3 crawl.py <url> --delay 3.0`

**Empty markdown extraction** — The content area heuristic may not match the site's HTML. Open an issue with the URL.

**Windows: `source` not found** — Use PowerShell: `.\.venv\Scripts\Activate.ps1`. If blocked: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

</details>

---

## Why Skills Instead of MCP?

Claude Code can access docs two ways: **MCP servers** (like [Context7](https://github.com/upstash/context7) or [docs-mcp-server](https://github.com/arabold/docs-mcp-server)) expose a search API, while **skills** give Claude a complete file-based index it can navigate directly.

Both approaches pre-index documentation. The difference is **how Claude finds what it needs**:

<table>
<tr><th width="50%">MCP Doc Servers</th><th width="50%">Skills (this project)</th></tr>
<tr>
<td>

**Blind search** — Claude formulates a query, calls the search tool, reviews results, and may need to refine and search again. Multiple round-trips if the first query misses.

- LLM must guess the right search terms
- Results depend on query quality
- May need multiple search → refine cycles
- Token cost per tool call (schema + protocol)

</td>
<td>

**Direct navigation** — Claude reads SKILL.md which lists every available page. It sees the full table of contents and navigates directly to the right file.

- LLM sees all available content upfront
- No guessing — picks the right file from the index
- Two reads: index + target file
- No tool call overhead — just file reads

</td>
</tr>
</table>

> **Trade-off:** One-time crawl (5–30 min) to generate the plugin. Re-crawl when docs update — monthly is usually enough.

---

<div align="center">

**MIT License**

</div>
