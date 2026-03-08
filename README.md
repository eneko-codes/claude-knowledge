# supercharge

A Claude Code plugin marketplace for generating documentation plugins from external documentation sites.

## Why This Exists: Skills vs MCP for Documentation

Claude Code can access external documentation in two ways: **MCP servers** (real-time API calls) and **skills** (pre-indexed local files). This project takes the skills approach, and here's why.

### The MCP Documentation Problem

MCP (Model Context Protocol) servers fetch documentation on-the-fly by calling external APIs or scraping pages at query time. This has significant drawbacks for documentation use cases:

| Issue | Impact |
|-------|--------|
| **Latency** | Every documentation lookup requires an HTTP round-trip (200-2000ms), sometimes multiple. A single coding question may need 3-5 lookups, adding seconds of wait time. |
| **Reliability** | External APIs go down, rate-limit, change endpoints, or require authentication. A documentation MCP server that worked yesterday may fail today. |
| **Token overhead** | MCP tool calls consume tool-use tokens for the request/response protocol on top of the actual content. A 500-token answer requires ~800 tokens when fetched via MCP. |
| **Incomplete context** | MCP servers typically fetch one page at a time. Claude can't cross-reference related pages or see the full documentation structure without multiple sequential calls. |
| **Bot detection** | Many documentation sites (Cloudflare-protected, rate-limited) block automated HTTP requests. MCP servers using simple `fetch()` get 403/429 errors on exactly the sites you most need. |
| **No offline access** | MCP documentation servers require internet connectivity. If you're on a plane, on a train, or behind a restrictive corporate firewall, documentation is unavailable. |

### The Skills Approach

Skills solve all of these problems by **pre-indexing documentation into local files** that Claude reads directly from disk:

| Advantage | How |
|-----------|-----|
| **Zero latency** | Documentation is local markdown files. Reading a file takes <1ms, not 200-2000ms. |
| **100% reliable** | No external dependencies at query time. Files don't go down, rate-limit, or change their API. |
| **Token efficient** | Direct file reads have no protocol overhead. Claude reads exactly the content it needs. |
| **Full context** | The SKILL.md index gives Claude a complete map of all documentation. It can cross-reference API pages, examples, and conceptual docs in a single response. |
| **Hierarchical navigation** | Documentation is organized into `api/`, `concepts/`, `examples/`, `warnings/` directories. Claude reads the index first and navigates to the relevant section — no wasted tokens on irrelevant content. |
| **Works offline** | Once generated, the plugin works without internet access. |

### The Trade-off

The skills approach requires a one-time crawl to generate the plugin (5-30 minutes depending on documentation size). Documentation updates require re-running the crawler. For most libraries, documentation changes infrequently enough that weekly or monthly re-crawls are sufficient.

### Research and Evidence

The effectiveness of local, pre-indexed documentation over real-time fetching is supported by several observations from the Claude Code ecosystem:

1. **The official plugin marketplace uses the same pattern.** Anthropic's own `claude-plugins-official` repository distributes documentation as local skill files (e.g., the Stripe plugin uses local markdown references, not MCP calls to the Stripe API).

2. **Context window utilization.** Claude's 200K token context window is most effective when filled with relevant content, not protocol overhead. A pre-indexed documentation plugin can load a complete SITEMAP.md (listing all available pages) in ~2K tokens, giving Claude a map of the entire library. An MCP server would need to be called just to discover what pages exist.

3. **Deterministic behavior.** Local files produce deterministic, reproducible answers. MCP servers can return different results due to A/B testing, geo-routing, CDN caching, or page updates between calls.

4. **Community convergence.** Multiple Claude Code plugin developers have independently converged on the "crawl once, read locally" pattern for documentation, suggesting it's a natural optimum for this use case.

## Plugins

| Plugin | Description |
|--------|-------------|
| **doc-scanner** | Crawls external documentation sites and generates complete documentation plugins |

## Prerequisites

### Python 3.8+

doc-scanner requires Python 3.8 or later (tested on 3.9, 3.11, 3.12).

<details>
<summary><strong>macOS</strong></summary>

Python 3 comes pre-installed on macOS 12.3+. Verify with:

```bash
python3 --version
```

If not installed or you need a newer version:

```bash
# Homebrew
brew install python@3.12

# MacPorts
sudo port install python312
```

</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
# APT (Ubuntu 22.04+ includes Python 3.10+)
sudo apt update && sudo apt install python3 python3-venv python3-pip

# Or install a specific version
sudo apt install python3.12 python3.12-venv
```

</details>

<details>
<summary><strong>Linux (Fedora/RHEL/CentOS)</strong></summary>

```bash
# DNF
sudo dnf install python3 python3-pip

# Or a specific version
sudo dnf install python3.12
```

</details>

<details>
<summary><strong>Linux (Arch)</strong></summary>

```bash
sudo pacman -S python python-pip
```

</details>

<details>
<summary><strong>Windows</strong></summary>

```powershell
# winget (recommended)
winget install Python.Python.3.12

