from urllib.parse import parse_qs, urlparse, unquote
from bs4 import BeautifulSoup

import requests
from lxml import html
from agent.LLM import *
from agent.Prompt import *


class StepEvaluator():
    def __init__(self):
        pass


class URLEvaluator(StepEvaluator):
    '''URL评测打分'''
    @staticmethod
    def url_exact_match(input_url, reference_answer, key=False):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = unquote(input_answer)
        result_score = MatchFunction.exact_match(input_answer, reference_answer)
        if result_score == 1:
            print("correct:", input_answer)
        return result_score

    @staticmethod
    def url_include_match(input_url, reference_answer, key=None):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = unquote(input_answer)
        result_score = MatchFunction.include_match(input_answer, reference_answer)
        print(result_score, input_answer, reference_answer)
        return result_score

    @staticmethod
    def url_semantic_match(input_url, reference_answer, key=False, semantic_method=None):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = unquote(input_answer)
        result_score = MatchFunction.semantic_match(input_answer, reference_answer, semantic_method)
        return result_score


class PathEvaluator(StepEvaluator):
    '''元素路径评测打分'''
    @staticmethod
    def path_exact_match(input_answer, reference_answer, method, html_content):
        score = 0
        if method == "xpath":
            try:
                tree = html.fromstring(html_content)
                input_elements = tree.xpath(input_answer)
                reference_elements = tree.xpath(reference_answer)
            except:
                score = 0
            if input_elements and reference_elements:
                score = input_elements[0] is reference_elements[0]
                try:
                    if reference_elements[0].tag == "span":
                        parent_element = reference_elements[0].getparent()
                        score_parent = input_elements[0] is parent_element
                        score = max(score, score_parent)
                except:
                    pass
            else:
                score = 0
        elif method == "selector":
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                input_element = soup.select_one(input_answer)
                reference_elements = soup.select_one(reference_answer)
                score = input_element is reference_elements

                try:
                    if reference_elements.name == "span":
                        parent_elements = reference_elements.parent
                        score_parent = input_element is parent_elements
                        score = max(score, score_parent)
                except:
                    pass
            except:
                score = 0
        # result_score = MatchFunction.include_match(
        #     input_answer, reference_answer)
        return score

    @staticmethod
    def path_included_match(input_answer, reference_answer, method, html_content):
        # TODO 路径包含
        result_score = MatchFunction.include_match(input_answer, reference_answer)
        return result_score

    @staticmethod
    def path_semantic_match(input_answer, reference_answer, method, html_content, semantic_method=None):
        result_score = MatchFunction.semantic_match(input_answer, reference_answer, semantic_method)
        return result_score


class TextEvaluator(StepEvaluator):
    '''文本评测打分'''
    @staticmethod
    def text_exact_match(input_answer, reference_answer):
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def text_included_match(input_answer, reference_answer):
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def text_semantic_match(input_answer, reference_answer, semantic_method=None):
        result_score = MatchFunction.semantic_match(
            input_answer, reference_answer, semantic_method)
        return result_score


class MatchFunction():
    def __init__(self):
        pass

    @staticmethod
    def exact_match(input_answer, reference_answer) -> int:
        return 1 if input_answer == reference_answer else 0

    @staticmethod
    def include_match(input_answer, reference_answer) -> int:
        return 1 if reference_answer in input_answer else 0

    @staticmethod
    def semantic_match(input_answer, reference_answer, semantic_method=None) -> int:
        GPT35 = GPTGenerator35()
        if semantic_method is None:
            pass # TODO 补全semantic match 默认method
        semantic_request = SemanticMatchPromptConstructor().construct(semantic_method)
        try: # 重试两次
            response = eval(GPT35.request(semantic_request))
            response = max(0, min(1, response)) # 将数字限定在0,1之间
        except:
            response = eval(GPT35.request(semantic_request))
            response = max(0, min(1, response)) # 将数字限定在0,1之间
        if response != 0 and response != 1:
            return round(response, 2)