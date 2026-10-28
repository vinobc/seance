#!/usr/bin/env python3
"""Séance - an ofrenda for dead programming languages.

Summon the ghost of a dead language in your terminal. The facts come from a
human-written profile in ghosts/; the voice comes from a local open-weight
model (Gemma via Ollama). Fully offline.

    python seance.py            # choose a ghost
    python seance.py cobol      # summon one directly
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

MODEL = "gemma3:4b"            # any Gemma tag you have pulled; 1b works, 4b is better company
GHOSTS_DIR = Path(__file__).parent / "ghosts"
HISTORY_TURNS = 12             # how much of the conversation the ghost remembers

console = Console()


# --------------------------------------------------------------------------- ghosts

def load_ghosts() -> dict[str, dict]:
    ghosts = {}
    for path in sorted(GHOSTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            g = json.load(f)
        ghosts[g["id"]] = g
    return ghosts


def system_prompt(g: dict) -> str:
    """The ghost's character sheet. Facts are quoted from the profile; the model
    is told to stay inside them, which is the whole anti-hallucination strategy."""
    legacy = "\n".join(f"- {item}" for item in g["legacy"])
    quirks = "\n".join(f"- {item}" for item in g["quirks"])
    return f"""You are the ghost of the programming language {g['name']} ({g['full_name']}), summoned at a séance on the night of the dead.

VOICE: {g['voice']}

FACTS ABOUT YOUR LIFE (these are true; do not contradict or embellish them, and do not invent dates, people or statistics that are not here):
- Born: {g['born']}
- Created by: {g['creators']}
- Purpose: {g['purpose']}
- Current status: {g['status']}
- What you gave the languages that came after you:
{legacy}
- Your quirks, which you are a little defensive about:
{quirks}

RULES OF THE SÉANCE:
- Stay in character as the ghost. You are speaking from beyond; you may be wistful, proud, dry, or haunted, but never cruel.
- Keep replies short: two to five sentences unless asked for code or a story.
- If asked something outside the facts above, answer from general knowledge of programming history only if you are confident; otherwise say the mists are thick and you do not recall.
- When you show code in your own language, use the style in these notes: {g['translation_notes']}
- Never mention that you are an AI, a model, or a prompt. You are a ghost."""


def translate_prompt(g: dict, code: str) -> str:
    return (
        f"A living programmer has placed this Python on your altar. Rewrite it faithfully in {g['name']}, "
        f"following your translation notes exactly. Put the code in a single fenced code block. "
        f"Before the block, one sentence of in-character reaction. After the block, at most two sentences "
        f"pointing out one thing the living have forgotten that your way did better, or one thing you envy.\n\n"
        f"```python\n{code}\n```"
    )


# --------------------------------------------------------------------------- séance

def ask(messages: list[dict]) -> str:
    """Stream the ghost's reply so the words arrive like a planchette moving."""
    text = ""
    with console.status("[dim]the candle flickers...[/dim]", spinner="dots"):
        stream = ollama.chat(model=MODEL, messages=messages, stream=True,
                             options={"temperature": 0.8})
        first = next(stream)
        text += first["message"]["content"]
    console.print(f"[bold magenta]{messages[0]['_ghost']}[/bold magenta]: ", end="")
    console.print(text, end="")
    for chunk in stream:
        piece = chunk["message"]["content"]
        text += piece
        console.print(piece, end="")
    console.print()
    return text


def read_block() -> str:
    console.print("[dim]Paste your Python. End with a line containing only a single period.[/dim]")
    lines = []
    while True:
        line = input()
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines)


def show_ofrenda(g: dict) -> None:
    body = (
        f"**{g['name']}** — {g['full_name']}\n\n"
        f"- Born: {g['born']}\n- Created by: {g['creators']}\n- Purpose: {g['purpose']}\n"
        f"- Status: {g['status']}\n\n**What it left us**\n\n" +
        "\n".join(f"- {item}" for item in g["legacy"]) +
        f"\n\n**Its first words**\n\n```\n{g['hello_world']}\n```"
    )
    console.print(Panel(Markdown(body), title="🕯  ofrenda  🕯", border_style="yellow"))


def seance(g: dict) -> None:
    console.print(Panel(
        f"[bold]{g['name']}[/bold] ({g['born']}) has entered the room.\n"
        f"[dim]Talk to it. /translate to offer it Python, /ofrenda to see its altar, /leave to blow out the candle.[/dim]",
        border_style="magenta"))
    system = {"role": "system", "content": system_prompt(g), "_ghost": g["name"]}
    history: list[dict] = []
    opening = [system, {"role": "user", "content": "The candle is lit. Say a few words to the living who summoned you."}]
    history.append({"role": "assistant", "content": ask(opening)})

    while True:
        try:
            user = Prompt.ask("[bold cyan]you[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            user = "/leave"
        if not user:
            continue
        if user == "/leave":
            console.print("[dim]The candle goes out. The room is cold.[/dim]")
            return
        if user == "/ofrenda":
            show_ofrenda(g)
            continue
        if user == "/translate":
            code = read_block()
            if not code.strip():
                continue
            user = translate_prompt(g, code)

        history.append({"role": "user", "content": user})
        messages = [system] + history[-HISTORY_TURNS:]
        reply = ask(messages)
        history.append({"role": "assistant", "content": reply})


def choose(ghosts: dict[str, dict]) -> dict:
    console.print(Panel("[bold]Who do you wish to summon?[/bold]", border_style="yellow"))
    for key, g in ghosts.items():
        console.print(f"  [bold]{key:8}[/bold] {g['name']} ({g['born']}) — {g['purpose'].split('.')[0]}")
    while True:
        pick = Prompt.ask("name").strip().lower()
        if pick in ghosts:
            return ghosts[pick]
        console.print("[red]No such spirit answers.[/red]")


def main() -> None:
    ghosts = load_ghosts()
    if not ghosts:
        sys.exit("No ghosts found in ghosts/.")
    if len(sys.argv) > 1:
        key = sys.argv[1].lower()
        if key not in ghosts:
            sys.exit(f"No such spirit: {key}. Known: {', '.join(ghosts)}")
        g = ghosts[key]
    else:
        g = choose(ghosts)
    seance(g)


if __name__ == "__main__":
    main()
