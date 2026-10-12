"""Lab 1, Exercise 2: tokens and temperature.
Part A counts tokens for different texts (tiktoken's o200k_base encoding, offline; open models use
their own tokenizers, so treat these as estimates). Part B asks the same question three times at
temperature 0 and three times at 1.2."""
import tiktoken

from client import CHAT_MODEL, get_client

enc = tiktoken.get_encoding("o200k_base")
TEXTS = {
    "English": "Can I reschedule my course to next month?",
    "Spanish": "¿Puedo cambiar mi curso al mes que viene?",
    "Hindi": "क्या मैं अपना कोर्स अगले महीने कर सकता हूँ?",
    "Code": "def add(a, b):\n    return a + b",
    "Error code": "LAB-503 TC-10477 AZ-104",
}
print("A. TOKENS (estimate)")
for name, text in TEXTS.items():
    print(f"  {name:10} {len(text):3} characters -> {len(enc.encode(text)):3} tokens")

print("\nB. TEMPERATURE")
client = get_client()
question = "Suggest a name for a coffee shop run by programmers. Reply with the name only."
for temperature in (0, 1.2):
    names = [client.chat.completions.create(model=CHAT_MODEL, temperature=temperature, messages=[
        {"role": "user", "content": question}]).choices[0].message.content.strip() for _ in range(3)]
    print(f"  temperature {temperature}: {names}")
