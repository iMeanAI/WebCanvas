# from ..base_trace import BaseTrace
# from ..base_qa import BaseConversation

from typing import Dict
import openai
import json
import os


class ReferenceTrace:

    def __init__(
        self,
        file_path: str,
        top_k, int=1
    ) -> None:

        self.file_path = file_path
        self.top_k = top_k

    # @staticmethod
    # def get_ref_trace_by_user_request(file_path: str, user_request: str) -> Dict[str, float]:
    #     similarity_scores = {}
    #     with open(file_path, "r", encoding="utf-8") as f:
    #         local_trace = json.loads(f.read())
    #         local_trace = ReferenceTrace().trace_process(local_trace)
    #         for idx, trace in enumerate(local_trace):
    #             # 取出相应的元素比如trace,request
    #             request = ""
    #             score = ReferenceTrace().calculate_similarity(user_request, request)
    #             similarity_scores[str(idx) + request] = score
    #     return similarity_scores

    # @staticmethod
    # def get_ref_trace_by_similar_trace(file_path: str, current_trace: str) -> Dict[str, float]:
    #     similarity_scores = {}
    #     with open(file_path, "r", encoding="utf-8") as f:
    #         # local_trace是base_qa保存的内容
    #         local_trace = json.loads(f.read())
    #         local_trace = ReferenceTrace().trace_process(local_trace)
    #         for idx, trace in enumerate(local_trace):
    #             # 取出相应的元素比如trace
    #             ##
    #             # 需要处理
    #             score = ReferenceTrace().calculate_similarity(current_trace, trace)
    #             #
    #             similarity_scores[str(idx) + trace] = score
    #     return similarity_scores

    # @staticmethod
    # def trace_process(local_trace: str):
    #     """
    #     """
    #     pass

    @staticmethod
    def calculate_similarity(text: str, reference_text: str) -> float:
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"评估以下两段文本的相似性：\n{text}\n{reference_text}\n \
            并给出相似度分数，以下是一个固定的格式输出的例子，例如：{text}和{reference_text}的相似度分数为0.3",
            max_tokens=50
        )
        print(response)
        print(response.choices[0].text)
        similarity_score = response.choices[0].text.strip()
        return similarity_score 

    # def get_topK_by_similar_trace(self, current_trace) -> BaseTrace:
    #     similarity_scores = self.get_similar_reference_trace(
    #         self.file_path, current_trace)
    #     sorted_similar_trace = sorted(
    #         similarity_scores.items(), key=lambda x: x[1], reverse=True)
    #     topK_trace = sorted_similar_trace[:self.top_k]
    #     ### 最后的处理 #######
    #     ###           #######
    #     return topK_trace

    # def get_topK_by_user_request(self, user_request) -> BaseTrace:
    #     similarity_scores = self.get_similar_reference_trace(
    #         self.file_path, user_request)
    #     sorted_similar_trace = sorted(
    #         similarity_scores.items(), key=lambda x: x[1], reverse=True)
    #     topK_trace = sorted_similar_trace[:self.top_k]
    #     ### 最后的处理 #######
    #     ###           #######
    #     return topK_trace


if __name__ == "__main__":
    score = ReferenceTrace.calculate_similarity("你好", "您好")
    print(score)
