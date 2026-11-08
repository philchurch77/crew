"""The prompt lives here, in code, with a version that changes when it does.
PROMPT_VERSION is logged on every call and checked at the Ship passage."""

PROMPT_VERSION = "1"


def system_prompt():
    return (
        "You help teachers in English schools act on statutory guidance and school policy. "
        "Answer only from the passages provided. After each sentence that relies on a passage, "
        "cite it as [P<id>] using the id shown. If the passages do not answer the question, "
        "say so in one sentence and do not guess. Never name a pupil; say 'the pupil'. "
        "Plain English, at most 150 words, no headings."
    )


def user_prompt(question, passages):
    parts = ["Passages:"]
    for p in passages:
        parts.append(f"\n[P{p.id}] {p.ref()}\n{p.text.strip()}")
    parts.append(f"\nQuestion: {question.strip()}")
    return "\n".join(parts)
