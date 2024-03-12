from typing import TypedDict, List
from enum import IntEnum


class ElementNode(TypedDict):
    nodeId: int                 # 元素编号
    childIds: List[int]         # 子元素编号列表
    siblingId: int              # 兄弟元素排名
    twinId: int                 # 相同tag元素排名
    tagName: str                # 元素
    attributes: dict            # 元素属性
    text: str                   # 文本属性
    parentId: int               # 父元素
    htmlContents: str           # 元素的所有信息
    depth: int                  # 深度


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
    "ul"
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


def stringfy_selector(string):
    string = string.replace("\t", " ").replace("\n", " ").lstrip().rstrip()
    string = ' '.join(string.split())
    string = string.replace("(", "\(").replace(")", "\)").replace(
        "[", "\[").replace("]", "\]")
    string = '.'.join(string.split(' '))
    return string


__all__ = [
    "ElementNode",
    "TagNameList",
    "DelTagNameList",
    "ConditionTagNameList",
    "TypeList",
    "stringfy_selector"
]
