---
name: {versioned_library}-docs
description: >
  {library_name_title} ({version}) documentation reference. Use when asked about {library_name},
  its API, configuration, usage patterns, or troubleshooting.
  {version_triggers}
---

# {library_name_title} Documentation ({version})

Complete reference for {library_name_title}, extracted from the official documentation.

- **Source:** {source_url}
- **Version:** {version}
- **Plugin name:** {plugin_name}
- **Total pages:** {total_pages}

## Directory Structure

{category_summary}
{quick_reference}
## File Index

{file_listing}

## How to Use

1. Start with `index/SITEMAP.md` for an overview of all available pages.
2. Navigate to the relevant directory based on what you need:
   - `reference/` for API signatures, type definitions, configuration parameters
   - `concepts/` for architecture, design, and how-things-work explanations
   - `guides/` for step-by-step tutorials, how-to procedures
   - `examples/` for code samples, recipes, and cookbooks
   - `troubleshooting/` for deprecation notices, error explanations, debugging
3. Read the specific sub-file for detailed content.

## Important

- All content is extracted verbatim from the official documentation.
- Code blocks are preserved exactly as they appear in the source, with language annotations.
- If content seems outdated, re-run the doc-indexer to refresh.
