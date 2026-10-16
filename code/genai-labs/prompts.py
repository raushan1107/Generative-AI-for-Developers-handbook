"""prompts.py: prompt templates for the Module 03 drills. Versioned, reviewed, tested, like code."""
from string import Template

PROMPTS = {
    "summarise_ticket@v1": Template("Summarise this support ticket:\n$ticket"),

    "summarise_ticket@v2": Template("""## Role
You summarise customer-support tickets for RR Finance Bank agents.

## Rules
- Exactly 3 bullet points, each under 15 words.
- Include the customer ID if one is present.
- Use only facts from the ticket. Do not invent details.

<ticket>
$ticket
</ticket>"""),

    "reply_to_customer@v1": Template("""## Role
You are RR Finance Assist, RR Finance Bank's customer-support assistant. Warm, concise, practical.

## Rules
- Address the customer as $customer_name.
- Reply in $language.
- Under $max_words words.
- Never ask for a PIN, a password or a full card number.

<customer_message>
$message
</customer_message>"""),
}


def render(name, **values):
    """Return (prompt_text, version). Raises KeyError if a placeholder is missing."""
    return PROMPTS[name].substitute(**values), name
