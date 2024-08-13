import re
from urllib.parse import parse_qs, urlparse, unquote
from bs4 import BeautifulSoup

import requests
from lxml import html
from agent.LLM import *
from agent.Prompt import *
from agent.Environment.html_env.utils import MapTagNameList


class StepEvaluator():
    def __init__(self):
        pass


class URLEvaluator(StepEvaluator):
    '''URL Evaluation Scoring'''
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
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        # if result_score == 1:
        #     print("url_exactly_match:", input_answer)
        return result_score

    @staticmethod
    def url_include_match(input_url, reference_answer, key=None):
        # print(input_url, reference_answer)
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            try:
                parsed_url = urlparse(input_url)
                input_answer = parsed_url.netloc + parsed_url.path
                if parsed_url.fragment is not None and (parsed_url.fragment):
                    input_answer += "#" + parsed_url.fragment
            except:
                input_answer = input_url
        input_answer = unquote(input_answer)
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        # print("score:", result_score, input_answer)
        return result_score

    @staticmethod
    async def url_semantic_match(input_url, semantic_method, key=False):
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
        result_score = await MatchFunction.semantic_match(input_answer, semantic_method)
        return result_score


class ElementEvaluator(StepEvaluator):
    '''Element evaluation and scoring'''
    @staticmethod
    def path_exact_match(input_answer, reference_answer, method, html_content, input_netloc, reference_netloc):
        score = 0
        if method == "xpath":
            if reference_netloc != input_netloc:
                # print("reference_netloc:", reference_netloc,
                #       "input_netloc:", input_netloc)
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
                    if reference_elements[0].tag in MapTagNameList:
                        trace_up_count = 0
                        current_element = reference_elements[0]
                        while trace_up_count < 3 and score == 0:
                            trace_up_count += 1
                            current_element = current_element.getparent()
                            score_parent = input_elements[0] is current_element
                            score = max(score, score_parent)
                except:
                    pass
            else:
                score = 0
        elif method == "selector":
            if reference_netloc != input_netloc:
                # print("reference_netloc:", reference_netloc,
                #       "input_netloc:", input_netloc)
                return 0
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                input_element = soup.select_one(input_answer)
                reference_element = soup.select_one(reference_answer)
                if (input_element is not None) and (reference_element is not None):
                    score = input_element is reference_element

                    try:
                        if reference_element.name in MapTagNameList:
                            # parent_elements = reference_element.parent
                            # score_parent = input_element is parent_elements
                            # score = max(score, score_parent)
                            trace_up_count = 0
                            current_element = reference_element
                            while trace_up_count < 3 and score == 0:
                                trace_up_count += 1
                                current_element = current_element.parent
                                score_parent = input_element is current_element
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
        # TODO Add path inclusion matching method
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def element_value_exact_match(input_answer, reference_answer, input_netloc, reference_netloc):
        if reference_netloc != input_netloc:
            # print("reference_netloc:", reference_netloc,
            #       "input_netloc:", input_netloc)
            return 0
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def element_value_include_match(input_answer, reference_answer, input_netloc, reference_netloc):
        if reference_netloc != input_netloc:
            # print("reference_netloc:", reference_netloc,
            #       "input_netloc:", input_netloc)
            return 0
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    async def element_value_semantic_match(input_answer, semantic_method, input_netloc, reference_netloc=0):
        if reference_netloc != input_netloc:
            # print("reference_netloc:", reference_netloc,
            #       "input_netloc:", input_netloc)
            return 0
        if len(input_answer) == 0:
            return 0
        result_score = await MatchFunction.semantic_match(input_answer, semantic_method)
        return result_score


class TextEvaluator(StepEvaluator):
    '''Text evaluation and scoring'''
    @staticmethod
    def text_exact_match(input_answer, reference_answer):
        input_answer = input_answer.lower()
        reference_answer = reference_answer.lower()
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def text_included_match(input_answer, reference_answer):
        input_answer = input_answer.lower()
        reference_answer = reference_answer.lower()
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def text_semantic_match(input_answer, semantic_method):
        result_score = MatchFunction.semantic_match(
            input_answer, semantic_method)
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
        # GPT35 = GPTGenerator(model="gpt-3.5-turbo")
        semantic_request = SemanticMatchPromptConstructor(
        ).construct(input_answer, semantic_method)
        score = None
        for i in range(3):
            try:
                # response, _ = await GPT35.request(semantic_request)
                response, _ = await semantic_match_llm_request(semantic_request)
                score = re.findall("```(.*?)```", response, re.S)[0]
                score = eval(score)
                # Limit the score between 0 and 1
                score = max(0, min(1, score))
                if score != None:
                    break
            except:
                score = None
        if score == None:
            score = 0
        if score != 0 and score != 1:
            return round(score, 2)
        else:
            return score
