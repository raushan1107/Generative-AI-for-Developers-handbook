"""Lab 1, Exercise 2: tokens and temperature.
Part A counts tokens for different texts (tiktoken's o200k_base encoding, offline; open models use
their own tokenizers, so treat these as estimates). Part B asks the same question three times at
temperature 0 and three times at 1.2."""
import tiktoken

from client import CHAT_MODEL, get_client

enc = tiktoken.get_encoding("o200k_base")
TEXTS = {
    "English": "Can I get my overdraft fee refunded?",
    "Spanish": "¿Pueden devolverme la comisión por descubierto?",
    "Hindi": "क्या मुझे मेरा ओवरड्राफ्ट शुल्क वापस मिल सकता है?",
    "Code": "def add(a, b):\n    return a + b",
    "IDs and amounts": "RR-10477 card 4821 $12,450.75",
}
print("A. TOKENS (estimate)")
for name, text in TEXTS.items():
    print(f"  {name:15} {len(text):3} characters -> {len(enc.encode(text)):3} tokens")

print("\nB. TEMPERATURE")
client = get_client()
question = "Suggest a name for a savings account for first-time savers. Reply with the name only."
for temperature in (0, 1.2):
    names = [client.chat.completions.create(model=CHAT_MODEL, temperature=temperature, messages=[
        {"role": "user", "content": question}]).choices[0].message.content.strip() for _ in range(3)]
    print(f"  temperature {temperature}: {names}")
