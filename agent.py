import os
import json
from groq import Groq
from dotenv import load_dotenv
from tools import get_tool_descriptions, run_tool, TOOLS

load_dotenv()

# im using llama 3.3 70b from groq - its fast and free
MODEL = "llama-3.3-70b-versatile"
_client = None

def get_client():
    """lazy load the groq client so it doesnt crash on import if key is missing"""
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


# this prompt is the most important part - it tells the LLM how to behave as an agent
SYSTEM_PROMPT = """You are an AI agent that solves tasks step by step. You have access to these tools:

{tools}

For each step, respond with ONLY valid JSON in this exact format:
{{
    "thought": "what you're thinking about and planning to do",
    "tool": "tool_name",
    "tool_input": "input for the tool",
    "is_final": false
}}

When you have enough information to give the final answer, respond with:
{{
    "thought": "I now have all the information needed",
    "tool": null,
    "tool_input": null,
    "is_final": true,
    "final_answer": "your complete answer here"
}}

Rules:
1. Think step by step. Break complex tasks into smaller steps.
2. Use tools when you need real information. Dont make stuff up.
3. After using a tool, analyze the result before deciding next step.
4. Maximum 10 steps. If you cant solve it by then, give your best answer.
5. tool must be one of the available tool names or null.
6. Always respond with ONLY valid JSON, nothing else.
"""


def run_agent(task, on_step=None):
    """main agent loop - keeps running until it gets a final answer or hits max steps"""

    client = get_client()
    tool_desc = get_tool_descriptions()
    system = SYSTEM_PROMPT.format(tools=tool_desc)

    # this is basically the agent's memory - it remembers past steps
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Task: {task}"}
    ]

    max_steps = 10
    steps = []

    for step_num in range(1, max_steps + 1):
        print(f"\n--- step {step_num} ---")

        try:
            # ask the AI what to do next
            chat = client.chat.completions.create(
                messages=messages,
                model=MODEL,
                temperature=0.3,
                max_tokens=1024
            )

            response_text = chat.choices[0].message.content
            print(f"agent said: {response_text[:200]}")

            # groq sometimes wraps response in ```json blocks, need to clean that
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            # try parsing the json response
            try:
                decision = json.loads(cleaned.strip())
            except json.JSONDecodeError:
                print(f"bad json from ai, trying to extract it...")
                # the ai sometimes adds random text around the json
                # so im trying to find the json object manually
                start = cleaned.find('{')
                end = cleaned.rfind('}') + 1
                if start >= 0 and end > start:
                    decision = json.loads(cleaned[start:end])
                else:
                    # give up and make a final answer from whatever the ai said
                    decision = {
                        "thought": "I'll answer directly",
                        "tool": None,
                        "tool_input": None,
                        "is_final": True,
                        "final_answer": response_text
                    }

            thought = decision.get("thought", "thinking...")
            tool_name = decision.get("tool")
            tool_input = decision.get("tool_input", "")
            is_final = decision.get("is_final", False)

            # check if agent is done thinking
            if is_final:
                final_answer = decision.get("final_answer", "Done.")
                step_data = {
                    "step": step_num,
                    "thought": thought,
                    "is_final": True,
                    "final_answer": final_answer
                }
                steps.append(step_data)
                if on_step:
                    on_step(step_data)
                print(f"agent done! answer: {final_answer[:100]}")
                return {
                    "final_answer": final_answer,
                    "steps": steps,
                    "total_steps": step_num
                }

            # agent picked a tool to use
            if tool_name:
                if tool_name not in TOOLS:
                    tool_output = f"Tool '{tool_name}' does not exist. Available: {', '.join(TOOLS.keys())}"
                else:
                    print(f"using tool: {tool_name}({tool_input[:100]})")
                    tool_output = run_tool(tool_name, tool_input)
                    print(f"tool result: {str(tool_output)[:200]}")

                step_data = {
                    "step": step_num,
                    "thought": thought,
                    "tool": tool_name,
                    "tool_input": tool_input,
                    "tool_output": str(tool_output)[:2000],  # limit output size
                    "is_final": False
                }
                steps.append(step_data)
                if on_step:
                    on_step(step_data)

                # feed the result back so the agent knows what happened
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Tool result from {tool_name}:\n{str(tool_output)[:2000]}\n\nContinue with the next step."})

            else:
                # no tool and not final? weird but handle it
                step_data = {
                    "step": step_num,
                    "thought": thought,
                    "is_final": False
                }
                steps.append(step_data)
                if on_step:
                    on_step(step_data)
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": "Continue. Pick a tool or give your final answer."})

        except Exception as e:
            print(f"agent error at step {step_num}: {e}")
            step_data = {
                "step": step_num,
                "thought": f"Error: {str(e)}",
                "is_final": True,
                "final_answer": f"Sorry, ran into an error: {str(e)}"
            }
            steps.append(step_data)
            if on_step:
                on_step(step_data)
            return {
                "final_answer": f"Error: {str(e)}",
                "steps": steps,
                "total_steps": step_num
            }

    # hit max steps - force a final answer
    print("hit max steps, forcing final answer")
    final = "I reached the maximum number of steps. Based on what I found: " + (steps[-1].get("tool_output", "no results") if steps else "no info gathered")
    return {
        "final_answer": final,
        "steps": steps,
        "total_steps": max_steps
    }
