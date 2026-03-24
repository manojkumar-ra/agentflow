import subprocess
import math
import datetime
from rag import search_documents as rag_search

# all the tools that the agent can pick from
# basically each function takes some input and gives back text


def web_search(query):
    """search the internet using duckduckgo"""
    try:
        from ddgs import DDGS

        ddg = DDGS()
        results = ddg.text(query, max_results=5)
        if not results:
            return "No results found."

        output = ""
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   {r['body']}\n"
            output += f"   URL: {r['href']}\n\n"

        return output.strip()

    except Exception as e:
        print(f"search error: {e}")
        return f"Search failed: {str(e)}"


def run_python(code):
    """run python code and return the output
    dont run this in production lol"""
    try:
        # basic safety - block dangerous stuff
        blocked = ['import os', 'import subprocess', 'import shutil', 'open(', 'exec(', 'eval(', '__import__']
        for b in blocked:
            if b in code:
                return f"Blocked: cant use '{b}' for safety reasons"

        result = subprocess.run(
            ['python', '-c', code],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout
        if result.stderr:
            output += "\nError: " + result.stderr

        if not output.strip():
            return "Code ran successfully but produced no output."

        return output.strip()

    except subprocess.TimeoutExpired:
        return "Code took too long (over 10 seconds). Try simpler code."
    except Exception as e:
        return f"Failed to run code: {str(e)}"


def calculator(expression):
    """evaluate math expressions - only allows math functions nothing dangerous"""
    try:
        allowed = {
            'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
            'tan': math.tan, 'log': math.log, 'log10': math.log10,
            'pi': math.pi, 'e': math.e, 'pow': pow, 'abs': abs,
            'round': round, 'floor': math.floor, 'ceil': math.ceil
        }
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


def wiki_search(topic):
    """search wikipedia - good for factual stuff"""
    try:
        import wikipedia
        summary = wikipedia.summary(topic, sentences=4)
        return summary
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


def get_datetime():
    """get current date and time"""
    now = datetime.datetime.now()
    return f"Current date: {now.strftime('%B %d, %Y')}\nCurrent time: {now.strftime('%I:%M %p')}\nDay: {now.strftime('%A')}"


def search_docs(query):
    """search through uploaded documents using RAG"""
    try:
        result = rag_search(query, top_k=5)
        return result
    except Exception as e:
        return f"Document search failed: {str(e)}"


# registering all tools here - agent picks from this dict
TOOLS = {
    "web_search": {
        "func": web_search,
        "description": "Search the internet for current information. Input: search query string."
    },
    "run_python": {
        "func": run_python,
        "description": "Execute Python code and get the output. Input: python code as a string."
    },
    "calculator": {
        "func": calculator,
        "description": "Calculate a math expression. Input: math expression like '2 + 2' or 'sqrt(144)'."
    },
    "wiki_search": {
        "func": wiki_search,
        "description": "Search Wikipedia for factual information about a topic. Input: topic name."
    },
    "get_datetime": {
        "func": get_datetime,
        "description": "Get the current date, time and day. Input: not needed, just pass 'now'."
    },
    "search_documents": {
        "func": search_docs,
        "description": "Search through uploaded documents/files for relevant information using RAG. Input: your search query."
    }
}


def get_tool_descriptions():
    """builds the tool list string that goes into the system prompt"""
    desc = ""
    for name, info in TOOLS.items():
        desc += f"- {name}: {info['description']}\n"
    return desc


def run_tool(tool_name, tool_input):
    """run a tool by name and return the result"""
    if tool_name not in TOOLS:
        return f"Tool '{tool_name}' does not exist. Available tools: {', '.join(TOOLS.keys())}"

    tool_func = TOOLS[tool_name]["func"]

    # get_datetime doesnt need input
    if tool_name == "get_datetime":
        return tool_func()

    return tool_func(tool_input)
