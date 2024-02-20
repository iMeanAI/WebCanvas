from .openai import GPTGenerator35, GPTGenerator4, GPTGenerator4V, GPTGenerator4WithJSON, GPTGenerator35WithJSON


class LLMInstance:
    _gpt35 = None
    _gpt4 = None
    _gpt4v = None
    _gpt35json = None
    _gpt4json = None

    @staticmethod
    def get_gpt35():
        if LLMInstance._gpt35 is None:
            LLMInstance._gpt35 = GPTGenerator35()
        return LLMInstance._gpt35

    @staticmethod
    def get_gpt4():
        if LLMInstance._gpt4 is None:
            LLMInstance._gpt4 = GPTGenerator4()
        return LLMInstance._gpt4

    @staticmethod
    def get_gpt4v():
        if LLMInstance._gpt4v is None:
            LLMInstance._gpt4v = GPTGenerator4V()
        return LLMInstance._gpt4v

    @staticmethod
    def get_gpt35json():
        if LLMInstance._gpt35json is None:
            LLMInstance._gpt35json = GPTGenerator35WithJSON()
        return LLMInstance._gpt35json

    @staticmethod
    def get_gpt4json():
        if LLMInstance._gpt4json is None:
            LLMInstance._gpt4json = GPTGenerator4WithJSON()
        return LLMInstance._gpt4json


# 访问GPT生成器实例：
# gpt35_instance = LLMInstance.get_gpt35()
# gpt4_instance = LLMInstance.get_gpt4()
# gpt4v_instance = LLMInstance.get_gpt4v()
# gpt35json_instance = LLMInstance.get_gpt35json()
# gpt4json_instance = LLMInstance.get_gpt4json()


# _gpt35 = None
# _gpt4 = None
# _gpt4v = None
# _gpt35json = None
# _gpt4json = None
#
#
# def get_gpt35():
#     global _gpt35
#     if _gpt35 is None:
#         _gpt35 = GPTGenerator35()
#     return _gpt35
#
#
# def get_gpt4():
#     global _gpt4
#     if _gpt4 is None:
#         _gpt4 = GPTGenerator4()
#     return _gpt4
#
#
# def get_gpt4v():
#     global _gpt4v
#     if _gpt4v is None:
#         _gpt4v = GPTGenerator4V()
#     return _gpt4v
#
#
# def get_gpt35json():
#     global _gpt35json
#     if _gpt35json is None:
#         _gpt35json = GPTGenerator35WithJSON()
#     return _gpt35json
#
#
# def get_gpt4json():
#     global _gpt4json
#     if _gpt4json is None:
#         _gpt4json = GPTGenerator4WithJSON()
#     return _gpt4json
