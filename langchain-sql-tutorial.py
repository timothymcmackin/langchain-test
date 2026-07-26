from langchain.chat_models import init_chat_model

model = init_chat_model(
    "qwen3",
    model_provider="ollama",
    temperature=0.7,
)

import pathlib
import requests

url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
local_path = pathlib.Path("Chinook.db")

if local_path.exists():
    print(f"{local_path} already exists, skipping download.")
else:
    response = requests.get(url, timeout=60)
    if response.status_code == 200:
        local_path.write_bytes(response.content)
        print(f"File downloaded and saved as {local_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

import sqlite3

con = sqlite3.connect("Chinook.db")
cursor = con.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

print("Dialect: sqlite")
print(f"Available tables: {tables}")

cursor.execute("SELECT * FROM Artist LIMIT 5;")
print(f"Sample output: {cursor.fetchall()}")
con.close()

import sqlite3
from langchain.tools import tool

# Below are minimal tools for demonstration purposes.
# They are not intended to be secure or for production use.

@tool
def sql_db_list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""
    con = sqlite3.connect("Chinook.db")
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        return ", ".join(tables)
    finally:
        con.close()

@tool
def sql_db_schema(table_names: str) -> str:
    """Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables.
    Be sure that the tables actually exist by calling sql_db_list_tables first!
    Example Input: table1, table2, table3"""
    con = sqlite3.connect("Chinook.db")
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        valid_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")}
        results = []
        for table in table_names.split(","):
            table = table.strip()
            if table not in valid_tables:
                results.append(f"Error: table_names {{{table!r}}} not found in database")
                continue
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
            schema_row = cursor.fetchone()
            if schema_row:
                results.append(schema_row[0])
                try:
                    quoted_table = '"' + table.replace('"', '""') + '"'
                    cursor.execute(f"SELECT * FROM {quoted_table} LIMIT 3;")
                    rows = cursor.fetchall()
                    if rows:
                        col_names = [description[0] for description in cursor.description]
                        results.append(
                            f"/*\n3 rows from {table} table:\n"
                            + "\t".join(col_names)
                            + "\n"
                            + "\n".join("\t".join(str(x) for x in row) for row in rows)
                            + "\n*/"
                        )
                except Exception as e:
                    results.append(f"Error fetching sample rows: {e}")
        return "\n\n".join(results)
    finally:
        con.close()

@tool
def sql_db_query(query: str) -> str:
    """Input to this tool is a detailed and correct SQL query, output is a result from the database.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields."""
    con = sqlite3.connect("Chinook.db")
    try:
        cursor = con.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        return str(res)
    except Exception as e:
        return f"Error: {e}"
    finally:
        con.close()

@tool
def sql_db_query_checker(query: str) -> str:
    """Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with sql_db_query!"""
    trigger_prompt = """{query}
Double check the sqlite query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.

SQL Query: """.format(query=query)

    response = model.invoke(trigger_prompt)
    return response.text.strip()

tools = [sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker]

# Use a distinct loop variable so it does not shadow the `tool` decorator.
for t in tools:
    print(f"{t.name}: {t.description}\n")



system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect="sqlite",
    top_k=5,
)

from langchain.agents import create_agent


agent = create_agent(
    model,
    tools,
    system_prompt=system_prompt,
)

question = "Which genre on average has the longest tracks?"

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


'''
Chinook.db already exists, skipping download.
Dialect: sqlite
Available tables: ['Album', 'Artist', 'Customer', 'Employee', 'Genre', 'Invoice', 'InvoiceLine', 'MediaType', 'Playlist', 'PlaylistTrack', 'Track']
Sample output: [(1, 'AC/DC'), (2, 'Accept'), (3, 'Aerosmith'), (4, 'Alanis Morissette'), (5, 'Alice In Chains')]
sql_db_list_tables: Input is an empty string, output is a comma-separated list of tables in the database.

sql_db_schema: Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables.
Be sure that the tables actually exist by calling sql_db_list_tables first!
Example Input: table1, table2, table3

sql_db_query: Input to this tool is a detailed and correct SQL query, output is a result from the database.
If the query is not correct, an error message will be returned.
If an error is returned, rewrite the query, check the query, and try again.
If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields.

sql_db_query_checker: Use this tool to double check if your query is correct before executing it.
Always use this tool before executing a query with sql_db_query!

/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph/pregel/main.py:3708: LangChainBetaWarning: The v3 streaming protocol on Pregel is experimental.
  return self._pregel_stream_v3(
/Users/tim/repos/langchain-test/.venv/lib/python3.14/site-packages/langgraph/pregel/main.py:3558: LangChainBetaWarning: The v3 streaming protocol on Pregel is experimental.
  return GraphRunStream(graph_iter, mux)

Tool call: sql_db_list_tables({})

Tool result: content='Album, Artist, Customer, Employee, Genre, Invoice, InvoiceLine, MediaType, Playlist, PlaylistTrack, Track' name='sql_db_list_tables' tool_call_id='1919d19b-3406-4ba1-b998-6b5a7e7081fd'

Tool call: sql_db_schema({'tables': 'Track,Genre'})

Tool result: None

Tool call: sql_db_schema({'tables': ['Track', 'Genre']})

Tool result: None

Tool call: sql_db_schema({'tables': 'Track,Genre'})

Tool result: None

Tool call: sql_db_schema({'tables': 'Track,Genre'})

Tool result: None

Tool call: sql_db_query_checker({'query': 'SELECT g.Name, AVG(t.Milliseconds) as AvgDuration FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY AvgDuration DESC LIMIT 5;'})

Tool result: content='SELECT g.Name, AVG(t.Milliseconds) as AvgDuration FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY AvgDuration DESC LIMIT 5;' name='sql_db_query_checker' tool_call_id='b44ae2ab-cb20-4420-b8ef-bbf41fc9a424'
SELECT g.Name, AVG(t.Milliseconds) as AvgDuration FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY AvgDuration DESC LIMIT 5;
Tool call: sql_db_query({'query': 'SELECT g.Name, AVG(t.Milliseconds) as AvgDuration FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY AvgDuration DESC LIMIT 5;'})

Tool result: content="[('Sci Fi & Fantasy', 2911783.0384615385), ('Science Fiction', 2625549.076923077), ('Drama', 2575283.78125), ('TV Shows', 2145041.0215053763), ('Comedy', 1585263.705882353)]" name='sql_db_query' tool_call_id='7e122d0d-29df-460c-b8b7-72a3654755ee'
The genre with the longest tracks on average is **Sci Fi & Fantasy** with an average track length of **2,911,783 milliseconds** (approximately 29 minutes).

Here are the top 5 genres by average track duration:
1. Sci Fi & Fantasy (29 minutes)
2. Science Fiction (26 minutes)
3. Drama (25 minutes)
4. TV Shows (21 minutes)
5. Comedy (15 minutes)
'''