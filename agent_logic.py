from anthropic import Anthropic
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

anthropic = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

def is_general_prompt(prompt: str) -> bool:
    general_keywords = ["hello", "hi", "how are you", "good morning", "good evening", "hey"]
    return any(word in prompt.lower() for word in general_keywords)

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

def query_claude_with_tasks(prompt: str, tasks: list, role: str) -> str:
    if is_general_prompt(prompt):
        return "Hi there! 👋 I'm your Delegation AI assistant. I can help you track tasks, deadlines, and team performance. Just ask me a question!"

    total_score = sum(
        t.get("taskScore", 0)
        for t in tasks
        if isinstance(t.get("taskScore"), (int, float))
    )

    # Shortcut bypass Claude if the user is only asking about total score
    if "total score" in prompt.lower() or "overall performance" in prompt.lower():
        return f"Your total score is {total_score}. You have handled {len(tasks)} tasks based on the available data."

    input_text = f"""
        You are a Delegation AI Assistant. Based on the USER ROLE and the TASK DATA provided, answer the user's question directly, accurately, and concisely. Use only the information available in the task data. Do NOT ask for more data or suggest improvements unless explicitly asked.

        USER ROLE: {role}
        USER TOTAL SCORE: {total_score}
        PROMPT: {prompt}

        TASK DATA:
        {format_tasks_for_prompt(tasks)}

        Answer only what is asked, based on the task data above. Don't speculate or add recommendations unless prompted.
    """

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
        return f"⚠️ Delegation AI Agent could not process your request: {str(e)}"
