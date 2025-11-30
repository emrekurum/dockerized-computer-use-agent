import json
import platform
from datetime import datetime
from typing import Any, cast, Literal
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from anthropic import Anthropic, APIError, APIResponseValidationError, APIStatusError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from computer_use_demo.tools import (
    TOOL_GROUPS_BY_VERSION,
    ToolCollection,
    ToolResult,
    ToolVersion,
)

# Constants from loop.py
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open firefox, please just click on the firefox icon.  Note, firefox-esr is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_based_edit_tool or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date is {datetime.today().strftime("%A, %B %d, %Y")}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your str_replace_based_edit_tool.
</IMPORTANT>"""

def _response_to_params(response: BetaMessage) -> list[BetaContentBlockParam]:
    res: list[BetaContentBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            if block.text:
                res.append(BetaTextBlockParam(type="text", text=block.text))
            elif getattr(block, "type", None) == "thinking":
                 # Handle thinking blocks if present
                thinking_block = {
                    "type": "thinking",
                    "thinking": getattr(block, "thinking", None),
                }
                if hasattr(block, "signature"):
                    thinking_block["signature"] = getattr(block, "signature", None)
                res.append(cast(BetaContentBlockParam, thinking_block))
        else:
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    tool_result_content: list[Any] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }

def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text

async def run_agent(session_id: str, input_text: str, chat_history: list):
    """
    Async generator that runs the agent loop.
    Yields dictionary events for the WebSocket.
    """
    # 1. Initialize Client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        yield {"type": "error", "content": "ANTHROPIC_API_KEY not found."}
        return

    client = Anthropic(api_key=api_key)
    
    # 2. Setup Tools
    # Using a default tool version, explicitly typed as ToolVersion literal
    tool_version: ToolVersion = "computer_use_20250124"
    tool_group = TOOL_GROUPS_BY_VERSION[tool_version]
    tool_collection = ToolCollection(*tool_group.tools)
    
    # 3. Prepare Messages
    messages: list[BetaMessageParam] = []
    
    # Reconstruct history
    for msg in chat_history:
        # msg is expected to be the SQLAlchemy model or Pydantic schema
        role = msg.role
        content_str = msg.content
        
        # Try to parse content as JSON, if it fails, treat as plain text
        try:
            content = json.loads(content_str)
        except (json.JSONDecodeError, TypeError):
            content = content_str
            
        # Map "tool" role from DB to "user" role with tool_result content for Anthropic
        if role == "tool":
             messages.append({"role": "user", "content": content})
        else:
             messages.append({"role": role, "content": content})

    # Append the new user message
    messages.append({"role": "user", "content": input_text})
    
    # 4. Sampling Loop
    max_tokens = 4096
    system = BetaTextBlockParam(
        type="text",
        text=SYSTEM_PROMPT
    )
    
    # Beta flags
    betas = [tool_group.beta_flag] if tool_group.beta_flag else []
    betas.append(PROMPT_CACHING_BETA_FLAG)

    while True:
        try:
            # Call API
            raw_response = client.beta.messages.with_raw_response.create(
                max_tokens=max_tokens,
                messages=messages,
                model="claude-sonnet-4-20250514",
                system=[system],
                tools=tool_collection.to_params(),
                betas=betas,
            )
            
            response = raw_response.parse()
            
            # Add assistant response to messages
            response_params = _response_to_params(response)
            messages.append({
                "role": "assistant",
                "content": response_params,
            })
            
            # Serialize response params for DB saving
            yield {
                "type": "db_save",
                "role": "assistant",
                "content": json.dumps(response_params)
            }

            # Process content blocks
            tool_result_content: list[BetaToolResultBlockParam] = []
            
            for content_block in response_params:
                # BetaContentBlockParam is a union of TypedDicts or objects.
                # We cast to dict to safely access keys if it's a dict, or check isinstance.
                # But response_params comes from _response_to_params which returns a list of BetaContentBlockParam
                # which are TypedDicts (mostly).
                
                # Safe access via cast to dict
                block_dict = cast(dict[str, Any], content_block)
                block_type = block_dict.get("type")

                if block_type == "text":
                    text = block_dict.get("text", "")
                    yield {"type": "text", "content": text}
                elif block_type == "tool_use":
                    name = block_dict.get("name")
                    input_data = block_dict.get("input")
                    tool_id = block_dict.get("id")
                    
                    if not name or not tool_id:
                        continue

                    yield {
                        "type": "tool_use", 
                        "name": name, 
                        "input": input_data,
                        "id": tool_id
                    }
                    
                    # Execute Tool
                    result = await tool_collection.run(
                        name=name,
                        tool_input=cast(dict[str, Any], input_data or {}),
                    )
                    
                    api_tool_result = _make_api_tool_result(result, tool_id)
                    tool_result_content.append(api_tool_result)
                    
                    # Yield tool output
                    output_text = result.output if result.output else ""
                    if result.error:
                         output_text = f"Error: {result.error}\n{output_text}"
                    
                    yield {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": output_text,
                        "is_error": bool(result.error)
                    }
                    
                    if result.base64_image:
                         yield {
                             "type": "image",
                             "tool_use_id": tool_id,
                             "data": result.base64_image
                         }

            if not tool_result_content:
                break
            
            # Append tool results to messages (Role: user)
            messages.append({"content": tool_result_content, "role": "user"})
            
            # Serialize tool results for DB saving
            yield {
                "type": "db_save",
                "role": "tool",
                "content": json.dumps(tool_result_content)
            }

        except (APIStatusError, APIResponseValidationError) as e:
            yield {"type": "error", "content": f"API Error: {str(e)}"}
            return
        except APIError as e:
            yield {"type": "error", "content": f"Anthropic Error: {str(e)}"}
            return
        except Exception as e:
            yield {"type": "error", "content": f"Unexpected Error: {str(e)}"}
            return
