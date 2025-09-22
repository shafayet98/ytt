import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from tools import get_video_transcript, make_segments


# =============================== AGENTS ===============================

def create_video_processor_agent():
    """
    Create VideoProcessorAgent that handles transcript fetching and segmentation
    """
    # Initialize the LLM without structured output
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Tools available to VideoProcessorAgent
    tools = [get_video_transcript, make_segments]

    # Very explicit system prompt about parameter handling
    system_prompt = """You are VideoProcessorAgent, a specialized agent for processing YouTube videos.

    Your job is to:
    1. Use get_video_transcript tool to fetch the transcript and metadata
    2. Use make_segments tool to create 5 time-based segments
    3. Return a summary of the segmentation results

    CRITICAL WORKFLOW - Follow this EXACTLY:

    Step 1: Call get_video_transcript with the video URL
    
    Step 2: Extract the required data from the transcript result:
    - Look for "transcript_snippets" key (this is a list of dictionaries)
    - Look for "metadata" key, then "total_duration" inside it (this is a number)
    
    Step 3: Call make_segments with exactly these three parameters:
    make_segments(
        transcript_snippets=[the list from step 2],
        total_duration=the_number_from_metadata,
        num_segments=5
    )

    CRITICAL: Do NOT pass strings or partial objects. Pass the actual extracted values.
    - transcript_snippets must be the actual list, not a string
    - total_duration must be the actual number, not a string
    - num_segments must be the integer 5

    Step 4: Return a summary of what was accomplished

    If you get validation errors, double-check that you're passing the correct data types."""

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True
    )
    
    return agent_executor