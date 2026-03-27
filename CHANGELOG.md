## [0.3.0] - 2026-03-27

### 🚀 Features

- Auto-convert plain text description/environment to ADF #closes bean-3ecbcefb
- Markdown to ADF block nodes — paragraph, heading, code block, blockquote, rule #closes bean-6bd8a8c9
- Markdown to ADF inline marks — bold, italic, code, strikethrough, nested #closes bean-d2be6245
- Markdown to ADF links with mark composition #closes bean-0cdcc25f
- Markdown to ADF lists — bullet, ordered, nested #closes bean-dd90ce05
- Wire markdown_to_adf into resolve_fields, remove text_to_adf #closes bean-4f738fa2

### 📚 Documentation

- Update CHANGELOG.md
- Update skill docs for Markdown description support #closes bean-21af5432

### 🧪 Testing

- Add full-document integration test exercising all ADF features at once

### ⚙️ Miscellaneous Tasks

- Test against Python 3.11, 3.12, 3.13 matrix, relax requires-python to >=3.11
- Add Python 3.14 to test matrix
- Add mistune dependency for Markdown to ADF conversion #closes bean-252df3d4
- Bump to v0.3.0
## [0.2.2] - 2026-03-27

### 🐛 Bug Fixes

- Switch to setuptools build backend for Homebrew compatibility, bump v0.2.2

### 📚 Documentation

- Update CHANGELOG.md
## [0.2.1] - 2026-03-27

### 🐛 Bug Fixes

- Show help when subcommand is missing instead of doing nothing #closes bean-412ca498
- Switch build backend from uv_build to hatchling for Homebrew compatibility

### 📚 Documentation

- Update CHANGELOG.md
- Add banner to README and assets
- Add Homebrew install instructions to README

### ⚙️ Miscellaneous Tasks

- Add homebrew tap auto-update to release workflow
- Bump to v0.2.1
## [0.2.0] - 2026-03-26

### 🚀 Features

- Add jira agent skill, finalize jira-genie rename and description #closes bean-137d4311

### 🐛 Bug Fixes

- Inspect-5p findings — security, correctness, design improvements

### 📚 Documentation

- Export beans journal (sanitized)
- Apply retro improvements to conventions and global AGENTS.md
- Update CHANGELOG.md

### ⚙️ Miscellaneous Tasks

- Rename package to jira-genie, bump to v0.2.0 #closes bean-9fcd9d43
## [0.1.0] - 2026-03-25

### 🚀 Features

- FileCache with file-backed key-value storage and expiry #closes bean-cd0a1792
- Instance discovery with multi-instance resolution #closes bean-1d58d17c
- JiraAuth with refresh token renewal via requestspro #closes bean-9b922e7d
- OAuth login flow with PKCE, token exchange, and config persistence #closes bean-35c47b66
- Pure formatters for issue, sprint, and transition responses #closes bean-08f9ed1a
- Template CRUD with default template support #closes bean-e1d10db5
- Schema sync with field registry and per-type schema discovery #closes bean-ef3d29e5
- Field resolution with name mapping and value expansion #closes bean-ec7a488f
- JiraClient with IssueSubClient and SearchSubClient #closes bean-d4c5f23c
- CLI with auth login/status/logout and parse/cli pattern #closes bean-e9690c48
- Build_issue_fields with template merge and field resolution #closes bean-acda4516
- CLI fields sync/list/schema commands #closes bean-463bfd6a
- Sprint/Board/User sub-clients, issue ops, and CLI issue/search/bulk commands
- CLI template, sprint, board, user commands and issue create
- Wire OAuth login flow, auth status, and auth logout in CLI
- Shell completion with argcomplete for commands, templates, and field values #closes bean-85d6704f
- Hardcode OAuth credentials with flag and env var overrides #closes bean-87c4c01b
- Auto-discover projects in fields sync, preserve existing schemas #closes bean-a2d17a66

### 🐛 Bug Fixes

- Remove unnecessary manage:jira-project scope
- Client_secret support, CloudFront GET body issue, and search API v3 migration
- Wire fields CLI, fix field resolution for project/issuetype/parent, handle empty DELETE response
- Expand components array to named objects in field resolution
- Detect user shell for completion install instructions

### 📚 Documentation

- Add project plan, conventions, and agent instructions
- Add MIT license and privacy policy for Atlassian app listing
- Comprehensive README focused on agent integration #closes bean-7985e7a2
- Update README for optional --project in fields sync

### 🧪 Testing

- Full coverage for auth.py — login flow, callback server, authorize URL, error paths

### ⚙️ Miscellaneous Tasks

- Set up beans task tracking with full project breakdown
- Project skeleton with pyproject.toml, src layout, dev tooling #closes bean-653fb364
- Rename package to jira-pro, update config dir and all references #closes bean-c0ab0f77
- Add CI and release workflows with changelog generation
