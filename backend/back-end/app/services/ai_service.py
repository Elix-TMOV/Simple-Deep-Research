# time to code a llm call for generating questions further questions
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

from typing import List, Dict, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END

load_dotenv()

gemini_api_key = "Your gemini api key here"
tavily_api_key = "Your tavily api key here"

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    google_api_key=gemini_api_key,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2, 
)

class questionsModel(BaseModel):
  """
    Pydantic model for holding a list of web clarifying questions.
  """
  questions: List[str] = Field(
        ..., description="questions that will be asked to the user to better understand the requirement, motives, and aims."
  )

async def generate_clarifying_questions(user_query: str):
  """
    we will ask use three questions to better understand the motives and the aims of the research so that we can conduct well thorough aligned research
  """
  system_message = SystemMessagePromptTemplate.from_template(
      """
      Based on the following user query, generate 3 follow-up questions that would help clarify what the user wants to know.
      These questions should:
      1. Seek to understand the user's specific information needs, requirements or goal for seeking this information
      2. Clarify ambiguous terms or concepts in the original query
      3. Determine the scope or boundaries of what the user is looking for
      4. Identify the user's level of familiarity with the topic
      """
  )
  human_message = human_message = HumanMessagePromptTemplate.from_template(
      """
      User asked: "{user_query}"
      Generate 3 follow up questions
      Return only a JSON object like:
        {{
          "follow_up_questions": ["question one", "question two", ...]
        }}
      """
  )


  prompt = ChatPromptTemplate.from_messages([system_message, human_message])

  structured_llm = llm.with_structured_output(questionsModel)

  messages = prompt.format_messages(user_query=user_query)

  try:
    response = await structured_llm.ainvoke(messages)
  except Exception as e:
    print("Error in generating clarifying questions:", e)
    return {"error": "Failed to generate clarifying questions."}

  return response.questions


# the rest of the code is for the agent or may I should call it a workflow
class ResearchState(TypedDict):
    """Represents the state of the research process within the agent."""
    user_query: str  # The original query (passed in, needed for report)
    combined_query_context: str  # the original query + the clarifying questions and their answers
    search_queries: List[str]  # Queries generated by the agent
    search_results: List[Dict[str, Any]]  # Results obtained from the search tool
    final_report: str  # The final synthesized report


async def execute_search(state: ResearchState):
    tavily_search_tool = TavilySearch(
        max_results=5,
        topic="general",
        tavily_api_key = tavily_api_key,
        search_depth="advanced",
        include_raw_content=True,
    )

    search_queries: List[str] = state.get("search_queries", [])
    queries = [{"query": query} for query in search_queries]

    # --- AWAIT the asynchronous abatch call ---
    results = await tavily_search_tool.abatch(queries)

    for result in results:
      del result["answer"]
      del result["follow_up_questions"]
      del result["images"]

    # delete the useless
    return {"search_results": results}
  
class QueryPlan(BaseModel):
    """
    Pydantic model for holding a list of web search queries.
    """
    queries: List[str] = Field(
        ..., description="Queries that will be used for web search."
    )


def generate_search_queries(
    state: ResearchState,
    max_queries: int = 8,
) -> QueryPlan:
    """
    Generate up to `max_queries` concise web search queries for a given user query
    using the Google Gemini model via LangChain. Returns a QueryPlan model.
    """
    # Build a clear system + user prompt for structured JSON output
    system_message = SystemMessagePromptTemplate.from_template(
        """
        You are an AI assistant that creates structured research plans.
        Your task is to turn a user's general query into a set of focused search queries.
        Always output valid JSON with a single key `queries`, whose value is a list of strings.
        """
    )
    human_message = HumanMessagePromptTemplate.from_template(
        """
        User asked: "{user_query}"
        Generate up to {max_queries}, specific search queries that cover different
        facets of the topic. If there exists some serious consideration or cons include them in the search queries as well.
        Return only a JSON object like:
        {{
          "queries": ["first query", "second query", ...]
        }}
        """
    )
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])

    # Create the structured LLM runnable
    structured_llm = llm.with_structured_output(QueryPlan)

    messages = prompt.format_messages(user_query=state["combined_query_context"], max_queries=max_queries)

    # Now invoke the chain with the input variables
    response = structured_llm.invoke(
        messages
    )

    # The response is already the parsed Pydantic object (QueryPlan)
    return {"search_queries": response.queries}


def report_writer(state: ResearchState):
    system_message = SystemMessagePromptTemplate.from_template(
        """
        You are a report writer who must examine and analyze a corpus of search results and data on a given topic and write an objective, detialed and comprehensive report
        that incorporates all of the researched data.

        Use headings for main sections and apply markdown formatting to structure the report.

        Include all the reference and the links at the end.
        """
    )

    human_message = HumanMessagePromptTemplate.from_template(
        """
          You Ought to write the report for this topic {user_query}. Here is all the researched data: {search_data}.
          Give out a highly detialed and comprehensive report include everything that was present in the research data
        """
    )

    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    message = prompt.format_messages(user_query=state["user_query"], search_data = state["search_results"])



    report = llm.invoke(message).content

    return {"final_report": report}
  

workflow = StateGraph(ResearchState)

# Add the execute_search node
workflow.add_node("create_search_queries", generate_search_queries)
workflow.add_node("execute_search", execute_search)
workflow.add_node("report_writer", report_writer)


workflow.set_entry_point("create_search_queries")
workflow.add_edge("create_search_queries", "execute_search")
workflow.add_edge("execute_search", "report_writer")
workflow.add_edge("report_writer", END)

application = workflow.compile()


async def run_workflow(initial_state):
    result = await application.ainvoke(initial_state)
    return result["final_report"]

class QAPair(BaseModel):
    question: str
    answer: str

def get_final_agent_query(user_query: str, clarifying_ques_ans: List[QAPair]) -> str:
    """Gets user input for each clarifying question and concatenates them."""
    qes_ans_query = ""
    for item in clarifying_ques_ans:
        qes_ans_query += f"Question: {item.question}\nAnswer: {item.answer}\n"
        
    combined_query = f"{user_query}\n\nClarifying questions and their answers:\n{qes_ans_query}"
    return combined_query


