import Anthropic from "@anthropic-ai/sdk";
import { traceable } from "langsmith/traceable";
import { wrapAnthropic } from "langsmith/wrappers/anthropic";

const client = wrapAnthropic(new Anthropic());

const myTool = traceable(async (question: string) => {
  return "During this morning's meeting, we solved all world conflict.";
}, { name: "Retrieve Context", run_type: "tool" });

const chatPipeline = traceable(async (question: string) => {
  const context = await myTool(question);
  const messages: Anthropic.MessageParam[] = [
      { role: "user", content: `Question: ${question}\nContext: ${context}` }
  ];
  const message = await client.messages.create({
      model: "claude-sonnet-4-6",
      messages: messages,
      max_tokens: 1024,
      system: "You are a helpful assistant. Please respond to the user's request only based on the given context."
  });
  return message;
}, { name: "Chat Pipeline" });

const result = await chatPipeline("Can you summarize this morning's meetings?");
console.log(result);