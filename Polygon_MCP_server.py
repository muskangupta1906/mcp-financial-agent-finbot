"""
Financial MCP Server that provides financial data tools using Polygon.io API
"""

import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from mcp import Tool #McpServer
from mcp.types import TextContent
from langchain_community.utilities.polygon import PolygonAPIWrapper
from langchain_community.tools import (
    PolygonLastQuote, 
    PolygonTickerNews, 
    PolygonFinancials, 
    PolygonAggregates
)
from mcp.server.fastmcp import FastMCP


load_dotenv()

polygon_api_key = os.environ.get("POLYGON_API_KEY")

polygon = PolygonAPIWrapper(polygon_api_key=polygon_api_key)

# server = McpServer("financial-server")
server =FastMCP("financial-server")
quote_tool = PolygonLastQuote(api_wrapper=polygon)
news_tool = PolygonTickerNews(api_wrapper=polygon)
financials_tool = PolygonFinancials(api_wrapper=polygon)
aggregates_tool = PolygonAggregates(api_wrapper=polygon)

@server.tool("get_last_quote")
async def get_last_quote(ticker: str) -> List[TextContent]:
    """Get the last quote for a stock ticker"""
    try:
        result = quote_tool.invoke({"query": ticker})
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting quote for {ticker}: {str(e)}")]

@server.tool("get_ticker_news")
async def get_ticker_news(ticker: str) -> List[TextContent]:
    """Get recent news for a stock ticker"""
    try:
        result = news_tool.invoke({"query": ticker})
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting news for {ticker}: {str(e)}")]

@server.tool("get_financials")
async def get_financials(ticker: str) -> List[TextContent]:
    """Get financial data for a stock ticker"""
    try:
        result = financials_tool.invoke({"query": ticker})
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting financials for {ticker}: {str(e)}")]

@server.tool("get_aggregates")
async def get_aggregates(ticker: str, timespan: str = "day", from_date: str = "", to_date: str = "") -> List[TextContent]:
    """Get aggregate market data for a stock ticker"""
    try:
        query = {"ticker": ticker, "timespan": timespan}
        if from_date:
            query["from"] = from_date
        if to_date:
            query["to"] = to_date
        
        result = aggregates_tool.invoke(query)
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting aggregates for {ticker}: {str(e)}")]

# if __name__ == "__main__":
#     import asyncio
#     from mcp import run_server
    
#     asyncio.run(run_server(server))

if __name__=="__main__":
    # asyncio.run(main())
    server.run(transport="stdio")