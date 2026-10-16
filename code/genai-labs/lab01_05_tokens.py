"""Drill 01.5: see text the way the model sees it, as tokens."""
import tiktoken

from llm import get_client, MODEL, PROVIDER

enc = tiktoken.get_encoding("o200k_base")  # tokenizer used by recent OpenAI models

samples = {
    "English": "I was charged an overdraft fee twice. Can you check my account?",
    "Spanish": "Me cobraron dos veces la comisión por descubierto. ¿Pueden revisar mi cuenta?",
    "Hindi": "मुझसे ओवरड्राफ्ट शुल्क दो बार लिया गया। क्या आप मेरा खाता देख सकते हैं?",
    "Japanese": "当座貸越の手数料を2回請求されました。口座を確認していただけますか？",
    "Code": "def interest(balance, apy): return round(balance * apy / 12, 2)",
    "JSON": '{"customer_id": "RR-10293", "card_status": "frozen", "cards": 2}',
    "Amount": "$12,450,309.75",
}

for label, text in samples.items():
    ids = enc.encode(text)
    pieces = [enc.decode([i]) for i in ids]
    print(f"\n{label}: {len(text)} characters -> {len(ids)} tokens")
    print(" | ".join(pieces))

# Ground truth: how many input tokens did the API actually bill?
client = get_client()
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": samples["English"]}],
)
print(f"\nAPI on {PROVIDER} billed {response.usage.prompt_tokens} input tokens for the English sentence")
