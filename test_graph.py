from unittest.mock import patch, MagicMock
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-fake-key-for-testing")
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "fake-langfuse-public-key")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "fake-langfuse-secret-key")
os.environ.setdefault("LANGFUSE_HOST", "http://localhost")
os.environ.setdefault("ALLOWED_USER_ID", "0")
os.environ.setdefault("PROMPT_NAME", "text-to-sql-bot-v1")

from langchain_core.messages import AIMessage
from app.LangGraph import react_graph


def test_graph_runs():
    fake_schema = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
    fake_llm_response = AIMessage(content="Вот результат запроса")

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.fetchall.return_value = [("users",)]
    mock_conn.execute.return_value.scalar.return_value = fake_schema

    mock_prompt = MagicMock()
    mock_prompt.config = {"model": "gpt-4o", "max_tokens": 1500}
    mock_prompt.compile.return_value = "fake system message"

    mock_llm_instance = MagicMock()
    mock_llm_instance.bind_tools.return_value.invoke.return_value = fake_llm_response

    with patch("app.LangGraph.create_engine") as mock_engine, \
         patch("app.LangGraph.langfuse") as mock_langfuse, \
         patch("app.LangGraph.ChatOpenAI") as mock_chat_openai:

        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_chat_openai.return_value = mock_llm_instance
        mock_engine.return_value.connect.return_value = mock_conn

        result = react_graph.invoke({
            "database": "kali",
            "user_input": "покажи всех пользователей",
            "database_schema": "",
            "messages": []
        })

    assert "messages" in result
    print("OK: граф отработал")
    print("Ответ LLM:", result["messages"][-1].content)


if __name__ == "__main__":
    test_graph_runs()
