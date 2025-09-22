import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor  
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import OPENAI_API_KEY, DEFAULT_MODEL
from tools import text_splitter, process_chunks_parallel

# =============================== AGENT 2 ===============================

def create_insight_extraction_agent():
    """
    Create InsightExtractionAgent that processes segments and extracts insights
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Slightly higher for creativity in storytelling
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Tools available to InsightExtractionAgent
    tools = [text_splitter, process_chunks_parallel]

    # System prompt for InsightExtractionAgent
    system_prompt = """You are InsightExtractionAgent, a specialized agent for extracting insights and creating engaging stories from video content.

Your job is to:
1. Receive video segments from VideoProcessorAgent
2. Process each segment to extract valuable insights
3. Create meaningful, contextual names for each segment
4. Transform content into engaging, story-like summaries
5. Return structured analysis with insights and narratives

For each segment you process:

WORKFLOW:
1. Check the segment content size and estimated tokens
2. If segment is large (>40k tokens):
   - Use text_splitter tool to break it into manageable chunks
   - Use process_chunks_parallel tool to process all chunks simultaneously
   - Combine the results into a coherent segment analysis
3. If segment is manageable:
   - Process directly without chunking
4. For each processed segment, provide:
   - A meaningful name (replace generic "Segment X" with descriptive titles)
   - 3-5 key insights extracted from the content
   - An engaging story-like summary that captures the essence
   - 2-3 actionable takeaways if applicable
   - Notable quotes if any stand out

IMPORTANT GUIDELINES:
- Create segment names that reflect actual content themes
- Make summaries engaging and narrative-driven, not just bullet points
- Focus on value extraction - what would viewers find most useful?
- Maintain accuracy while making content accessible and interesting
- If using chunking, ensure the final analysis feels cohesive, not fragmented

Be intelligent about processing decisions and always aim for high-quality insights."""

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