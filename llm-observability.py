import openai
from langsmith.wrappers import wrap_openai
from langsmith import traceable

# client = wrap_openai(OpenAI())
client = wrap_openai(openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"))

docs = [
    "Acme Cloud supports unlimited users on Enterprise plans. Starter plans are limited to 5 users.",
    "To reset your password, click 'Forgot password' on the login page and follow the instructions sent to your email.",
    "API rate limits are 1,000 requests per hour on the Starter plan and 10,000 requests per hour on Enterprise.",
]

def retriever(query: str) -> list[str]:
    return docs

@traceable(name="Support bot")
def support_bot(question: str) -> str:
    context = retriever(question)
    system_message = (
        "You are a helpful customer support agent. "
        "Answer using only the information provided below:\n\n"
        + "\n".join(context)
    )
    response = client.chat.completions.create(
        # model="gpt-5.4-mini",
        model="qwen3",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print(support_bot("How many users can I have on the Starter plan?"))