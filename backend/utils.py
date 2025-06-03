
# Here we target the Golf of specification
# we are creating a bridge between us: developer and the llm pipeline

# To be succesfull our prompt should be detailed and data specific and follow this six steps

# role
# instructions
# context
# examples
# output
# delimeters and structure

import litellm  # type: ignore
import os
from typing import Final, Dict, List

## set ENV variables
from dotenv import load_dotenv

load_dotenv(override=False)

response = litellm.completion(
  model="anthropic/claude-3-sonnet-20240229",
  messages=[{ "content": "Hello, how are you?","role": "user"}]
)

SYSTEM_PROMPT: Final[str] = """
### Role ###
You're a helpful football scouting analyst.
### Instructions ###
Provide detailed specifications about players based on the user query.
Your responses should be concise, informative, and relevant to the query.
### output ###
Your output should be in markdown format, structured with headings and bullet points where appropriate.
"""

# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = os.environ.get("MODEL_NAME", "anthropic/claude-3-haiku-20240307")

def get_agent_response(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Generate a response from the LLM based on the provided messages.
    
    Args:
        messages (List[Dict[str, str]]): A list of message dictionaries with 'role' and 'content'.
        
    Returns:
        List[Dict[str, str]]: The response from the LLM.
    """
    # litellm is model-agnostic; we only need to supply the model name and key.
    # The first message is assumed to be the system prompt if not explicitly provided
    # or if the history is empty. We'll ensure the system prompt is always first.
    current_messages: List[Dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    completion = litellm.completion(
        model=MODEL_NAME,
        messages=current_messages
    )

    assistant_reply_content: str = (
        completion["choices"][0]["message"]["content"] # type: ignore
        .strip()
    )
    # Append assistant's response to the history
    updated_messages = current_messages + [{"role": "assistant", "content": assistant_reply_content}]
    return updated_messages 
