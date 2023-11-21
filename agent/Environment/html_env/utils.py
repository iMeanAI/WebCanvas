from typing import TypedDict

class ElementNode(TypedDict):
    nodeId: int
    childIds: list[int]
    siblingId: int
    tagName: str
    attributes: dict
    text: str
    parentId: int
    htmlContents: str
    depth: int
    

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
    'div'
]



__all__ = [
    "ElementNode",
    "TagNameList",
    "DelTagNameList",
    "ConditionTagNameList"
]