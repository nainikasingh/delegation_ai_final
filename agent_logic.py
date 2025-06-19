from anthropic import Anthropic
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

anthropic = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

def format_tasks_for_prompt(tasks):
    def format_date(d): return d.strftime('%Y-%m-%d') if isinstance(d, datetime) else str(d)

    task_lines = []
    for t in tasks:
        line = (
            f"Task: {t.get('taskTitle')}, "
            f"Status: {t.get('taskStatus')}, "
            f"Target Date: {format_date(t.get('targetDate'))}, "
            f"Score: {t.get('taskScore')}, "
            f"Delegatees: {', '.join(str(uid) for uid in t.get('delegateeName', []))}"
        )
        task_lines.append(line)

    return "\n".join(task_lines)

def query_claude_with_tasks(prompt, tasks, role):
    input_text = f"""You are a delegation AI assistant. Based on the user's role and the task data, answer the prompt.

USER ROLE: {role}
PROMPT: {prompt}

TASK DATA:
{format_tasks_for_prompt(tasks)}

Answer accurately and clearly. If the data is not enough, explain what’s missing."""

    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.2,
            messages=[
                {"role": "user", "content": input_text}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Claude could not process your request: {str(e)}"
