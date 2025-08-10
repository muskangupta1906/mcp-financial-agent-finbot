# Polygon_Tools_UI.py #AgenticAI Without MCP
# This file sets up a Gradio web interface for a Financial Agent using Polygon API tools with LangGraph.

import os
import pprint
import gradio as gr 
from langchain import hub
from langchain.agents import create_openai_functions_agent
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.tools import PolygonLastQuote, PolygonTickerNews, PolygonFinancials, PolygonAggregates
from langchain_community.utilities.polygon import PolygonAPIWrapper
from langchain_core.agents import AgentFinish
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.graph import END, Graph
from langgraph.graph import END, StateGraph

import warnings
warnings.filterwarnings('ignore')

from dotenv import load_dotenv
load_dotenv()

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

polygon = PolygonAPIWrapper(polygon_api_key = POLYGON_API_KEY)

# llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    google_api_key=GEMINI_API_KEY
)

prompt = hub.pull('hwchase17/openai-functions-agent')
#pprint.pprint(prompt)

tools = [ 
    PolygonLastQuote(api_wrapper=polygon),
    PolygonTickerNews(api_wrapper=polygon),
    PolygonFinancials(api_wrapper=polygon),
    PolygonAggregates(api_wrapper=polygon)
]

agent_runnable = create_openai_functions_agent(llm, tools, prompt) #creat_agent_tool_calling

agent = RunnablePassthrough.assign(
    agent_outcome = agent_runnable
)

# print(agent) 

def execute_tools(data):
    print('lalalala')
    agent_action = data.pop('agent_outcome')
    tool_to_use = {t.name: t for t in tools}[agent_action.tool]
    observation = tool_to_use.invoke(agent_action.tool_input)
    print("Tool Output:", observation)

    data['intermediate_steps'].append((agent_action, observation))
    print("Updated Intermediate Steps:", data['intermediate_steps'])
    return data

#the LangGraph
from langgraph.graph import END, StateGraph

#logic that will be used to determine which conditional edge to go down
def should_continue(data):
    print("Agent Outcome:", data['agent_outcome'])
    if isinstance(data['agent_outcome'], AgentFinish):
        return "exit"
    else:
        return "continue"
from typing import TypedDict, List, Any

class AgentState(TypedDict):
    input: str
    intermediate_steps: List[Any]
    chat_history: List[Any]
    agent_outcome: Any

# Then create the StateGraph with the schema:
workflow = StateGraph(AgentState)
# workflow = StateGraph()
workflow.add_node("agent", agent)
workflow.add_node("tools", execute_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "exit": END
    }
)
workflow.add_edge('tools', 'agent')
chain = workflow.compile()

def financial_agent(input_text):
    input_data = {"input": input_text, "intermediate_steps": [], "chat_history": []}
    rendered_prompt = prompt.format(
        input=input_text,
        agent_scratchpad= input_data["intermediate_steps"],
        chat_history=input_data["chat_history"]
    )
    print("Rendered Prompt:")
    pprint.pprint(rendered_prompt, indent=2)

    result = chain.invoke({"input": input_text, "intermediate_steps": []})
    output = result['agent_outcome'].return_values["output"]

    print("Final Output:", output)
    return output

webapp = gr.Interface(
    fn=financial_agent,
    inputs=gr.Textbox(lines=2, placeholder="Enter your query here..."),
    outputs=gr.Markdown(),
    title = "Polygon Tools",
    description = "Financial Agent dynamically invocating Polygon API tools with LangGraph.",
    theme = "default"
)

webapp.launch()