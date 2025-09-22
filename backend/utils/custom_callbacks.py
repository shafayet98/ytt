from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class CleanToolCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler that shows only clean tool invocation messages
    without the massive data dumps
    """
    
    def __init__(self, show_input: bool = True, show_timing: bool = False):
        """
        Initialize the callback handler
        
        Args:
            show_input: Whether to show tool input parameters
            show_timing: Whether to show timing information
        """
        super().__init__()
        self.show_input = show_input
        self.show_timing = show_timing
        self.tool_start_time = None
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts running"""
        if self.show_timing:
            self.tool_start_time = datetime.now()
        
        tool_name = serialized.get("name", "Unknown Tool")
        
        if self.show_input:
            # Clean and format the input
            cleaned_input = self._clean_input(input_str)
            print(f"🔧 Invoking: `{tool_name}` with `{cleaned_input}`")
        else:
            print(f"🔧 Invoking: `{tool_name}`")
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes running"""
        if self.show_timing and self.tool_start_time:
            duration = datetime.now() - self.tool_start_time
            print(f"   ✅ Completed in {duration.total_seconds():.2f}s")
        else:
            print(f"   ✅ Completed")
    
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """Called when a tool encounters an error"""
        print(f"   ❌ Error: {str(error)[:100]}{'...' if len(str(error)) > 100 else ''}")
    
    def on_agent_action(self, action, **kwargs) -> None:
        """Called when agent decides to use a tool - handled in on_tool_start"""
        pass
    
    def on_agent_finish(self, finish, **kwargs) -> None:
        """Called when agent finishes"""
        print(f"🏁 Agent completed")
    
    def _clean_input(self, input_str: str) -> str:
        """
        Clean and truncate input for display
        """
        try:
            # Try to parse as JSON
            if isinstance(input_str, str) and input_str.strip().startswith('{'):
                input_data = json.loads(input_str)
                cleaned_input = {}
                
                for key, value in input_data.items():
                    if isinstance(value, str):
                        # Truncate long strings
                        if len(value) > 50:
                            cleaned_input[key] = f"{value[:50]}..."
                        else:
                            cleaned_input[key] = value
                    elif isinstance(value, list):
                        # Show list length instead of full content
                        cleaned_input[key] = f"[{len(value)} items]"
                    elif isinstance(value, dict):
                        # Show dict keys instead of full content
                        cleaned_input[key] = f"{{...{len(value)} keys...}}"
                    else:
                        cleaned_input[key] = value
                
                return json.dumps(cleaned_input, separators=(',', ':'))
            else:
                # Not JSON, just truncate if too long
                return input_str[:100] + "..." if len(input_str) > 100 else input_str
                
        except json.JSONDecodeError:
            # If JSON parsing fails, just truncate
            return input_str[:100] + "..." if len(input_str) > 100 else input_str


class MinimalCallbackHandler(BaseCallbackHandler):
    """
    Ultra-minimal callback handler - shows only tool names
    """
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        tool_name = serialized.get("name", "Unknown Tool")
        print(f"🔧 {tool_name}")
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        print(f"   ✅")
    
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        print(f"   ❌")


class DetailedCallbackHandler(BaseCallbackHandler):
    """
    Detailed callback handler for debugging
    """
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        tool_name = serialized.get("name", "Unknown Tool")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔧 Starting: {tool_name}")
        print(f"           Input: {input_str[:200]}{'...' if len(input_str) > 200 else ''}")
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Try to parse output and show summary
        try:
            if isinstance(output, str) and output.strip().startswith('{'):
                output_data = json.loads(output)
                if isinstance(output_data, dict):
                    summary = {}
                    for key, value in output_data.items():
                        if key == "success":
                            summary[key] = value
                        elif isinstance(value, list):
                            summary[key] = f"{len(value)} items"
                        elif isinstance(value, str) and len(value) > 50:
                            summary[key] = f"{value[:50]}..."
                        else:
                            summary[key] = value
                    print(f"[{timestamp}] ✅ Result: {json.dumps(summary, separators=(',', ':'))}")
                else:
                    print(f"[{timestamp}] ✅ Completed")
            else:
                print(f"[{timestamp}] ✅ Completed")
        except:
            print(f"[{timestamp}] ✅ Completed")
    
    def on_tool_error(self, error: Exception, **kwargs) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ Error: {str(error)}")
