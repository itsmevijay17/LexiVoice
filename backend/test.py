from groq import Groq
import os

print("Groq module path:", Groq.__module__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()
    print("✅ Connection successful!")
    for model in models.data[:5]:
        print("-", model.id)
except Exception as e:
    print("❌ Error:", e)
