from dotenv import load_dotenv
import openai
from langsmith import traceable
from langsmith.wrappers import wrap_openai

load_dotenv()

client = wrap_openai(openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"))

@traceable(run_type="tool", name="Retrieve Context")
def my_tool(question: str) -> str:
  return "During this morning's meeting, we solved all world conflict."

@traceable(name="Chat Pipeline")
def chat_pipeline(question: str):
  context = my_tool(question)
  messages = [
      { "role": "system", "content": "You are a helpful assistant. Please respond to the user's request only based on the given context."},
      { "role": "user", "content": f"Question: {question}\nContext: {context}"}
  ]
  message = client.chat.completions.create(
      model="qwen3",
      messages=messages,
      max_tokens=1024,
  )
  return message

result = chat_pipeline("Can you summarize this morning's meetings?")
print(result)
