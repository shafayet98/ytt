from re import T
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor  
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import OPENAI_API_KEY, DEFAULT_MODEL
from tools import text_splitter, process_chunks_parallel

from utils.custom_callbacks import CleanToolCallbackHandler, MinimalCallbackHandler, DetailedCallbackHandler

from pydantic import BaseModel, Field
from typing import List, Optional

# =============================== STRUCTURED OUTPUT MODELS ===============================

class SegmentAnalysis(BaseModel):
    """Structured output model for segment analysis"""
    segment_number: int = Field(description="The segment number (1, 2, 3, etc.)")
    segment_name: str = Field(description="Meaningful, descriptive name for the segment based on content")
    summary: str = Field(description="Engaging 2-3 sentence summary of the segment")
    key_insights: List[str] = Field(description="3-5 key insights extracted from the segment")
    actionable_takeaways: List[str] = Field(description="2-3 actionable takeaways for viewers")

class MultiSegmentAnalysis(BaseModel):
    """Container for multiple segment analyses"""
    segments: List[SegmentAnalysis] = Field(description="List of analyzed segments")
    total_segments: int = Field(description="Total number of segments processed")

# =============================== CALLBACK CONFIGURATION ===============================

def get_callbacks(level="clean"):
    """
    Get callback handlers based on verbosity level
    
    Args:
        level: "minimal", "clean", "detailed", or "none"
    """
    callback_options = {
        "minimal": [MinimalCallbackHandler()],
        "clean": [CleanToolCallbackHandler(show_input=True, show_timing=True)],
        "clean_no_input": [CleanToolCallbackHandler(show_input=False, show_timing=True)],
        "detailed": [DetailedCallbackHandler()],
        "none": []
    }
    return callback_options.get(level, callback_options["clean"])

# =============================== AGENT 2 ===============================

def create_insight_extraction_agent(callback_level="clean"):
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
    system_prompt = """You are InsightExtractionAgent. Your job is to:

    1. Process video segments to extract 3-5 key insights
    2. Create a meaningful segment name (not generic "Segment X")  
    3. Write an engaging 2-3 sentence summary
    4. Identify 2-3 actionable takeaways


    Be concise and intelligent in your processing decisions."""

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # Create the agent executor with configurable callbacks
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        callbacks=get_callbacks(callback_level),
        return_intermediate_steps=True
    )
    
    return agent_executor

def create_structured_insight_extractor():
    """
    Create a structured insight extractor that returns SegmentAnalysis objects
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    ).with_structured_output(SegmentAnalysis)
    
    return llm

def process_segment_with_structured_output(segment_data: dict, segment_number: int, callback_level: str = "clean") -> SegmentAnalysis:
    """
    Process a single segment and return structured analysis.
    IMPROVED VERSION: Always returns structured output, even for large segments (>40k tokens).
    
    Args:
        segment_data: Dictionary containing segment information
        segment_number: The segment number for identification
        
    Returns:
        SegmentAnalysis object with structured data
    """
    try:
        content = segment_data.get('content', '')
        estimated_tokens = segment_data.get('estimated_tokens', 0)
        
        if estimated_tokens > 40000:
            # IMPROVED: Use agent with tools, then force structured output
            agent = create_insight_extraction_agent(callback_level)
            
            # Step 1: Let agent process with tools
            input_text = f"""Process this large segment using your tools (text_splitter, process_chunks_parallel) if needed:
            
Segment {segment_number}: {segment_data}

After processing, provide:
1. A meaningful segment name based on content
2. An engaging 2-3 sentence summary
3. 3-5 key insights
4. 2-3 actionable takeaways"""
            
            agent_result = agent.invoke({"input": input_text})
            processed_content = agent_result['output']
            
            # Step 2: Force structured output using the processed content
            structured_llm = create_structured_insight_extractor()
            
            structured_prompt = f"""Based on this analysis of Segment {segment_number}, create structured output:

PROCESSED ANALYSIS:
{processed_content}

ORIGINAL SEGMENT DATA:
Duration: {segment_data.get('duration', 'Unknown')} seconds
Character Count: {segment_data.get('character_count', 0)}

Extract and structure the analysis into the required format."""

            result = structured_llm.invoke(structured_prompt)
            result.segment_number = segment_number
            return result
            
        else:
            # Small segments: Direct structured processing (unchanged)
            structured_llm = create_structured_insight_extractor()
            prompt = f"""Analyze this video segment and provide structured insights:

SEGMENT {segment_number} DATA:
Content: {content}
Duration: {segment_data.get('duration', 'Unknown')} seconds
Character Count: {segment_data.get('character_count', 0)}

Provide:
1. A meaningful segment name based on the actual content (not generic "Segment X")
2. An engaging 2-3 sentence summary
3. 3-5 key insights from the content
4. 2-3 actionable takeaways for viewers

Focus on extracting valuable, specific insights rather than generic statements."""

            result = structured_llm.invoke(prompt)
            result.segment_number = segment_number
            return result
            
    except Exception as e:
        # Return a fallback structured response
        return SegmentAnalysis(
            segment_number=segment_number,
            segment_name=f"Segment {segment_number} (Processing Error)",
            summary=f"Error processing segment: {str(e)}",
            key_insights=["Processing error occurred"],
            actionable_takeaways=["Review segment processing"]
        )

def parse_agent_output_to_structured(output_text: str, segment_number: int) -> SegmentAnalysis:
    """
    Parse agent text output into structured format (fallback method)
    """
    try:
        # Simple parsing logic - this is a fallback
        lines = output_text.split('\n')
        
        segment_name = f"Segment {segment_number}"
        summary = "Analysis completed using agent tools."
        insights = ["Complex processing completed"]
        takeaways = ["Review detailed analysis"]
        
        # Try to extract information from the text
        for line in lines:
            if "segment name:" in line.lower() or "name:" in line.lower():
                segment_name = line.split(":")[-1].strip()
            elif "summary:" in line.lower():
                summary = line.split(":")[-1].strip()
        
        return SegmentAnalysis(
            segment_number=segment_number,
            segment_name=segment_name,
            summary=summary,
            key_insights=insights,
            actionable_takeaways=takeaways
        )
        
    except Exception:
        return SegmentAnalysis(
            segment_number=segment_number,
            segment_name=f"Segment {segment_number}",
            summary="Analysis completed.",
            key_insights=["Processing completed"],
            actionable_takeaways=["Review analysis"]
        )

def get_structured_analysis_summary(structured_result: MultiSegmentAnalysis) -> dict:
    """
    Convert structured analysis to a summary dictionary for easy access
    """
    return {
        "total_segments": structured_result.total_segments,
        "segments": [
            {
                "segment_number": seg.segment_number,
                "segment_name": seg.segment_name,
                "summary": seg.summary,
                "key_insights": seg.key_insights,
                "actionable_takeaways": seg.actionable_takeaways
            }
            for seg in structured_result.segments
        ]
    }