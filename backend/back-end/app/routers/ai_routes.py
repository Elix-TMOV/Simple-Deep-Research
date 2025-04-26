from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from app.services.ai_service import generate_clarifying_questions, get_final_agent_query, QAPair, ResearchState, run_workflow

# Create a model for the request body
class UserQuery(BaseModel):
    user_query: str

class ReportQuery(BaseModel):
    user_query: str
    qaList: list[QAPair]
    
router = APIRouter()

@router.post("/get_carifying_questions", response_model=list[str])
async def get_carifying_questions(
    query: UserQuery,
    response: Response
):
    print("Received query the ai route was calleb:", query.user_query)
    """
    Generate clarifying questions based on the user's query.
    """
    try:
        questions_list = await generate_clarifying_questions(query.user_query)
        return questions_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating clarifying questions.",
        )


@router.post("/get_report")
async def get_report(
    report_query: ReportQuery,
    response: Response
):
    """
    Process the query and QA pairs to generate a comprehensive research report
    """
    try:
        # Generate the combined query from original query and QA pairs
        combined_query = get_final_agent_query(report_query.user_query, report_query.qaList)
        
        # Create the initial state for the workflow
        initial_state: ResearchState = {
            "user_query": report_query.user_query,
            "combined_query_context": combined_query,
            "search_queries": [],
            "search_results": [],
            "final_report": ""
        }
        
        # Run the workflow and get the final report
        final_report = await run_workflow(initial_state)
        
        return final_report
        
    except Exception as e:
        print(f"Error in get_report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the report: {str(e)}",
        )