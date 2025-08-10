"""
Polygon Financial Agent using MCP Server
A LangChain agent that uses the Financial MCP Server for stock market queries
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import asyncio
import os
import gradio as gr

load_dotenv()

class FinancialAgent:
    def __init__(self):
        # Initialize MCP client
        self.client = MultiServerMCPClient(
            {
                "financial": {
                    "command": "python",
                    "args": ["Polygon_MCP_server.py"],  # Path to your MCP server
                    "transport": "stdio",
                    "env": {
                        "POLYGON_API_KEY": os.getenv("POLYGON_API_KEY")
                    }
                }
            }
        )
        # Initialize Gemini model
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            google_api_key=GEMINI_API_KEY
        )
        # Placeholder for tools and agent
        self.tools = None
        self.agent = None

    async def initialize(self):
        """Initialize tools and agent"""
        print("Connecting to financial MCP server...")
        self.tools = await self.client.get_tools()
        print(f"Available tools: {[tool.name for tool in self.tools]}")
        self.agent = create_react_agent(self.model, self.tools)

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        if not self.agent:
            await self.initialize()
        
        messages = [{"role": "user", "content": query}]
        
        print("\n🤔 Processing...")
        response = await self.agent.ainvoke({"messages": messages})
        
        return response['messages'][-1].content

    async def chat_loop(self):
        """Run an interactive chat loop"""
        await self.initialize()
        
        print("\n🚀 Financial Agent Started!")
        print("Type your stock market queries (e.g., 'What's the latest price for AAPL?')")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("💰 Query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye! 👋")
                    break
                
                if not query:
                    continue
                
                response = await self.process_query(query)
                print(f"\n🤖 Response: {response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")

    async def cleanup(self):
        """Clean up resources"""
        await self.client.close()

def gradio_interface(query: str, agent: FinancialAgent) -> str:
    """Process queries for Gradio interface"""
    # Run async process_query in sync context for Gradio
    return asyncio.run(agent.process_query(query))

async def main(mode: str = "terminal"):
    """Main function to run the financial agent in terminal or web mode"""
    agent = FinancialAgent()
    try:
        if mode == "web":
            print("Launching Gradio web interface...")
            webapp = gr.Interface(
                fn=lambda query: gradio_interface(query, agent),
                inputs=gr.Textbox(lines=2, placeholder="Enter your query here..."),
                outputs=gr.Markdown(),
                title="Polygon Tools",
                description="AI Financial Agent powered by Gemini LLM and MCP server architecture. " \
                "Get real-time stock data, news, and market analysis through natural language queries.",
                # "Financial Agent dynamically invoking Polygon API tools with LangChain.",
                theme= gr.themes.Monochrome() #"default"
            )
            webapp.launch()
        else:
            await agent.chat_loop()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    import sys
    mode = "web" if len(sys.argv) > 1 and sys.argv[1] == "web" else "terminal"
    asyncio.run(main(mode))