"""Claude-powered agent loop for generating experiment hypotheses."""

from __future__ import annotations

import anthropic

from autoresearch.models import ExperimentState
from autoresearch.state import format_results_table

SYSTEM_PROMPT = """\
You are an autonomous experiment runner. Your goal is to improve a metric by \
making focused, incremental changes to the mutable files.

RULES:
- Make ONE focused change per iteration. Small changes are easier to evaluate.
- After each run, analyze results before proposing the next change.
- If a change improved the metric, build on it. If not, try a different direction.
- Removing code for equal results is a great outcome (simplicity wins).
- Never modify read-only files.
- Never stop. Keep iterating until killed.
- Log your reasoning in the description field.
"""


def build_prompt(state: ExperimentState, mutable_contents: dict[str, str]) -> str:
    """Build the prompt for the next iteration."""
    cfg = state.config
    dashboard = format_results_table(state)

    parts = [
        f"## Objective\n{cfg.objective}\n",
        f"## Metric\n{cfg.metric_name} ({cfg.direction.value} is better)",
    ]

    if cfg.metric_unit:
        parts[-1] += f", unit: {cfg.metric_unit}"

    parts.append(f"\n## Verify command\n```bash\n{cfg.verify_command}\n```")

    if state.best_metric is not None:
        parts.append(
            f"\n## Current best\n{cfg.metric_name} = {state.best_metric} (run #{state.best_run})"
        )

    parts.append(f"\n## Results so far\n{dashboard}")

    parts.append("\n## Mutable files (you may edit these)")
    for name, content in mutable_contents.items():
        parts.append(f"\n### {name}\n```\n{content}\n```")

    parts.append(
        "\n## Your task\n"
        "Propose ONE focused change to improve the metric. Return:\n"
        "1. A short description of the change (1 sentence)\n"
        "2. The complete new content of each file you want to modify\n\n"
        "Format your response as:\n"
        "DESCRIPTION: <your description>\n"
        "FILE: <filename>\n"
        "```\n<complete file content>\n```\n"
    )

    return "\n".join(parts)


def get_next_change(
    state: ExperimentState,
    mutable_contents: dict[str, str],
    model: str = "claude-sonnet-4-6",
) -> tuple[str, dict[str, str]]:
    """Ask Claude for the next experiment change.

    Returns (description, {filename: new_content}).
    """
    prompt = build_prompt(state, mutable_contents)
    client = anthropic.Anthropic()

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    return parse_agent_response(text)


def parse_agent_response(text: str) -> tuple[str, dict[str, str]]:
    """Parse the agent's response into description and file changes.

    Expected format:
    DESCRIPTION: <description>
    FILE: <filename>
    ```
    <content>
    ```
    """
    description = ""
    files: dict[str, str] = {}

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("DESCRIPTION:"):
            description = line[len("DESCRIPTION:") :].strip()

        elif line.startswith("FILE:"):
            filename = line[len("FILE:") :].strip()
            # Find the code block
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                i += 1
            i += 1  # Skip opening ```
            content_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                content_lines.append(lines[i])
                i += 1
            files[filename] = "\n".join(content_lines)

        i += 1

    if not description:
        description = "Agent-proposed change"

    return description, files
