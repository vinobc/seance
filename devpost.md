*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

## What I Built

**Séance** is an ofrenda for dead programming languages. Run it in a terminal, light the candle, and summon the ghost of COBOL, FORTRAN, Pascal, BASIC or Lisp. The ghost speaks in the voice of its era, tells you what it was for and what it gave the languages that outlived it, and, if you place some Python on its altar, rewrites it in its own dialect, usually with a remark about your lack of discipline.

Then comes the part I'm proudest of: a real compiler for that language judges the ghost's code. The ghost speaks; the compiler is the medium.

It runs entirely offline on Gemma 3 4B through Ollama. I teach computer science at a university in Bengaluru, and the history of programming languages is a topic students politely endure. A COBOL that sighs at your indentation turns out to be a better lecturer than I am.

## Demo

```
COBOL (1959) has entered the room.

COBOL: (A dry, rustling sound, like old paper)
"You have disturbed a process. A significant one. I am COBOL. And I assure
you, I am still... operational."

you: /translate
    for n in range(1, 6):
        if n % 2 == 0:
            print(n, "is even")
        else:
            print(n, "is odd")

COBOL: (A faint, metallic sigh)
"This... *Python*. A curious construct. It is... inefficient."

       IDENTIFICATION DIVISION.
       PROGRAM-ID. EVENODD.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 COUNTER PIC 9(4) VALUE 1.
       PROCEDURE DIVISION.
           PERFORM UNTIL COUNTER > 5
               IF COUNTER MOD 2 = 0
                   DISPLAY COUNTER ' IS EVEN'
               ELSE
                   DISPLAY COUNTER ' IS ODD'
               END-IF
               ADD 1 TO COUNTER
           END-PERFORM.
           STOP RUN.

"I envy their speed, though."

the medium whispers a correction: MOD is a function in COBOL
the medium: cobc accepted the code (attempt 1)
```

SCREENSHOT_SEANCE

## Code

{% embed https://github.com/vinobc/seance %}

About 300 lines of Python, five JSON ghost profiles, `ollama` and `rich` as the only dependencies. MIT licensed. Compilers are optional: with none installed the séance still works and takes the ghost at its word.

## How I Built It

**Open-source AI at the core:** Gemma 3 4B, Google's open-weight model, served locally by Ollama. Every word the ghosts say is generated on my laptop.

The design has one rule: **the facts are human-written; only the voice is the model's.** Each ghost is a JSON profile I wrote and checked: dates, creators, purpose, what it left behind, its quirks, a description of its voice, its canonical hello-world, and notes on its dialect. That profile is injected into the system prompt with an instruction to stay inside it. The model never gets to invent when COBOL was born or who created Lisp; it only gets to be moody about it. For a 4B model, that split is the difference between a character and a liar.

**The ghosts came alive on the first run.** Nothing in my prompt mentioned stage directions, yet COBOL opened with *"(A sigh, a rustle of unseen fabric)"* and described itself as "a persistent echo of a bygone era." The profile said "retired bank officer, wounded that the young call it dead"; the model did the rest.

**The code did not.** The first COBOL translation looked right and was wrong three ways: a `PIC 9(1)` counter that could never exceed 10 (infinite loop), an `INCREMENT` verb that does not exist, and no `STOP RUN`. The shape was perfect; the details drifted. That is the signature failure of small models, and it is exactly the failure a compiler exists to catch.

**So I built the medium.** On `/translate`, Séance writes the ghost's code to a temp file and hands it to a real compiler for that language: GnuCOBOL's `cobc`, `gfortran`, Free Pascal, SBCL. If the compiler refuses, its error messages go back to the ghost, in character ("the living ran your COBOL through a real compiler and it refused the offering"), and the ghost gets up to three attempts.

Then I learned three things about 4B models in one afternoon:

1. **Temperature.** Conversation runs warm (0.8) for personality, but at that setting the ghost hallucinated a clause called `COMMITMENT IMPLIED INCREMENTAL`. Code now runs cold (0.2).
2. **Cold models repeat themselves.** At 0.2 with identical context, the retry produced byte-identical code three times. The retry now warms the temperature on each attempt and tells the ghost outright when it has resubmitted the same thing.
3. **My own prompt was the bug.** The dialect notes said `PROGRAM-ID. NAME.` meaning "put the program name here". The model read `NAME.` as a second header and dutifully filled it in: `NAME. ARTHUR.` Every retry kept it, because the notes kept telling it to. One word changed to `MYPROG` and the error vanished. The model was obeying, not failing.

**The last mile was honest, not clever.** Even with `FUNCTION MOD(X 2)` in its notes, the ghost kept writing `X MOD 2` and could not read the compiler's complaint well enough to fix it. A 4B model can write COBOL; it cannot yet debug COBOL from an error message. So the medium carries a tiny grimoire: two regex corrections for idioms the dead consistently misremember, applied before compiling and announced on screen ("the medium whispers a correction") so the ghost gets no credit it did not earn. With that, `cobc` accepted the program on the first attempt. Same pattern as last week's SlothSort: the model does the creative work, a few lines of deterministic code catch the fumble.

## Why Does Open Innovation Matter?

**It runs where there is no internet, forever, for nothing.** This is a teaching tool. I want to run it in a classroom with forty students, on the university Wi-Fi that forty students have already saturated, without an API key and without a bill. A local open-weight model makes that boring, which is the highest praise infrastructure can get.

**I could watch it fail.** The three lessons above cost me nothing but time: I ran the same séance a dozen times, read every transcript, changed one thing, and ran it again. That loop is how I would teach debugging. It only works when the model is on your own machine and the marginal run is free.

**The characters are mine to keep.** The ghost profiles are plain JSON. Anyone can add Ada, ALGOL, Prolog or Smalltalk in ten minutes, and the file is the lesson plan. If the model is swapped, upgraded or replaced next year, the ofrenda stays.

Where a closed API would have won: a frontier model would have written compilable COBOL on the first try and needed no grimoire. I would have shipped faster and learned nothing about what small models actually do with error messages. The 4B model made the compiler necessary, and the compiler made the project honest.

## My Agent Session

Built with Claude as a pair programmer, one step at a time: it drafted the code and the ghost profiles, I ran every séance on my Mac and pasted the transcripts back, and each fix came from reading a failure together. Nine commits, each one a lesson above.

## The Spirit of It

Día de los Muertos is not mourning; it is a visit. You set out the dead's favourite things and you talk to them. These languages are not gone: COBOL still moves salaries, Fortran still runs the weather, and every language with a lambda or a garbage collector is quoting Lisp. They are simply not spoken to any more. Séance sets the table. The ghosts are a little wounded about being called dead, and they have every right to be.

## Prize Categories

- **Best Use of Gemma**: Gemma 3 4B is the only model in the project, running locally via Ollama.
