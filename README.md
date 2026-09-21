# LLM Datetime & Calendar — Claude Code Plugin

A Claude Code plugin containing a deterministic datetime/calendar Agent Skill.

## Structure

```text
llm-datetime-calendar/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── datetime-calendar/
│       ├── SKILL.md
│       └── scripts/
│           └── datetime_tool.py
├── tests/
└── README.md
```

The plugin uses Claude Code's standard plugin layout: the manifest is under
`.claude-plugin/plugin.json`, while skills live at the plugin root under
`skills/<skill-name>/SKILL.md`.

## Install for local development

From the directory containing this plugin:

```bash
claude --plugin-dir ./llm-datetime-calendar
```

Or, if the plugin directory is already the current directory:

```bash
claude --plugin-dir .
```

You can also install/enable it through Claude Code's plugin system.

## Test the skill directly

```bash
python skills/datetime-calendar/scripts/datetime_tool.py now
python skills/datetime-calendar/scripts/datetime_tool.py now --timezone Europe/Berlin
python skills/datetime-calendar/scripts/datetime_tool.py convert --datetime "2026-09-21T21:37:00+03:30" --to-timezone Europe/Berlin
python skills/datetime-calendar/scripts/datetime_tool.py month --month 2026-09
```

## What Claude gets

Claude discovers the `datetime-calendar` skill from:

```text
skills/datetime-calendar/SKILL.md
```

The skill instructs Claude to execute the Python utility rather than trying to
calculate current time or calendar structure from its own model knowledge.

## Important

This is a Claude Code Agent Skill/plugin, not an MCP server.

It does not need a `.mcp.json` because datetime/calendar operations are local
deterministic script operations. If you later want the same functionality exposed
as callable MCP tools to multiple clients, an MCP server can be added separately.
