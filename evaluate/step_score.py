import re
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
            print("url_exactly_match:", input_answer)
        return result_score

    @staticmethod
    def url_include_match(input_url, reference_answer, key=None):
        print(input_url, reference_answer)
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
        print("score:", result_score, input_answer)
        return result_score

    @staticmethod
    def url_semantic_match(input_url, semantic_method, key=False):
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
        result_score = MatchFunction.semantic_match(input_answer, semantic_method)
        return result_score


class ElementEvaluator(StepEvaluator):
    '''元素评测打分'''
    @staticmethod
    def path_exact_match(input_answer, reference_answer, method, html_content,  input_netloc, reference_netloc):
        score = 0
        if method == "xpath":
            if reference_netloc != input_netloc:
                print("reference_netloc:", reference_netloc, "input_netloc:", input_netloc)
                return 0
            try:
                tree = html.fromstring(html_content)
                input_elements = tree.xpath(input_answer)
                reference_elements = tree.xpath(reference_answer)
            except:
                score = 0
            if (input_elements is not None) and (reference_elements is not None):
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
            if reference_netloc != input_netloc:
                print("reference_netloc:", reference_netloc, "input_netloc:", input_netloc)
                return 0
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                input_element = soup.select_one(input_answer)
                reference_element = soup.select_one(reference_answer)
                if (input_element is not None) and (reference_element is not None):
                    score = input_element is reference_element

                    try:
                        if reference_element.name == "span":
                            parent_elements = reference_element.parent
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
    def element_value_exact_match(input_answer, reference_answer, input_netloc, reference_netloc):
        if reference_netloc != input_netloc:
            print("reference_netloc:", reference_netloc, "input_netloc:", input_netloc)
            return 0
        result_score = MatchFunction.exact_match(input_answer, reference_answer)
        return result_score

    @staticmethod
    def element_value_include_match(input_answer, reference_answer, input_netloc, reference_netloc):
        if reference_netloc != input_netloc:
            print("reference_netloc:", reference_netloc, "input_netloc:", input_netloc)
            return 0
        result_score = MatchFunction.include_match(input_answer, reference_answer)
        return result_score

    @staticmethod
    def element_value_semantic_match(input_answer, semantic_method, input_netloc, reference_netloc=0):
        if reference_netloc != input_netloc:
            print("reference_netloc:", reference_netloc, "input_netloc:", input_netloc)
            return 0
        if len(input_answer) == 0:
            return 0
        result_score = MatchFunction.semantic_match(input_answer, semantic_method)
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
    def text_semantic_match(input_answer, semantic_method):
        result_score = MatchFunction.semantic_match(
            input_answer, semantic_method, semantic_method)
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
    async def semantic_match(input_answer, semantic_method) -> float:
        GPT35 = GPTGenerator35()
        semantic_request = SemanticMatchPromptConstructor().construct(input_answer, semantic_method)
        # print(f"\033[32m{semantic_request}")  # 绿色
        try:  # 重试两次
            response, _ = await GPT35.request(semantic_request)
            print(response)
            score = re.findall("```(.*?)```", response, re.S)[0]
            score = eval(score)
            score = max(0, min(1, score))  # 将数字限定在0,1之间
        except:
            response, _ = await GPT35.request(semantic_request)
            print(response)
            score = re.findall("```(.*?)```", response, re.S)[0]
            score = eval(score)
            score = max(0, min(1, score))  # 将数字限定在0,1之间
        if score != 0 and score != 1:
            print("semantic_method:", semantic_method, "input_answer:", input_answer, score)
            return round(score, 2)
        else:
            print("semantic_method:", semantic_method, "input_answer:", input_answer, score)
            return score
