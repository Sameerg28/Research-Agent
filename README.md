# Deep Research System

Modular paper-analysis and deep-research agent designed for loose coupling and later integration into larger systems.

## Architecture

- `interfaces/` defines the contracts for memory, LLM, search, and tools.
- `implementations/` contains the concrete backends, including Groq and OpenAlex.
- `intelligence/` orchestrates extraction, evaluation, convergence, and synthesis.
- `memory/working.py` is now a wrapper over a swappable memory backend instead of a hardcoded store.
- `agent.py` is the composition root: it creates implementations, injects them, and keeps the CLI behavior intact.

## Folder Structure

```text
ResearchSystem/
|-- agent.py
|-- config.py
|-- core/
|   |-- api.py
|   |-- voice.py
|   |-- renderer.py
|   `-- logger.py
|-- interfaces/
|   |-- llm.py
|   |-- memory.py
|   |-- search.py
|   `-- tool.py
|-- implementations/
|   |-- llm/
|   |   `-- groq_llm.py
|   |-- memory/
|   |   `-- simple_memory.py
|   |-- search/
|   |   `-- openalex_search.py
|   `-- tool/
|       `-- groq_voice_transcriber.py
|-- cognition/
|   |-- decision.py
|   `-- modes.py
|-- intelligence/
|   |-- evaluator.py
|   |-- expander.py
|   |-- extractor.py
|   `-- researcher.py
|-- memory/
|   |-- episodic.py
|   |-- semantic.py
|   `-- working.py
|-- tools/
|   |-- file_handler.py
|   |-- llm.py
|   `-- web.py
|-- feedback/
|   |-- correction.py
|   `-- validator.py
|-- state/
|   |-- state.py
|   `-- tracker.py
|-- context/
|   `-- erisia.txt
|-- inputs/
|   |-- pdfs/
|   `-- text/
`-- outputs/
    `-- reports/
```

## Usage

```bash
python agent.py --input inputs/pdfs/paper.pdf
python agent.py --input inputs/pdfs/paper.pdf --breadth 4 --depth 2
python agent.py --input inputs/pdfs/paper.pdf --no-web
python agent.py --input inputs/pdfs/paper.pdf --save
```

`--paper` is still accepted as an alias for `--input`.
