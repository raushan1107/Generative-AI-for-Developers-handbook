"""prompts.py: prompt templates for the Module 03 drills. Versioned, reviewed, tested, like code."""
from string import Template

PROMPTS = {
    "summarise_ticket@v1": Template("Summarise this support ticket:\n$ticket"),

    "summarise_ticket@v2": Template("""## Role
You summarise learner-support tickets for TrainCrest agents.

## Rules
- Exactly 3 bullet points, each under 15 words.
- Include the enrolment ID if one is present.
- Use only facts from the ticket. Do not invent details.

<ticket>
$ticket
</ticket>"""),

    "reply_to_learner@v1": Template("""## Role
You are Traincrest Assist, TrainCrest's learner-support assistant. Warm, concise, practical.

## Rules
- Address the learner as $learner_name.
- Reply in $language.
- Under $max_words words.

<learner_message>
$message
</learner_message>"""),
}


def render(name, **values):
    """Return (prompt_text, version). Raises KeyError if a placeholder is missing."""
    return PROMPTS[name].substitute(**values), name
