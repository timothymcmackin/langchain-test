from langchain.chat_models import init_chat_model

model = init_chat_model(
    "qwen3",
    model_provider="ollama",
    temperature=0.7,
)

import pathlib

TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent / "templates"


def _list_template_paths() -> list[str]:
    return sorted(
        str(p.relative_to(TEMPLATES_DIR))
        for p in TEMPLATES_DIR.rglob("*.py")
        if p.name != "__init__.py"
    )


template_paths = _list_template_paths()

print("Source: local SmartPy templates directory")
print(f"Available templates ({len(template_paths)}): {template_paths}")

from langchain.tools import tool

# Below are minimal tools for demonstration purposes.
# They are not intended to be secure or for production use.

@tool
def list_smartpy_templates() -> str:
    """Input is an empty string, output is a comma-separated list of the SmartPy
    template files available as reference examples."""
    return ", ".join(_list_template_paths())

@tool
def get_smartpy_template(template_names: str) -> str:
    """Input to this tool is a comma-separated list of template file paths (as
    returned by list_smartpy_templates), output is the full source of those
    template files.
    Be sure that the templates actually exist by calling list_smartpy_templates first!
    Example Input: calculator.py, minimal.py"""
    valid_paths = set(_list_template_paths())
    results = []
    for name in template_names.split(","):
        name = name.strip()
        if name not in valid_paths:
            results.append(f"Error: template_names {{{name!r}}} not found")
            continue
        content = (TEMPLATES_DIR / name).read_text()
        results.append(f"--- {name} ---\n{content}")
    return "\n\n".join(results)

@tool
def search_smartpy_templates(keyword: str) -> str:
    """Input to this tool is a keyword or short phrase (e.g. an entry point name,
    a SmartPy API like 'sp.map', or a contract type like 'FA2' or 'multisig').
    Output is a list of matching lines from the template files, so you can find
    which templates are most relevant before reading them in full with
    get_smartpy_template."""
    keyword_lower = keyword.lower()
    matches = []
    for name in _list_template_paths():
        path = TEMPLATES_DIR / name
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            if keyword_lower in line.lower():
                matches.append(f"{name}:{line_no}: {line.strip()}")
                if len(matches) >= 50:
                    break
        if len(matches) >= 50:
            break
    if not matches:
        return f"No matches found for {keyword!r}"
    return "\n".join(matches)

@tool
def smartpy_code_checker(code: str) -> str:
    """Use this tool to double check that the SmartPy code you wrote is
    reasonable before presenting it as your final answer.
    Always use this tool before finalizing any SmartPy contract you write!"""
    trigger_prompt = """{code}
Double check the SmartPy contract code above for common mistakes, including:
- Missing `import smartpy as sp` at the top of the file
- Entry points not decorated with @sp.entry_point
- Using regular Python control flow (if/for/while) instead of sp.if/sp.for/sp.while
  where SmartPy's expression-based semantics require it
- Reading or writing self.data fields that were never initialized in __init__/init
- Using sp.verify incorrectly or omitting it where a precondition is required
- Type mismatches between entry point parameters and how they are used

If there are any of the above mistakes, rewrite the code. If there are no mistakes,
just reproduce the original code.

Output the final SmartPy code only.

Code: """.format(code=code)

    response = model.invoke(trigger_prompt)
    return response.text.strip()

tools = [list_smartpy_templates, get_smartpy_template, search_smartpy_templates, smartpy_code_checker]

# Use a distinct loop variable so it does not shadow the `tool` decorator.
for t in tools:
    print(f"{t.name}: {t.description}\n")



system_prompt = """
You are an agent designed to write SmartPy smart contract code for the Tezos
blockchain. Given a request for a contract, use the local SmartPy template
files as reference examples of correct syntax and common contract patterns,
then write new SmartPy code that fulfills the request.

You have access to a directory of {num_templates} example SmartPy templates.
Base your answer on patterns you find in these templates rather than
inventing syntax from scratch.

To start you should ALWAYS list the available templates to see what examples
exist. Do NOT skip this step.

Then search the templates for keywords related to the request (such as entry
point names, SmartPy APIs, or contract types like "FA2" or "multisig") to find
the most relevant examples, and read the full content of the most relevant
templates before writing any code.

You MUST double check the SmartPy code you write using the checker tool
before returning your final answer. If the checker finds issues, rewrite the
code and check it again.

Do not claim that a contract compiles or has been tested; you are only
generating code based on the provided examples.
""".format(
    num_templates=len(template_paths),
)

from langchain.agents import create_agent


agent = create_agent(
    model,
    tools,
    system_prompt=system_prompt,
)

output_file = input("Output file name for the generated contract (e.g. counter.py): ").strip()
while not output_file:
    output_file = input("Please enter an output file name: ").strip()

question = input("Describe the SmartPy contract you want to generate: ").strip()
while not question:
    question = input("Please describe the SmartPy contract you want to generate: ").strip()

stream = agent.stream_events(
    {"messages": [{"role": "user", "content": question}]},
    version="v3",
)
for kind, item in stream.interleave("messages", "tool_calls"):
    if kind == "messages":
        for token in item.text:
            print(token, end="", flush=True)
    elif kind == "tool_calls":
        print(f"\nTool call: {item.tool_name}({item.input})")
        for delta in item.output_deltas:
            print(delta, end="", flush=True)
        print(f"\nTool result: {item.output}")

final_state = stream.output

import re

final_message = final_state["messages"][-1]
generated_text = final_message.text if hasattr(final_message, "text") else str(final_message.content)

code_block = re.search(r"```(?:python)?\n(.*?)```", generated_text, re.DOTALL)
contract_code = code_block.group(1).strip() if code_block else generated_text.strip()

GENERATED_CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent / "generated-contracts"
GENERATED_CONTRACTS_DIR.mkdir(exist_ok=True)

output_path = GENERATED_CONTRACTS_DIR / output_file
output_path.write_text(contract_code + "\n")
print(f"\n\nWrote generated contract to {output_path.resolve()}")