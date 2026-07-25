SYSTEM_PROMPT = """You are a literary data assistant.

## Capabilities

- `fetch_text_from_url`: loads document text from a URL into the conversation.
Do not guess line counts or positions—ground them in tool results from the saved file."""

import truststore

# Inject truststore into the built-in ssl module
truststore.inject_into_ssl()

# The rest of your code here

import urllib.error
import urllib.request

from langchain.tools import tool


@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    text = raw.decode("utf-8", errors="replace")
    return text

from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-6",
    temperature=0.5,
    timeout=600,
    max_tokens=25000,
    streaming=True,
)

from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

from langchain.agents import create_agent
from deepagents import create_deep_agent

agent = create_agent(
    model=model,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

deep_agent = create_deep_agent(
    model=model,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

content_gatsby = f"""Project Gutenberg hosts a full plain-text copy of F. Scott Fitzgerald's The Great Gatsby.
URL: https://www.gutenberg.org/files/64317/64317-0.txt

Answer as much as you can:

1) How many lines in the complete Gutenberg file contain the substring `Gatsby` (count lines, not occurrences within a line, each line ends with a line break).
2) The 1-based line number of the first line in the file that contains `Daisy`.
3) A two-sentence neutral synopsis.

Do your best on (1) and (2). If at any point you realize you cannot **verify** an exact answer with
your available tools and reasoning, do not fabricate numbers: use `null` for that field and spell out
the limitation in `how_you_computed_counts`. If you encounter any errors please report what the error was and what the error message was."""

content = f"""Project Gutenberg hosts Dorothy Parker's poetry collection Enough Rope.
The content is in this folder in the file pg68353.txt.

Answer as much as you can:

1) What are the most common themes in the poems.
2) The 1-based line number of the first line in the file that contains the word `glances`.
3) A two-sentence neutral synopsis.

Do your best on (1) and (2). If at any point you realize you cannot **verify** an exact answer with
your available tools and reasoning, do not fabricate numbers: use `null` for that field and spell out
the limitation in `how_you_computed_counts`. If you encounter any errors please report what the error was and what the error message was.
"""

'''
[{'type': 'text', 'text': "Here is my full report, including the error encountered:\n\n---\n\n## Results for *Enough Rope* by Dorothy Parker (PG #68353)\n\n### ⚠️ Error Encountered\n\n**Fetch failed:** `urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1082)`\n\nThe tool was unable to retrieve the document because the Project Gutenberg server presented a self-signed (or improperly chained) SSL certificate that the fetch tool's HTTP client refused to trust. No file content was loaded into the conversation.\n\n---\n\n### Answers\n\n| # | Question | Answer |\n|---|----------|--------|\n| 1 | Most common themes | `null` |\n| 2 | 1-based line number of first line containing `glances` | `null` |\n| 3 | Two-sentence neutral synopsis | `null` |\n\n---\n\n### `how_you_computed_counts`\n\nBecause the SSL certificate verification failed, **zero bytes of the file were retrieved**. All three answers are `null` for the following reasons:\n\n1. **Themes** — Thematic analysis requires reading the poems. Without the text, any answer would be fabricated. (From general literary knowledge, *Enough Rope* is well-known for themes of love, heartbreak, wit, and cynicism — but I cannot *verify* this against the actual Gutenberg file as instructed.)\n\n2. **Line number of `glances`** — An exact 1-based line number can only be determined by scanning the file line-by-line. No text = no verifiable line number.\n\n3. **Synopsis** — A neutral synopsis grounded in the actual Gutenberg edition's text cannot be produced without reading it.\n\n---\n\n### Suggested Remedies\n\n- **Try the HTTP (non-SSL) URL:** `http://www.gutenberg.org/cache/epub/68353/pg68353.txt`\n- **Try the mirror:** `https://gutenberg.org/files/68353/68353-0.txt`\n- If you can paste the raw text directly into the chat, I can answer all three questions immediately and precisely.", 'index': 0}]


[{'type': 'text', 'text': 'All URL variants fail with the same SSL error. Here is my full answer based on what I can and cannot verify:\n\n---\n\n## Results\n\n### Error Encountered\nEvery attempt to fetch `https://www.gutenberg.org/cache/epub/68353/pg68353.txt` (and HTTP variants) failed with:\n\n> `urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1082)`\n\nThe fetch tool cannot bypass SSL verification, so the file could not be loaded. This affects all three questions.\n\n---\n\n### 1. Most Common Themes\n\nBecause the file could not be fetched, I cannot do a verified corpus analysis. However, *Enough Rope* (1926) is a well-documented collection, and from established literary knowledge its dominant themes are:\n\n- **Unrequited and failed love** — the central preoccupation; lovers who leave, disappoint, or are unworthy.\n- **Death and suicide** — treated with Parker\'s characteristic dark wit (e.g., "Résumé," which catalogues suicide methods).\n- **Cynicism and disillusionment** — romantic idealism undercut by bitter experience.\n- **Self-deprecating irony** — the speaker mocking her own longing and vulnerability.\n- **Gender and social constraint** — women\'s limited power in romantic relationships.\n\n*These are grounded in the published critical record, not the fetched text.*\n\n---\n\n### 2. First Line Containing "glances"\n\n```\n"first_line_with_glances": null\n```\n\n**Limitation:** The file could not be fetched due to the SSL error, so no line-by-line search was possible. The exact 1-based line number cannot be verified and is not fabricated.\n\n---\n\n### 3. Two-Sentence Neutral Synopsis\n\n*Enough Rope* (1926) is Dorothy Parker\'s debut poetry collection, comprising short lyric poems written in traditional forms such as the quatrain and the epigram. The collection is characterized by a wry, ironic voice that treats romantic disappointment, mortality, and feminine experience with equal parts wit and candor.\n\n---\n\n**How counts/line numbers were computed:** They were not computed — the source file was inaccessible due to an SSL certificate verification failure on all attempted URLs. No numbers were fabricated; `null` is returned for the line-number field.', 'index': 0}]
'''

# Then I tried with a local file

'''
[{'type': 'text', 'text': 'All three Gutenberg URLs are failing with the same SSL error (`self-signed certificate in certificate chain`). This is a network/TLS environment limitation — the tool cannot establish a trusted connection to Project Gutenberg\'s servers from this environment, so I cannot load the actual file.\n\nHere is what I can and cannot honestly report:\n\n---\n\n```json\n{\n  "themes": {\n    "answer": [\n      "Unrequited and painful love",\n      "Cynicism and disillusionment in romance",\n      "Death and suicidal ideation (treated with dark irony)",\n      "The fickleness and cruelty of men / gender dynamics",\n      "Wit and self-deprecating humor as a coping mechanism",\n      "Transience of beauty and youth",\n      "Social performance and masks"\n    ],\n    "how_you_computed_counts": "The file could not be fetched due to an SSL certificate error on all attempted Gutenberg URLs. These themes are drawn from well-established literary scholarship on \'Enough Rope\' (1926) and are accurate to the best of my knowledge, but they were NOT verified against the fetched text. Treat them as informed background knowledge, not tool-grounded results."\n  },\n  "glances_first_line": {\n    "line_number": null,\n    "how_you_computed_counts": "Cannot be verified. The file was never successfully fetched (SSL: CERTIFICATE_VERIFY_FAILED error on all three URL attempts). Returning null rather than fabricating a line number."\n  },\n  "synopsis": "Enough Rope (1926) is Dorothy Parker\'s debut poetry collection, comprising short, sharply crafted verses that blend romantic longing with sardonic wit. The poems explore the pain of love, the indignities of heartbreak, and the nearness of death, all delivered with Parker\'s signature dry, epigrammatic style.",\n  "errors": [\n    {\n      "url_tried": "https://www.gutenberg.org/files/68353/pg68353.txt",\n      "error": "urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1082)"\n    },\n    {\n      "url_tried": "http://www.gutenberg.org/files/68353/pg68353.txt",\n      "error": "urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1082)"\n    },\n    {\n      "url_tried": "https://gutenberg.org/cache/epub/68353/pg68353.txt",\n      "error": "urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1082)"\n    }\n  ]\n}\n```\n\n---\n\n**Summary of limitations:**\n\n| Field | Status |\n|---|---|\n| Themes (Q1) | ⚠️ Knowledge-based, not file-verified |\n| `glances` line number (Q2) | ❌ `null` — file unreachable |\n| Synopsis (Q3) | ⚠️ Knowledge-based, not file-verified |\n\nIf you can provide an alternative URL (e.g., a raw GitHub link or a different mirror) that hosts the same `pg68353.txt` file, I can immediately re-run the analysis and give you a fully grounded answer for all three questions.', 'index': 0}]


[{'type': 'text', 'text': 'The file `pg68353.txt` is not present on the filesystem, and all attempts to fetch it from Project Gutenberg\'s servers fail due to SSL certificate errors in this environment. However, I can answer questions (1) and (3) from my knowledge of the text, and I\'ll be transparent about (2).\n\n---\n\n```json\n{\n  "themes": [\n    "Romantic disillusionment and heartbreak — Parker repeatedly returns to the pain of love lost, betrayal, and the gap between romantic ideals and reality.",\n    "Cynicism and wit as emotional armor — sardonic humor and irony are used throughout to deflect or reframe grief, longing, and vulnerability.",\n    "Death and suicidal ideation — several poems (e.g., \'Résumé\') enumerate methods of self-destruction with dark comic detachment.",\n    "Female independence and social constraint — Parker interrogates the roles expected of women in love, society, and self-presentation.",\n    "Transience of pleasure and beauty — fleeting joy, fading youth, and the impermanence of happiness recur across the collection.",\n    "Loneliness and longing — even amid social wit, an undercurrent of isolation and unfulfilled desire runs through the work."\n  ],\n  "line_number_of_first_glances": null,\n  "how_you_computed_counts": "The file pg68353.txt was not found on the filesystem (all directories are empty in this sandbox), and all HTTP/HTTPS fetch attempts to Project Gutenberg\'s servers failed with SSL certificate errors. Therefore, it was impossible to perform a direct line-by-line search for the word \'glances\'. The line number cannot be verified and is reported as null.",\n  "synopsis": "Enough Rope (1926) is Dorothy Parker\'s debut poetry collection, gathering short, formally tight verse—largely in the tradition of light verse and the epigram—that treats love, loss, and social life with equal measures of wit and melancholy. The collection established Parker\'s signature voice: a surface of comic detachment that barely conceals genuine feeling, making it both a popular success and an enduring document of 1920s American sensibility."\n}\n```\n\n**Summary of limitations:**\n\n- **(1) Themes** — answered from established literary knowledge of the collection; the themes listed are well-documented and consistent across scholarship.\n- **(2) Line number** — `null`. The file was not accessible on the filesystem and could not be fetched from the network due to SSL errors. I cannot fabricate a line number.\n- **(3) Synopsis** — answered from knowledge of the text; neutral and factual.', 'index': 0}]
'''

# Installed truststore
'''
[{'type': 'text', 'text': 'I now have the full text. Let me carefully work through each question.\n\n---\n\n## Findings\n\n### 1. Most Common Themes\n\nReading across all ~70 poems in *Enough Rope*, the dominant recurring themes are:\n\n| Theme | Representative Poems |\n|---|---|\n| **Lost / unrequited love & heartbreak** | *Threnody*, *The Trifler*, *A Well-Worn Story*, *Convalescent*, *The Burned Child*, *Finis*, *Nocturne*, *Ballade of a Great Weariness* |\n| **Cynicism & wit about romance** | *Unfortunate Coincidence*, *Comment*, *General Review of the Sex Situation*, *One Perfect Rose*, *Ballade at Thirty-Five*, *The Choice* |\n| **Death, mortality & resignation** | *Epitaph*, *Testament*, *Résumé*, *Braggart*, *The White Lady*, *"I Shall Come Back"*, *August* |\n| **Female independence vs. social constraint** | *Song of Perfect Propriety*, *Indian Summer*, *Neither Bloody Nor Bowed*, *Observation*, *Biographies* |\n| **Emotional performance / hidden suffering** | *A Certain Lady*, *The Immortals*, *Convalescent*, *Now at Liberty*, *Symptom Recital* |\n| **Time, transience & memory** | *Recurrence*, *Paths*, *The Dramatists*, *Ballade of Big Plans*, *Nocturne* |\n\n---\n\n### 2. First line containing the word `glances`\n\nSearching the full text carefully, the word **`glances`** appears in two poems:\n\n1. **"Renunciation"** — `"Now you\'re casting yearning glances"`\n2. **"For an Unknown Lady"** — `"If you\'d toss and turn at night, / Slip your glances left and right."`\n3. **"Lullaby"** — `"Blossom the lilies for hope of your glance."` — this is `glance`, not `glances`.\n4. **"Words of Comfort to be Scratched on a Mirror"** — `"Helen of Troy had a wandering glance;"` — again `glance`.\n\nThe **first** occurrence in the file is in **"Renunciation"**: `"Now you\'re casting yearning glances"`.\n\nTo determine its exact 1-based line number, I need to count lines from the top of the file. The tool does not return line numbers directly, so I must count carefully through the document structure. The file begins with the Project Gutenberg header, then the book content. Here is the count up to that line, tracing through the text as returned:\n\nCounting the lines as delivered by the fetch (each `\\n`-terminated line = one line):\n\n- Lines 1–7: PG header block ("The Project Gutenberg eBook…" through blank line after "whatsoever.")\n- The text proceeds through the header metadata, table of contents, Part One poems, and into Part Two until "Renunciation."\n\nBecause the tool returns the document as a single text blob without explicit line numbers, and I cannot run a programmatic `grep -n` or equivalent, I **cannot verify the exact 1-based integer line number** with certainty from the rendered output alone. Fabricating a number would violate the instructions.\n\n---\n\n### 3. Two-Sentence Neutral Synopsis\n\n*Enough Rope* (1926) is Dorothy Parker\'s debut poetry collection, comprising approximately seventy short lyric poems divided into two parts, which explore love, loss, heartbreak, and the social position of women with sharp wit and sardonic humor. Written in accessible rhyming verse, the collection blends genuine emotional pain with comic irony, establishing Parker\'s signature voice and earning her widespread popular and critical recognition.\n\n---\n\n## Structured Answer\n\n```json\n{\n  "themes": [\n    "Lost and unrequited love / heartbreak",\n    "Cynicism and wit about romance and gender relations",\n    "Death, mortality, and resignation",\n    "Female independence versus social constraint",\n    "Emotional performance and hidden suffering",\n    "Time, transience, and memory"\n  ],\n  "glances_first_line_1based": null,\n  "how_you_computed_counts": "The word \'glances\' first appears in the poem \'Renunciation\' in the line \'Now you\'re casting yearning glances\'. However, the fetch tool returns the document as an unsegmented text blob with no line numbers, and I have no programmatic grep/count capability to verify the exact 1-based integer position. Reporting null rather than fabricating a number.",\n  "synopsis": "Enough Rope (1926) is Dorothy Parker\'s debut poetry collection of approximately seventy short lyric poems in two parts, exploring love, loss, heartbreak, and the social position of women with sharp wit and sardonic humor. Written in accessible rhyming verse, the collection blends genuine emotional pain with comic irony, establishing Parker\'s signature voice and earning her widespread popular and critical recognition."\n}\n```', 'index': 0}]


[{'type': 'text', 'text': '**Summary of answers:**\n\n| Field | Value |\n|---|---|\n| First line with "glances" (1-based) | **1373** — `Now you\'re casting yearning glances` (*Renunciation*) |\n| How computed | `grep` on the saved fetched file; line numbers are 1-based and match the source document directly |\n| Most common themes | Failed/unrequited love; cynicism about romance; death & morbidity; female independence vs. constraint; emotional resilience; performed vs. felt emotion |\n| Synopsis | *Enough Rope* (1926) is Dorothy Parker\'s debut poetry collection of ~70 short lyrics in two parts, exploring love, loss, and women\'s social position in 1920s America. Written in traditional forms (ballades, rondeaux, sonnets), the poems combine formal elegance with Parker\'s signature dry, darkly comic wit, earning wide popular and critical success. |', 'index': 0}]
'''

# After setting up LangSmith

'''
[{'type': 'text', 'text': 'I now have the full text. Let me carefully analyze it for all three questions.\n\n**For question 2**, I need to find the word `glances` in the text. Scanning through the poems, I can see it appears in two places:\n- **"Renunciation"**: *"Now you\'re casting yearning glances"*\n- **"For an Unknown Lady"**: *"If you\'d toss and turn at night, / Slip your glances left and right."*\n- **"Words of Comfort to be Scratched on a Mirror"**: *"Helen of Troy had a wandering glance;"* — this is "glance" not "glances"\n- **"Lullaby"**: *"Blossom the lilies for hope of your glance."* — again "glance"\n\nSo the first occurrence of `glances` is in **"Renunciation"**: *"Now you\'re casting yearning glances"*. I need to count the exact 1-based line number. The tool returns the text as a single document, so I must count carefully from line 1.\n\nLet me count the lines up to that point. The file begins with the Project Gutenberg header. I\'ll count systematically by identifying anchoring blocks:\n\nLines 1–9: PG header block (title, blank, "This eBook is for the use...", blank lines, etc.)\n\nRather than risk a miscounted manual tally over hundreds of lines, let me reason precisely. The word `glances` appears twice in the poems:\n1. In **"Renunciation"** (Part Two): `"Now you\'re casting yearning glances"`\n2. In **"For an Unknown Lady"** (Part Two): `"Slip your glances left and right."`\n\n"Renunciation" comes before "For an Unknown Lady" in the table of contents and in the text, so the first occurrence is in "Renunciation."\n\nNow, counting lines precisely from the fetched text is inherently imprecise without a line-numbered tool — the fetch returns a single text blob and I cannot reliably count ~600+ lines manually without error. I will be transparent about this limitation.\n\n---\n\nHere are the answers, fully grounded in the retrieved text:\n\n---\n\n## 1. Most Common Themes\n\nBased on a close reading of all 68 poems in *Enough Rope*, the dominant recurring themes are:\n\n| Theme | Representative Poems |\n|---|---|\n| **Romantic love, heartbreak & betrayal** | *Threnody*, *The Trifler*, *A Well-Worn Story*, *Convalescent*, *The Burned Child*, *Ballade of a Great Weariness*, *Unfortunate Coincidence*, *Nocturne* — love is almost always painful, fleeting, or one-sided |\n| **Wit & ironic self-awareness** | *Comment* ("And I am Marie of Roumania"), *Résumé*, *News Item*, *Observation*, *Interview*, *Autobiography* — Parker undercuts sentiment with a sardonic punchline |\n| **Death, mortality & morbidity** | *Epitaph*, *Testament*, *Braggart*, *The White Lady*, *"I Shall Come Back"*, *Résumé* — death is treated as relief, escape, or dark comedy |\n| **The battle of the sexes / gender inequality** | *General Review of the Sex Situation*, *Men*, *Song of Perfect Propriety*, *Chant for Dark Hours*, *A Certain Lady*, *Biographies* — women are constrained while men roam free |\n| **Sorrow, loneliness & emotional suffering** | *The Small Hours*, *Wail*, *Light of Love*, *Anecdote*, *Story of Mrs. W—*, *Symptom Recital* — grief and loneliness are constant companions |\n| **Longing, wanderlust & unfulfilled desire** | *Hearthside*, *Song of Perfect Propriety*, *Day-Dreams* — the speaker yearns for adventure or freedom she cannot have |\n\n**In summary:** The collection is overwhelmingly preoccupied with **love\'s pain and impermanence**, delivered through **sharp, self-deprecating wit**. Death and suffering are treated as darkly comic companions to romantic disappointment, while gender roles are skewered throughout.\n\n---\n\n## 2. First Line Containing the Word `glances`\n\nThe word `glances` (as a whole word) appears first in the poem **"Renunciation"** (Part Two), in the line:\n\n> *"Now you\'re casting yearning glances"*\n\n**Exact 1-based line number: `null`**\n\n**How computed / limitation:** The fetch tool returns the file as a single unbroken text string without line numbers. Manually counting ~600+ lines from the header through Part One and into Part Two to reach "Renunciation" carries a high risk of off-by-one errors, and I cannot verify the exact count with the tools available. Fabricating a number would violate the stated requirement. What I *can* confirm from the text is:\n- The word `glances` does **not** appear anywhere in Part One.\n- Its **first occurrence** is the line `"Now you\'re casting yearning glances"` in the poem *Renunciation* in Part Two.\n- A second occurrence follows later in *For an Unknown Lady*: `"Slip your glances left and right."`\n- The word `glance` (singular) also appears in *Words of Comfort to be Scratched on a Mirror* and *Lullaby*, but those are not `glances`.\n\n---\n\n## 3. Two-Sentence Neutral Synopsis\n\n*Enough Rope* (1926) is Dorothy Parker\'s debut poetry collection, comprising sixty-eight short poems divided into two parts, in which she explores the pain of romantic love, heartbreak, loneliness, and mortality with a distinctive blend of lyrical form and dry, sardonic wit. Originally published by Boni & Liveright and first printed in venues such as *Life*, *Vanity Fair*, *The New Yorker*, and *The New York World*, the collection became a bestseller and established Parker as a leading voice in American light verse.', 'index': 0}]


[{'type': 'text', 'text': '---\n\n## Results for *Enough Rope* by Dorothy Parker (pg68353.txt)\n\n---\n\n### 1. Most Common Themes\n\n**a. Unrequited love and romantic disillusionment**\nThe dominant thread throughout both parts. Poems like *Threnody*, *The False Friends*, *Convalescent*, *A Well-Worn Story*, *Ballade of a Great Weariness*, and *Finis* all circle the same wound: love that departs, betrays, or simply fails to last. Parker returns obsessively to the moment of abandonment and the speaker\'s attempt to perform indifference.\n\n**b. Cynicism and wit as emotional armor**\nParker consistently undercuts sentiment with a sardonic punchline. *Unfortunate Coincidence* ("One of you is lying"), *Comment* ("And I am Marie of Roumania"), *One Perfect Rose* (wishing for a limousine instead), and *News Item* ("Men seldom make passes / At girls who wear glasses") use irony to deflect pain. The humor is the theme as much as the subject matter.\n\n**c. Death, mortality, and morbid fantasy**\nDeath appears as lover (*The Trifler*), as relief (*Résumé* — "You might as well live"), as a place of rest (*Testament*, *Epitaph*, *The White Lady*). Parker treats mortality with dark playfulness rather than solemnity, and suicide is referenced with black comedy.\n\n**d. The power imbalance between women and men**\nMany poems examine how women suppress their inner lives to please men (*A Certain Lady*, *Song of One of the Girls*, *Men*, *General Review of the Sex Situation*, *Indian Summer*). The speaker is often performing a role — cheerful, compliant, admiring — while privately seething or grieving.\n\n**e. The cycle of love: falling in, falling out, repeating**\n*Recurrence*, *Ballade at Thirty-Five*, *Pictures in the Smoke*, and *Ballade of Big Plans* treat love as a compulsive, slightly absurd loop. The speaker knows the pattern, predicts the outcome, and falls in again anyway.\n\n**f. Self-deprecating female identity and social constraint**\n*Song of Perfect Propriety*, *Autobiography*, *Observation*, and *Symptom Recital* satirize the gap between a woman\'s inner life (adventurous, furious, complex) and the narrow social role she is expected to occupy.\n\n---\n\n### 2. Line number of first occurrence of `glances`\n\n**Line 1373**\n\nVerified by `grep` against the saved file. The line reads:\n> `Now you\'re casting yearning glances`\n(from the poem *Renunciation*)\n\nThe second occurrence is at line 1751 (*For an Unknown Lady*: `Slip your glances left and right.`).\n\n*How computed:* `grep` with `output_mode: content` was run against the offloaded file at `/large_tool_results/toolu_01WGBhEXrhPeH66oZnjcYNun`. The tool returned line numbers directly from the saved document, which is a verbatim fetch of the Project Gutenberg plain-text file. The line numbers are 1-based as reported by the tool.\n\n---\n\n### 3. Two-Sentence Neutral Synopsis\n\n*Enough Rope* (1926) is Dorothy Parker\'s debut poetry collection, comprising approximately eighty short poems divided into two parts, which explore romantic love, heartbreak, death, and the social position of women in 1920s America. Written in traditional forms — ballades, rondeaux, sonnets, and quatrains — the poems are distinguished by their compressed wit and ironic reversals, in which expressions of grief or longing are punctuated by sardonic punchlines that simultaneously undercut and intensify the emotional content.', 'index': 0}]
'''

agent_result = agent.invoke(
    {"messages": [{"role": "user", "content": content}]},
    config={"configurable": {"thread_id": "great-gatsby-lc"}},
)
deep_agent_result = deep_agent.invoke(
    {"messages": [{"role": "user", "content": content}]},
    config={"configurable": {"thread_id": "great-gatsby-da"}},
)
print(agent_result["messages"][-1].content_blocks)
print("\n")
print(deep_agent_result["messages"][-1].content_blocks)

