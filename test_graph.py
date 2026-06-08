from unittest.mock import patch, MagicMock
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-fake-key-for-testing")

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

    with patch("app.LangGraph.create_engine") as mock_engine, \
         patch("app.LangGraph.llm_with_tools") as mock_llm:

        mock_engine.return_value.connect.return_value = mock_conn
        mock_llm.invoke.return_value = fake_llm_response

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
