import json
from typing import Union, List, Dict, Tuple, Optional

import toml

def read_config(toml_path: Optional[str] = None) -> Dict:
    """Read configuration from TOML file.
    
    Args:
        toml_path: Path to the TOML config file. Defaults to 'configs/setting.toml'
        
    Returns:
        Dict containing configuration data
    """
    if toml_path is None:
        toml_path = 'configs/setting.toml'
    with open(toml_path, 'r') as f:
        config = toml.load(f)
    return config

def is_model_supported(model_name: str) -> bool:
    """Check if the model is supported in the configuration.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        bool indicating whether the model is supported
    """
    try:
        config = read_config()
        return model_name in config["token_pricing"]["pricing_models"]
    except:
        return False

def estimate_tokens(text: str) -> float:
    """Estimate the number of tokens for a given text.
    
    Args:
        text: Input text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    return len(text) / 4.8

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to fit within the maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        
    Returns:
        Truncated text
    """
    return text[:max_length]

def process_content(
    content: Union[str, List[Dict]], 
    remaining_tokens: float
) -> Tuple[Union[str, List[Dict]], float]:
    """Process and possibly truncate content based on remaining token allowance.
    
    Args:
        content: Content to process (either string or list of content items)
        remaining_tokens: Number of tokens remaining
        
    Returns:
        Tuple of (processed content, tokens used)
    """
    if isinstance(content, list):
        truncated_content = []
        used_tokens = 0
        
        for item in content:
            if item['type'] == 'text':
                item_text = item['text']
                item_tokens = estimate_tokens(item_text)
                
                if used_tokens + item_tokens > remaining_tokens:
                    max_length = int((remaining_tokens - used_tokens) * 4.8)
                    truncated_text = truncate_text(item_text, max_length)
                    truncated_content.append({'type': 'text', 'text': truncated_text})
                    used_tokens += estimate_tokens(truncated_text)
                    break
                    
                truncated_content.append(item)
                used_tokens += item_tokens
                
        return truncated_content, used_tokens
    else:
        # Simple text content
        tokens = estimate_tokens(content)
        if tokens > remaining_tokens:
            truncated_content = truncate_text(content, int(remaining_tokens * 4.8))
            return truncated_content, estimate_tokens(truncated_content)
        return content, tokens

def truncate_messages_based_on_estimated_tokens(
    messages: List[Dict], 
    max_tokens: int
) -> List[Dict]:
    """Truncate a list of messages based on an estimated token limit.
    
    Args:
        messages: List of message dictionaries to process
        max_tokens: Maximum number of tokens allowed
        
    Returns:
        List of truncated messages
    """
    current_tokens = 0
    truncated_messages = []

    for message in messages:
        content = message['content']
        processed_content, used_tokens = process_content(content, max_tokens - current_tokens)
        
        if used_tokens > 0:
            truncated_messages.append({
                'role': message['role'], 
                'content': processed_content
            })
            current_tokens += used_tokens
            
        if current_tokens >= max_tokens:
            break

    return truncated_messages
