import logging

def setup_logging():
    """Configure logging for the entire application"""
    # Suppress verbose LangChain output
    logging.getLogger("langchain").setLevel(logging.WARNING)
    
    # You can also configure your own app logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )