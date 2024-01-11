import json5





def extract_longest_substring(s):
    start = s.find('{')  # Find the first occurrence of '['
    end = s.rfind('}')  # Find the last occurrence of ']'
    # Check if '[' and ']' were found and if they are in the right order
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]  # Return the longest substring
    else:
        return None  # Return None if no valid substring was found



