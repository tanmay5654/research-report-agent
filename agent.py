"""
Research & Report Agent
-----------------------
Flow: Topic → Search Node → Analyze Node → Write Report Node → Output

Uses:
- LangGraph for agent orchestration
- Tavily for web search
- Groq (llama-3.3-70b) for reasoning and report writing (free tier)
"""

import os
from dotenv import load_dotenv
from typing import TypedDict, List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from tavily import TavilyClient

load_dotenv()

# ── Clients ──────────────────────────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ── State ─────────────────────────────────────────────────────────────────────
# This dict is passed between every node in the graph.

class ResearchState(TypedDict):
    topic: str                  # The user's research question
    search_results: List[dict]  # Raw results from Tavily
    analysis: str               # Claude's synthesis of the results
    report: str                 # Final structured report


# ── Node 1: Search ────────────────────────────────────────────────────────────

def search_node(state: ResearchState) -> ResearchState:
    """Search the web for the research topic using Tavily."""
    print(f"\n[Search] Searching for: {state['topic']}")

    results = tavily.search(
        query=state["topic"],
        search_depth="advanced",  # deeper crawl
        max_results=5,
    )

    state["search_results"] = results.get("results", [])
    print(f"[Search] Found {len(state['search_results'])} sources")
    return state


# ── Node 2: Analyze ───────────────────────────────────────────────────────────

def analyze_node(state: ResearchState) -> ResearchState:
    """Claude reads the raw search results and extracts key insights."""
    print("\n[Analyze] Synthesizing search results...")

    # Format search results into readable text
    sources_text = ""
    for i, result in enumerate(state["search_results"], 1):
        sources_text += f"\n--- Source {i} ---\n"
        sources_text += f"Title: {result.get('title', 'N/A')}\n"
        sources_text += f"URL: {result.get('url', 'N/A')}\n"
        sources_text += f"Content: {result.get('content', 'N/A')}\n"

    response = llm.invoke([
        SystemMessage(content=(
            "You are a research analyst. Read the following search results and "
            "extract the most important facts, trends, and insights about the topic. "
            "Be concise but thorough. Identify key themes and note any conflicting information."
        )),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n\n"
            f"Search Results:\n{sources_text}"
        )),
    ])

    state["analysis"] = response.content
    print("[Analyze] Analysis complete.")
    return state


# ── Node 3: Write Report ──────────────────────────────────────────────────────

def write_report_node(state: ResearchState) -> ResearchState:
    """Claude turns the analysis into a clean, structured Markdown report."""
    print("\n[Report] Writing final report...")

    response = llm.invoke([
        SystemMessage(content=(
            "You are a professional report writer. Write a clear, well-structured "
            "research report in Markdown format. Include:\n"
            "1. Executive Summary\n"
            "2. Key Findings (with bullet points)\n"
            "3. Detailed Analysis (2-3 sections)\n"
            "4. Conclusion\n"
            "5. Sources Used\n\n"
            "Make it professional, readable, and insightful."
        )),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n\n"
            f"Research Analysis:\n{state['analysis']}\n\n"
            f"Sources:\n" + "\n".join(
                f"- [{r.get('title')}]({r.get('url')})"
                for r in state["search_results"]
            )
        )),
    ])

    state["report"] = response.content
    print("[Report] Report written successfully.")
    return state


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("search", search_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("write_report", write_report_node)

    # Define edges (the flow)
    graph.set_entry_point("search")
    graph.add_edge("search", "analyze")
    graph.add_edge("analyze", "write_report")
    graph.add_edge("write_report", END)

    return graph.compile()


# ── Run ───────────────────────────────────────────────────────────────────────

def run_research_agent(topic: str) -> str:
    """Run the full research pipeline on a given topic."""
    agent = build_graph()

    initial_state: ResearchState = {
        "topic": topic,
        "search_results": [],
        "analysis": "",
        "report": "",
    }

    final_state = agent.invoke(initial_state)
    return final_state["report"]


if __name__ == "__main__":
    topic = input("Enter research topic: ").strip()

    if not topic:
        topic = "Latest advancements in Agentic AI 2025"

    report = run_research_agent(topic)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)

    # Save report to file
    filename = topic.replace(" ", "_")[:40] + "_report.md"
    with open(filename, "w") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(report)

    print(f"\nReport saved to: {filename}")
