# Séance

*An ofrenda for dead programming languages.*

Summon the ghost of COBOL, FORTRAN, Pascal, BASIC or Lisp in your terminal. It tells you its story, what it gave to the languages that outlived it, and, if you paste in some Python, rewrites it in its own dialect while complaining about your indentation. Runs entirely offline on a local open-weight model (Gemma via Ollama).

Built for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26).

## Quick start

```bash
# 1. Install Ollama (https://ollama.com) and pull a Gemma model
ollama pull gemma3:4b

# 2. Install Python deps
pip install -r requirements.txt

# 3. Light a candle
python seance.py                 # choose a ghost
python seance.py cobol           # summon one directly
```

Inside the séance:

- just type to talk to the ghost
- `/translate` then paste Python, end with a line containing only `.` — the ghost rewrites it in its own tongue
- `/ofrenda` — the ghost's altar: dates, creator, legacy, and its canonical first program
- `/leave` — blow out the candle

## How it works

The facts are human-written; the voice is the model's. Each ghost in `ghosts/` is a small profile with dates, creator, purpose, legacy and a canonical hello-world program, checked against the historical record. The model never invents history: the profile is injected into its system prompt, and it is told to stay inside it. What the model *does* bring is the thing a 1990s textbook can't: a personality, a conversation, and the ability to translate your code into a dialect that has not been written in anger for decades.

## The medium

A ghost's memory is imperfect. When you `/translate`, Séance hands the ghost's code to a real compiler for that language if one is installed (`cobc` from GnuCOBOL, `gfortran`, `fpc`, `sbcl`). If the compiler refuses, its error messages go back to the ghost, which gets up to three attempts. The ghost speaks; the compiler is the medium. Without a compiler installed, the séance still works and takes the ghost at its word.

```bash
brew install gnucobol gcc fpc sbcl    # optional, any subset
```

## Ghosts

`cobol` (1959), `fortran` (1957), `pascal` (1970), `basic` (1964), `lisp` (1958). Add your own: copy a file in `ghosts/` and fill in the altar.

## License

MIT
