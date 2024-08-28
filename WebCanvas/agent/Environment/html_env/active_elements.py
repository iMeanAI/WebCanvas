from .utils import ElementNode, ConditionTagNameList, TypeList
import re


class ActiveElements:
    @staticmethod
    def is_visiable(element: ElementNode, only_child_check=True):
        style = element["attributes"].get('style')
        if style and ('display: none' in style or 'opacity: 0' in style):
            return False
        aria_hidden = element["attributes"].get('aria-hidden')
        if aria_hidden == 'true':
            return False
        if only_child_check:
            visibility = element["attributes"].get('style')
            if visibility and ('visibility: hidden' in visibility or 'visibility: collapse' in visibility):
                return False
            rect = element["attributes"].get('rect')
            if rect and (rect['width'] == 0 or rect['height'] == 0):
                return False
        return True

    @staticmethod
    def is_interactive(element: ElementNode):
        if element is None:
            return False
        tag = ActiveElements.get_element_tagName(element)
        if tag == 'input' and element["attributes"].get('type') == 'hidden':
            return False
        if tag in ['select', 'option'] and element["attributes"].get('disabled'):
            return False
        if tag in ['input', 'textarea', 'button', 'a'] and element["attributes"].get('disabled'):
            return False
        return True

    @staticmethod
    def get_element_tagName(element: ElementNode) -> str:
        tag_name = element["tagName"].lower()
        if tag_name == 'input':
            input_type = element["attributes"].get('type')
            if input_type == 'checkbox':
                return 'checkbox'
            elif input_type == 'radio':
                return 'radio'
            elif input_type == 'button':
                return 'button'
            else:
                return 'input'
        elif tag_name == 'select':
            return 'select'
        elif tag_name == 'optgroup':
            return 'optgroup'
        elif tag_name == 'textarea':
            return 'textarea'
        elif tag_name == 'option':
            return 'option'
        elif tag_name == 'datalist':
            return 'datalist'
        # elif tag_name == 'label':
        #     return 'label'
        elif tag_name == 'button':
            return 'button'
        elif tag_name == 'a':
            return 'link'
        elif tag_name in ConditionTagNameList:
            role = element["attributes"].get('role')
            if not role:
                return 'unknown'
            elif role == 'button':
                return 'button'
            elif role == 'link':
                return 'link'
            elif role == 'menuitem':
                return 'link'
            elif role == 'textbox':
                return 'input'
            elif role == 'checkbox':
                return 'checkbox'
            elif role == 'radio':
                return 'radio'
            elif role == 'tab':
                return 'link'
            elif role == 'switch':
                return 'switch'
            elif role == 'option':
                return 'option'
            elif role == 'row':
                return 'row'
            elif role == 'search-box':
                return 'search-box'
            else:
                return 'unknown'
        else:
            return 'unknown'

    @staticmethod
    def is_valid_element(element: ElementNode) -> bool:
        return ActiveElements.is_interactive(element) and ActiveElements.is_visiable(element)

    @staticmethod
    def get_element_value(element: ElementNode) -> str:
        if element["text"] and element["text"] != "":
            return element["text"]
        title = element['attributes'].get('title')
        if title:
            return title
        placeholder = element['attributes'].get('placeholder')
        if placeholder:
            return placeholder
        aria_label = element['attributes'].get('aria-label')
        if aria_label:
            return aria_label
        aria_checked = element['attributes'].get('aria-checked')
        if aria_checked:
            return aria_checked
        element_type = element["attributes"].get('type')
        if element_type in TypeList:
            return element_type
        if element["tagName"] == "select":
            return "Select an option value"
        return ""
