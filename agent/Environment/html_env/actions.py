from beartype import beartype
from typing import TypedDict
from enum import IntEnum


class Action(TypedDict):
    action_type: int
    element_id: int
    element_name: str
    url: str
    fill_text: str


class ActionTypes(IntEnum):
    NONE = 0
    CLICK = 1
    GOTO = 2
    GOOGLE_SEARCH = 3
    FILL_FORM = 4
    SWITCH_TAB = 5


@beartype
def create_click_action(elementid: int) -> Action:
    return {
        "action_type": ActionTypes.CLICK,
        "element_id": elementid,
        "url": "",
        "fill_text": "",
        "element_name": ""
    }


@beartype
def create_goto_action(elementid: int, url: str) -> Action:
    return {
        "action_type": ActionTypes.GOTO,
        "element_id": elementid,
        "url": url,
        "fill_text": "",
        "element_name": ""
    }


@beartype
def create_none_action(elementid: int) -> Action:
    return {
        "action_type": ActionTypes.NONE,
        "element_id": elementid,
        "url": "",
        "fill_text": "",
        "element_name": ""
    }


@beartype
def create_fill_action(elementid: int, fill_text: str) -> Action:
    return {
        "action_type": ActionTypes.FILL_FORM,
        "element_id": elementid,
        "url": "",
        "fill_text": fill_text,
        "element_name": ""
    }


@beartype
def create_search_action(elementid: int, text: str) -> Action:
    return {
        "action_type": ActionTypes.GOOGLE_SEARCH,
        "element_id": elementid,
        "url": "https://www.google.com",
        "fill_text": text
    }


@beartype
def create_action(elementid: int, action_type: str, action_input: str) -> Action:
    if action_type == "click":
        return create_click_action(elementid=elementid)
    elif action_type == "fill_form":
        return create_fill_action(elementid=elementid, fill_text=action_input)
    elif action_type == "goto":
        return create_goto_action(elementid=elementid, url=action_input)
    elif action_type == "google_search":
        return create_search_action(elementid=elementid, text=action_input)
    else:
        return create_none_action(elementid=elementid)


__all__ = [
    "Action",
    "ActionTypes",
    "create_click_action",
    "create_fill_action",
    "create_none_action",
    "create_goto_action",
    "create_search_action",
    "create_action"
]