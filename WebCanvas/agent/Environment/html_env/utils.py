from typing import TypedDict, List
from enum import IntEnum


class ElementNode(TypedDict):
    nodeId: int                 # Element ID
    childIds: List[int]         # List of child element IDs
    siblingId: int              # Sibling element ranking
    twinId: int                 # Same tag element ranking
    tagName: str                # Element
    attributes: dict            # Element attributes
    text: str                   # Text attribute
    parentId: int               # Parent element
    htmlContents: str           # All information of the element
    depth: int                  # Depth

TagNameList = [
    "button",
    "a",
    "input",
    "select",
    "textarea",
    "option",
    "datalist",
    "label",
    "div",
    "span",
    "p",
    "th",
    "tr",
    "td",
    "ul",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "filter-chip",
    "sup",
    "select-label",
    "optgroup"
]

MapTagNameList = [
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "div",
    "li",
    "ul",
    "p"
]

DelTagNameList = [
    "script",           # del
    "noscript",         # del
    "style",            # del
    "link",             # del
    "meta",             # del
]


ConditionTagNameList = [
    'span',
    'td',
    'th',
    'tr',
    'li',
    'div',
    'label',
    'filter-chip'
]


TypeList = [
    "submit"
]


def stringfy_selector(string: str):
    special_chars = '#.>+~[]():*^$|=%@!\''
    string = string.replace("\t", " ").replace("\n", " ").lstrip().rstrip()
    string = ' '.join(string.split())
    for char in special_chars:
        string = string.replace(char, '\\' + char)
    string = '.'.join(string.split(' '))
    if string[0].isdigit():
        string = f"\\{'{:X}'.format(ord(string[0]))}" + " " + string[1:]
    return string

def stringfy_value(string):
    special_chars = '#.>+~[]():*^$|=@\''
    for char in special_chars:
        string = string.replace(char, '\\' + char)
    return rf"{string}"

__all__ = [
    "ElementNode",
    "TagNameList",
    "DelTagNameList",
    "ConditionTagNameList",
    "TypeList",
    "stringfy_selector",
    "stringfy_value"
]
