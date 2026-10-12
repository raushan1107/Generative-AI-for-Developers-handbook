"""Drill 01.5: see text the way the model sees it, as tokens."""
import tiktoken

from llm import get_client, MODEL, PROVIDER

enc = tiktoken.get_encoding("o200k_base")  # tokenizer used by recent OpenAI models

samples = {
    "English": "My exam voucher hasn't arrived yet. Can you check my enrolment?",
    "Spanish": "Mi cupón de examen aún no ha llegado. ¿Pueden revisar mi inscripción?",
    "Hindi": "मेरा परीक्षा वाउचर अभी तक नहीं आया है। क्या आप मेरा नामांकन देख सकते हैं?",
    "Japanese": "試験バウチャーがまだ届いていません。登録を確認していただけますか？",
    "Code": "def total(items): return sum(i.price * i.qty for i in items)",
    "JSON": '{"enrolment_id": "TC-10293", "status": "confirmed", "seats": 2}',
    "Number": "3.14159265358979",
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
