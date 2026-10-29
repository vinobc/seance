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
import re
import shutil
import subprocess
import sys
import tempfile
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


# --------------------------------------------------------------------------- the medium

# The ghost speaks; a real compiler judges. Each entry: (binary, args builder, source suffix).
# If the compiler is not installed, the séance still works, it just takes the ghost at its word.
COMPILERS = {
    "cobol":   ("cobc",     lambda src, out: ["cobc", "-x", "-free", "-o", out, src], ".cob"),
    "fortran": ("gfortran", lambda src, out: ["gfortran", "-std=legacy", "-o", out, src], ".f"),
    "pascal":  ("fpc",      lambda src, out: ["fpc", "-o" + out, src], ".pas"),
    "lisp":    ("sbcl",     lambda src, out: ["sbcl", "--script", src], ".lisp"),
}
MAX_ATTEMPTS = 3


def extract_code(reply: str) -> str | None:
    m = re.search(r"```[a-zA-Z0-9_+-]*\n(.*?)```", reply, re.S)
    return m.group(1) if m else None


def compile_check(ghost_id: str, code: str) -> tuple[bool, str]:
    """Return (ok, message). ok is True when the compiler accepts the code (or none is installed)."""
    spec = COMPILERS.get(ghost_id)
    if not spec or not shutil.which(spec[0]):
        return True, "no compiler present; the ghost's word is taken on faith"
    binary, build, suffix = spec
    with tempfile.TemporaryDirectory() as tmp:
        src = str(Path(tmp) / f"offering{suffix}")
        out = str(Path(tmp) / "offering")
        Path(src).write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(build(src, out), capture_output=True, text=True, timeout=60, cwd=tmp)
        except subprocess.TimeoutExpired:
            return False, "the compiler did not answer within a minute"
    if r.returncode == 0:
        return True, f"{binary} accepted the code"
    err = (r.stderr or r.stdout).strip()
    lines = [l for l in err.splitlines() if l.strip()][:12]
    return False, "\n".join(lines)


def retry_prompt(g: dict, errors: str) -> str:
    return (
        f"The living ran your {g['name']} through a real {g['name']} compiler and it refused the offering. "
        f"Here are the compiler's words:\n\n{errors}\n\n"
        f"Fix the lines the compiler points at (remove any line it calls invalid; do not add new divisions or sections). "
        f"Reply with one short in-character sentence, then the COMPLETE corrected "
        f"program in a single fenced code block (never a fragment), following your translation notes exactly."
    )


# --------------------------------------------------------------------------- séance

def ask(messages: list[dict], temperature: float = 0.8) -> str:
    """Stream the ghost's reply so the words arrive like a planchette moving.
    Conversation runs warm (0.8) for personality; code runs cold (0.2) for accuracy."""
    text = ""
    with console.status("[dim]the candle flickers...[/dim]", spinner="dots"):
        stream = ollama.chat(model=MODEL, messages=messages, stream=True,
                             options={"temperature": temperature})
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
            translate_with_medium(g, system, history, code)
            continue

        history.append({"role": "user", "content": user})
        messages = [system] + history[-HISTORY_TURNS:]
        reply = ask(messages)
        history.append({"role": "assistant", "content": reply})


def translate_with_medium(g: dict, system: dict, history: list[dict], code: str) -> None:
    """Ask the ghost to translate; let the compiler be the medium; give the ghost up to
    MAX_ATTEMPTS to produce something the living machine accepts."""
    history.append({"role": "user", "content": translate_prompt(g, code)})
    previous = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # cold first, warmer on each retry so a small model does not repeat itself verbatim
        reply = ask([system] + history[-HISTORY_TURNS:], temperature=0.2 + 0.3 * (attempt - 1))
        history.append({"role": "assistant", "content": reply})
        offered = extract_code(reply)
        if offered is None:  # the ghost talked but did not write; insist once
            history.append({"role": "user", "content":
                            "You gave no program. Reply with the complete corrected program in a single fenced code block, nothing else."})
            reply = ask([system] + history[-HISTORY_TURNS:], temperature=0.2)
            history.append({"role": "assistant", "content": reply})
            offered = extract_code(reply)
        if offered is None:
            console.print("[dim]the medium: the ghost would not write[/dim]")
            return
        ok, msg = compile_check(g["id"], offered)
        if ok:
            console.print(f"[green]the medium:[/green] {msg} (attempt {attempt})")
            return
        console.print(Panel(msg, title=f"the medium: the compiler refused (attempt {attempt})",
                            border_style="red"))
        if attempt == MAX_ATTEMPTS:
            console.print("[dim]the medium: three attempts; the dead are allowed their mistakes[/dim]")
            return
        nudge = retry_prompt(g, msg)
        if previous is not None and offered.strip() == previous.strip():
            nudge += "\n\nYour last offering was identical to the one before it. You must change the lines the compiler points at."
        previous = offered
        history.append({"role": "user", "content": nudge})


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
