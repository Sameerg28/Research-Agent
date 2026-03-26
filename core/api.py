import json
import re


def extract_json(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response:\n{raw[:300]}")


def chunk_text(text: str, chunk_size: int) -> list[str]:
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    for index in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[index : index + chunk_size]))
    return chunks


def merge_chunk_results(chunks_data: list[dict]) -> dict:
    if len(chunks_data) == 1:
        return chunks_data[0]

    merged = chunks_data[0].copy()
    application = merged.setdefault("application_to_erisia", {})

    all_takeaways: list[str] = []
    all_experiments: list[str] = []
    all_ideas: list[dict] = []

    for chunk_data in chunks_data:
        app = chunk_data.get("application_to_erisia", {})
        all_takeaways.extend(app.get("key_takeaways", []))
        all_experiments.extend(app.get("experiment_suggestions", []))
        all_ideas.extend(app.get("implementation_ideas", []))

    application["key_takeaways"] = list(dict.fromkeys(all_takeaways))[:6]
    application["experiment_suggestions"] = list(dict.fromkeys(all_experiments))[:4]
    application["implementation_ideas"] = all_ideas[:5]

    return merged


def paper_chunk_prompts(user_prompt: str, chunk_size: int) -> list[str]:
    prefix = "Analyze this research paper:\n\n"
    paper_body = user_prompt[len(prefix) :] if user_prompt.startswith(prefix) else user_prompt
    chunks = chunk_text(paper_body.strip(), chunk_size)
    if len(chunks) == 1:
        return [user_prompt]

    return [
        f"Analyze PART {index + 1}/{len(chunks)} of this research paper:\n\n{chunk}"
        for index, chunk in enumerate(chunks)
    ]
