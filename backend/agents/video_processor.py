import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from tools import process_video_and_segment

# Add this import at the top
from utils.custom_callbacks import CleanToolCallbackHandler

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
    tools = [process_video_and_segment]

    # Very explicit system prompt about parameter handling
    system_prompt = """You are VideoProcessorAgent, a specialized agent for processing YouTube videos.

    Your job is to:
    1. Use the process_video_and_segment tool to fetch transcript and create segments in one step
    2. Return a summary of the segmentation results

    SIMPLE WORKFLOW:

    Step 1: Call process_video_and_segment(video_url="the_youtube_url", num_segments=5)

    Step 2: Return a summary including:
    - Video metadata (duration, snippets count)
    - Number of segments created
    - Brief overview of what was accomplished"""

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
        callbacks=[CleanToolCallbackHandler(show_input=True, show_timing=True)], 
        return_intermediate_steps=True
    )
    
    return agent_executor