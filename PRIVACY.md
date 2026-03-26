# Privacy Policy

**jira-genie** is an open-source command-line tool. It does not collect, transmit, or share any user data.

## What is stored locally

When you run `jira auth login`, the following are saved to `~/.config/jira-genie/` on your machine:

- **OAuth refresh token** — used to authenticate with your Jira Cloud instance
- **Cloud ID and site URL** — identifies which Jira instance you're connected to
- **Schema cache** — a copy of your instance's field configuration (field names, types, allowed values)

All data stays on your machine. Nothing is sent to any server other than Atlassian's API (`api.atlassian.com`, `auth.atlassian.com`).

## How to remove your data

```bash
jira auth logout
```

This deletes all stored tokens and configuration for your instance.

## No warranty

This software is provided "as is" under the [MIT License](LICENSE), without warranty of any kind.
