from urllib.parse import parse_qs, urlparse, quote


class StepEvaluator():
    def __init__(self, evaluate_function, value):
        pass


class URLEvaluator(StepEvaluator):
    '''URL评测打分'''
    @staticmethod
    def URL_exact_match(input_url, reference_answer, key=False):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = quote(input_answer)
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        if result_score == 1:
            print("correct:", input_answer)
        return result_score

    @staticmethod
    def URL_include_match(input_url, reference_answer, key=False):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = quote(input_answer)
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def URL_semantic_match(input_url, reference_answer, key=False, method=None):
        if key:
            try:
                parsed_url = urlparse(input_url)
                url_params = parse_qs(parsed_url.query)
                input_answer = url_params[key][0]
            except:
                return 0
        else:
            input_answer = input_url
        input_answer = quote(input_answer)
        result_score = MatchFunction.semantic_match(
            input_answer, reference_answer, method)
        return result_score


class PathEvaluator(StepEvaluator):
    '''元素路径评测打分'''
    @staticmethod
    def path_exact_match(input_answer, reference_answer):
        result_score = MatchFunction.exact_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def path_included_match(input_answer, reference_answer):
        result_score = MatchFunction.include_match(
            input_answer, reference_answer)
        return result_score

    @staticmethod
    def path_semantic_match(input_answer, reference_answer, method=None):
        result_score = MatchFunction.semantic_match(
            input_answer, reference_answer, method)
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
    def text_semantic_match(input_answer, reference_answer, method=None):
        result_score = MatchFunction.semantic_match(
            input_answer, reference_answer, method)
        return result_score


class MatchFunction():
    def __init__(self):
        pass

    @staticmethod
    def exact_match(input_answer, reference_answer) -> int:
        return 1 if input_answer == reference_answer else 0

    @staticmethod
    def include_match(input_answer, reference_answer) -> int:
        return 1 if input_answer in reference_answer else 0

    @staticmethod
    def semantic_match(input_answer, reference_answer, method=None) -> int:
        pass  # TODO 补全semantic match
