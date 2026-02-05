---
name: terminal-code
description: Referência do Code CLI para desenvolvimento. Comandos, slash commands, atalhos.
triggers:
  - terminal
  - cli
  - code
  - comando
  - command
  - slash
  - init
  - help
---

# WINDI Terminal Code CLI Reference

Complete reference for AI Code terminal commands in WINDI development context.

## Starting Sessions

claude - Start interactive session
claude "task" - Start with initial prompt
claude -p "query" - One-time query (no session)
claude -c - Continue last session
claude --resume [id] - Resume specific session

## Essential Slash Commands

Session Management:
/help - Show all available commands
/exit or /quit - End session
/clear - Reset conversation context
/compact - Compress context to save tokens
/status - Show version and connectivity

Project Context:
/init - Create CLAUDE.md project file
/context - Visualize context usage
/add-dir [path] - Add working directory
/cost - Show token costs

Code Operations:
/review - Request code review
/todos - List tracked TODO items
/doctor - Health check installation
/model - Switch AI model

## File & Command Prefixes

@ - Reference file (example: @./src/main.py)
! - Run shell command (example: !npm test)

## Think Modes

Standard (80% of tasks): "Add a button to navigation"
Think mode (15%): "think: How should I structure the database?"
Think-hard (5%): "think hard: Refactor the complete API"

## WINDI-Specific Commands

Start in WINDI project:
cd /opt/windi && claude

Analyze WINDI engine:
"liste os arquivos na pasta engine e me explique"

Check Three Dragons:
"analise dragon_apis.py e explique o protocolo"
