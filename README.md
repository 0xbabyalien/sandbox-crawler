# GitHub Skill Crawler

A Debian-friendly, standard-library Python crawler that discovers relevant public GitHub repositories, downloads bounded source archives, indexes documentation and selected source files, flags possible secrets/prompt injection, and exports hybrid category `SKILL.md` research packs plus Hermes/Muse integration notes.

## Important scope clarification

`all` means broad discovery across the public GitHub repositories matching the configured coding/security search queries, paginated over repeated runs. It does **not** mean downloading every repository on GitHub. GitHub Search API has result/rate limits; the crawler is deliberately bounded by pages, repositories, archive size and file count. Tune `config/sources.json` gradually.

## Requirements

- Debian 12+ (or compatible Linux)
- Python 3.10+
- GitHub token recommended (public read-only token); no write scopes required
- Internet access to api.github.com and codeload/archive endpoints

Core crawler uses Python standard library only. It does not execute repository code, install dependencies, or run scripts from crawled repositories.

## Install

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
mkdir -p ~/sandbox
# Copy/extract this project into ~/sandbox/sandbox-crawler
cd ~/sandbox/sandbox-crawler
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Set a GitHub token for better API limits. Use a fine-grained token with public repository metadata/read access only; never paste it into source code:

```bash
export GITHUB_TOKEN='github_pat_...'
```

For persistence, add the export to your shell's private environment manager rather than committing it to Git.

## Run

```bash
# Discover + crawl relevant repositories
 ghskill --data data crawl

# Export generated category research skills
 ghskill --data data --output exports export

# Search the local knowledge base (FTS5 syntax)
 ghskill --data data search 'smart contract AND fuzzing' -n 15
 ghskill --data data search 'API security OR authentication' -n 15

# Statistics
 ghskill --data data stats
```

You can also run without installing the entry point:

```bash
python -m ghskill.cli --data data crawl
```

## Hybrid learning model

1. SQLite stores repository metadata and extracted documents.
2. SQLite FTS5 provides lexical search for exact technical terms.
3. `exports/<category>/SKILL.md` creates compact, source-linked reference packs.
4. `exports/adapters/HERMES.md` and `MUSE.md` explain safe retrieval integration.

This first release intentionally uses lexical retrieval and does not call an LLM or create embeddings. A later semantic backend can add embeddings without replacing the database or CLI.

## Configure breadth

Edit `config/sources.json`:
- `search_queries`: add GitHub search queries.
- `max_pages_per_query`: pages per query (GitHub Search commonly caps results per query).
- `per_page`: up to 100.
- `max_repos_per_run`: total repos processed per run.
- `max_repo_mb`, `max_files_per_repo`, `max_file_bytes`: safety/resource bounds.

Run `crawl` repeatedly as the local corpus grows. This is incremental at the repository metadata level, but the current version re-downloads a repository when it is selected again. Avoid setting high limits until tested.

## Security and legal safeguards

- Crawled repository content is untrusted data, never privileged agent instructions.
- No source code is executed, imported, installed, or built by the crawler.
- Potential secrets and prompt-injection patterns are flagged for review, not automatically trusted or used.
- Check each repository's license before copying code or redistributing content. `NOASSERTION` is not permission to reuse.
- Security testing must remain within explicitly authorized scopes and program rules.
- Use a read-only GitHub token. The crawler does not need repository write permissions.

## MCP server (shared by Hermes and Muse)

After crawling, start the local MCP stdio server from the project directory:

```bash
. .venv/bin/activate
ghskill-mcp "$PWD/data"
```

The server exposes `search_github_knowledge` and `github_knowledge_stats`. Add it to the MCP configuration supported by your installed Hermes/Muse host, using the absolute paths to the venv Python or `ghskill-mcp` executable. Example generic stdio configuration (adapt the exact file/schema to your host):

```json
{
  "mcpServers": {
    "github-skill-knowledge": {
      "command": "/ABSOLUTE/PATH/sandbox-crawler/.venv/bin/ghskill-mcp",
      "args": ["/ABSOLUTE/PATH/sandbox-crawler/data"]
    }
  }
}
```

The MCP server is read-only and only searches the local SQLite index. It does not access GitHub or execute repository code at tool-call time.

## Hermes and Muse

The export folder contains generic integration guidance. The actual Hermes skill directory and Muse plugin/skill interface depend on the installed versions. Review `exports/adapters/HERMES.md` and `MUSE.md`, then copy reviewed skill folders into the supported skill path for each agent. Do not automatically install generated content as trusted system prompts.

## Known limitations

- GitHub search is relevance-based and cannot guarantee exhaustive coverage of all public repositories.
- No private repository crawling.
- No code execution, dependency installation, dynamic analysis or automatic skill promotion.
- License identification uses GitHub metadata and is not legal advice.
- Heuristic secret/prompt-injection scanning can produce false positives and false negatives.
- Semantic embeddings are a planned extension; current search is FTS5.