# Chocolatey
choco install python --version=3.12

# Scoop
scoop install python
```

Or download from [python.org](https://www.python.org/downloads/windows/).

> **Important:** During installation, check "Add Python to PATH".

</details>

### Claude Code

doc-scanner is a Claude Code plugin. You need Claude Code installed:

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
# npm (requires Node.js 18+)
npm install -g @anthropic-ai/claude-code

# Homebrew
brew install claude-code
```

</details>

<details>
<summary><strong>Windows</strong></summary>

```powershell
# npm (requires Node.js 18+)
npm install -g @anthropic-ai/claude-code
```

</details>

### Playwright System Dependencies

Playwright's Chromium browser requires certain system libraries. The `playwright install chromium` command handles the browser download, but some Linux distributions need additional system packages.

<details>
<summary><strong>macOS</strong></summary>

No additional system dependencies needed. Playwright's Chromium bundle is self-contained on macOS.

</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
# Install system dependencies for Chromium
sudo npx playwright install-deps chromium

# Or manually:
sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

</details>

<details>
<summary><strong>Linux (Fedora/RHEL)</strong></summary>

```bash
sudo dnf install nss nspr atk at-spi2-atk cups-libs libdrm \
  libxkbcommon libXcomposite libXdamage libXfixes libXrandr mesa-libgbm \
  pango cairo alsa-lib
```

</details>

<details>
<summary><strong>Windows</strong></summary>

No additional system dependencies needed. Playwright's Chromium bundle is self-contained on Windows.

</details>

## Installation

### Step 1: Add the Marketplace

```bash
claude /plugin marketplace add https://github.com/eneko-codes/claude-plugins
```

### Step 2: Install the Plugin

```bash
claude /plugin install doc-scanner@supercharge
```

### Step 3: Run Setup (One-Time)

