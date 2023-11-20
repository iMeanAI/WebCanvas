from typing import TypedDict

class ElementNode(TypedDict):
    nodeId: int
    childIds: list[int]
    siblingId: int
    tagName: str
    attributes: str
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
    "textbox",
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

__all__ = [
    "ElementNode",
    "TagNameList",
    "DelTagNameList"
]