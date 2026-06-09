from typing_extensions import TypedDict
from typing import List, TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.graph import START, StateGraph
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display

class State(TypedDict):
    database: str
    user_input: str 
    database_schema: str
    messages: Annotated[list[AnyMessage], add_messages]

langfuse_handler = CallbackHandler()

############ TOOLS

def db_query(sql_query: str, database_name: str) -> list:
    """
    Execute query in SQL syntac from sqlite database called database_name.

    Args:
        sql_query: SQL query
        database_name: name of database from which to execute

    Returns:
        A list of rows with answer
"""
    if database_name == 'kali':
        database_url = "sqlite:////app/data/kali/app.db"
    else:
        database_url = "sqlite:////app/data/dreams/app.db"
    connect_args = {"check_same_thread": False, "timeout": 30} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        result = session.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return f"Ошибка запроса: {e}"
    finally:
        session.close()

# Equip the butler with tools
tools = [
    db_query
    ]

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)


########### NODES



def get_schema_db(state: State):
    db_name = state["database"]
    
    if db_name == 'kali':
        database_url = "sqlite:////app/data/kali/app.db"
    else:
        database_url = "sqlite:////app/data/dreams/app.db"

    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_engine(database_url, connect_args=connect_args, future=True)

    with engine.connect() as conn:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        schema_parts = []
        for (table_name,) in tables:
            create_sql = conn.execute(
                text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": table_name}
            ).scalar()
            schema_parts.append(create_sql)

    return {
            "database": state['database'], 
            "database_schema": "\n\n".join(schema_parts),
            "user_input": state["user_input"]
            }

def assistant(state: State):
    # System message
    user_query = state["user_input"]
    db_schema = state["database_schema"]
    database_name = state["database"]

    textual_description_of_tool="""
def db_query(sql_query: str, database_name: str) -> list
    Execute query in SQL syntac from sqlite database called database_name.

    Args:
        sql_query: SQL query
        database_name: name of database from which to execute

    Returns:
        A list of rows with answer
"""
    systemprompt = f"""
You are an analytic. You can make SQL queries to databases from human language query of your manager:
This is user query in human language: {user_query}
Here is the name of the database you want to make query: {database_name}\n
These schemas of all tables in this database: {db_schema}\n
Here is a descriprion of the tool-sql-executer \n {textual_description_of_tool}\n
You should execute the user query with your tool passing argument of sql query
then answer using beautiful formatting of the output of the tool please

"""
    sys_msg = SystemMessage(content=systemprompt)

    return {
        "messages": [llm_with_tools.invoke([sys_msg] + state["messages"])],
    }


################### Graph itself

builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("get_schema_db", get_schema_db)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "get_schema_db")
builder.add_edge("get_schema_db", "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message requires a tool, route to tools
    # Otherwise, provide a direct response
    tools_condition,
)
builder.add_edge("tools", "assistant")
react_graph = builder.compile()