The first time you use doc-scanner, Claude will run the setup script automatically. This creates a Python virtual environment and downloads Chromium (~200MB). You can also run it manually:

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
cd ~/.claude/plugins/cache/supercharge/*/plugins/doc-scanner/skills/doc-scanner/scripts
bash setup.sh
```

</details>

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
cd $env:USERPROFILE\.claude\plugins\cache\supercharge\*\plugins\doc-scanner\skills\doc-scanner\scripts
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

> **Note:** On Windows, use `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`. The Python scripts themselves are cross-platform.

</details>

## Usage

Once installed, tell Claude to scan documentation for any library:

```
> Scan the documentation at https://docs.sqlc.dev/en/stable/ and generate a docs plugin for sqlc
```

```
> Crawl the htmx documentation at https://htmx.org/docs/ and create a plugin
```

```
> Index the Goose library docs at https://pressly.github.io/goose/
```

Claude will:
1. Ask for any missing parameters (library name, version)
2. Crawl all documentation pages
3. Extract and classify content
4. Build a complete documentation plugin
5. Validate coverage
6. Register it in the marketplace

### What Gets Generated

For a library called `sqlc`, doc-scanner produces:

```
plugins/docs-sqlc/
├── .claude-plugin/
│   └── plugin.json                          # Plugin metadata
└── skills/sqlc-docs/
    ├── SKILL.md                             # Entry point — full file index
    ├── index/
    │   └── SITEMAP.md                       # Complete page listing
    ├── api/                                 # API reference pages
    │   ├── configuration.md
    │   ├── query-annotations.md
    │   └── ...
    ├── concepts/                            # Conceptual docs + tutorials
    │   ├── overview.md
    │   ├── getting-started.md
    │   └── ...
    ├── examples/                            # Code-heavy example pages
    │   ├── using-sqlc-with-postgresql.md
    │   └── ...
    └── warnings/                            # Deprecation notices
        └── WARNINGS.md
```

### Using a Generated Plugin

After doc-scanner generates a plugin, install it:

```bash
claude /plugin install docs-sqlc@supercharge
```

Then ask Claude questions about the library — it will automatically use the documentation:

```
> What's the configuration format for sqlc.yaml?
> How do I use sqlc with PostgreSQL arrays?
> What functions does sqlc generate for a query?
```

## Pipeline Scripts

The doc-scanner skill orchestrates four Python scripts that form a pipeline:

```
crawl.py → extract.py → build_plugin.py → validate.py
```

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `crawl.py` | Root URL | `sitemap.json` | BFS crawl to discover all doc pages |
| `extract.py` | `sitemap.json` | `extracted/*.json` | Fetch and convert each page to structured markdown |
| `build_plugin.py` | `extracted/` dir | Complete plugin directory | Assemble content into plugin structure |
| `validate.py` | Plugin directory | Coverage report | Verify completeness and correctness |

### Manual Usage

You can run the scripts directly without Claude if needed:

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
cd plugins/doc-scanner/skills/doc-scanner/scripts
source .venv/bin/activate

# 1. Crawl documentation
python3 crawl.py https://pressly.github.io/goose/ \
  --output /tmp/goose-sitemap.json \
  --same-path-prefix

# 2. Extract content
python3 extract.py /tmp/goose-sitemap.json \
  --output /tmp/goose-extracted/

# 3. Build plugin
python3 build_plugin.py goose /tmp/goose-extracted/ \
  --source-url https://pressly.github.io/goose/ \
  --output-dir ../../../../../../plugins/docs-goose

# 4. Validate
python3 validate.py ../../../../../../plugins/docs-goose/ \
  --sitemap /tmp/goose-sitemap.json
```

</details>

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
cd plugins\doc-scanner\skills\doc-scanner\scripts
.\.venv\Scripts\Activate.ps1

# 1. Crawl documentation
python crawl.py https://pressly.github.io/goose/ `
  --output $env:TEMP\goose-sitemap.json `
  --same-path-prefix

# 2. Extract content
python extract.py $env:TEMP\goose-sitemap.json `
  --output $env:TEMP\goose-extracted\

# 3. Build plugin
python build_plugin.py goose $env:TEMP\goose-extracted\ `
  --source-url https://pressly.github.io/goose/ `
  --output-dir ..\..\..\..\..\..\plugins\docs-goose

# 4. Validate
python validate.py ..\..\..\..\..\..\plugins\docs-goose\ `
  --sitemap $env:TEMP\goose-sitemap.json
```

</details>

## How It Works

### Crawling (crawl.py)

- Launches a headless Chromium browser with [playwright-stealth](https://github.com/nickmilo/playwright-stealth) patches that modify 20+ browser fingerprint vectors (navigator.webdriver, chrome.runtime, WebGL vendor, etc.)
- Performs BFS traversal starting from the root URL, following only same-domain links
- `--same-path-prefix` restricts crawling to the URL subtree (critical for versioned docs like `/en/stable/`)
- Adds randomized delay between requests (default 1.5s ± 0.5s) to mimic human browsing
- Handles redirects, HTTP errors, and JavaScript-rendered pages
- Outputs a `sitemap.json` with URL, title, H1/H2/H3 headings, and HTTP status for every page

### Extraction (extract.py)

- Re-visits each page from the sitemap with the same stealth browser
- Detects the main content area using 15 CSS selector heuristics (`<main>`, `<article>`, `[role="main"]`, `.docs-content`, etc.)
- Strips navigation, sidebar, header, footer, and UI widgets (copy buttons, breadcrumbs, etc.)
- Converts HTML to markdown using [html2text](https://github.com/Alir3z4/html2text) with settings that preserve code blocks, links, and formatting
- Classifies each page as: `api-reference`, `conceptual`, `tutorial`, `example`, or `warning`
- Extracts function signatures using language-specific regex patterns (Go, Python, TypeScript, Rust, Java)

### Plugin Generation (build_plugin.py)

- Groups pages by category into directories: `api/`, `concepts/`, `examples/`, `warnings/`
- Generates one markdown file per page using a template (title, source URL, full content)
- Consolidates all warning/deprecation pages into a single `warnings/WARNINGS.md`
- Builds `index/SITEMAP.md` — a complete page listing grouped by category
- Generates `SKILL.md` — the entry point Claude reads, with trigger phrases, quick reference for top API functions, and a complete file index
- Generates `.claude-plugin/plugin.json` metadata

### Validation (validate.py)

Runs 7 checks with clear PASS/FAIL output:
1. `plugin.json` exists with required fields
2. `SKILL.md` has YAML frontmatter and substantial content
3. `SITEMAP.md` exists
4. Page count matches between generated files and sitemap (accounting for warning consolidation)
5. Section coverage: >= 90% of sitemap headings found in content files
6. Link resolution: all file paths in SKILL.md point to existing files
7. No empty content files

## Troubleshooting

### Playwright fails to install Chromium

**Symptom:** `playwright install chromium` hangs or fails.

**Fix:** Ensure you have internet access and sufficient disk space (~200MB). On Linux, install system dependencies first:

```bash
sudo npx playwright install-deps chromium
```

### Crawl gets blocked (403/429 errors)

**Symptom:** Many pages return HTTP 403 or 429 in the sitemap.

**Fix:** Increase the delay to be more polite:

```bash
python3 crawl.py <url> --delay 3.0
```

Some sites may require even longer delays or may block automated access entirely.

### Extraction produces empty markdown

**Symptom:** Extracted JSON files have empty `markdown` fields.

**Fix:** The content area heuristic may not match the site's HTML structure. Check the site's HTML to find the content selector and file an issue with the site URL so we can add support.

### Windows: `source .venv/bin/activate` fails

**Symptom:** `source: not found` or similar error.

**Fix:** On Windows, use PowerShell instead of Command Prompt, and activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell execution policy blocks it:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## License

MIT
