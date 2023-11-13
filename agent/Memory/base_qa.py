from .base_trace import BaseTrace
import time
import os


class BaseConversation:

    def __init__(
        self,
        status: str,
        user_request: str,
        current_trace: BaseTrace
    ):
        self.status = status
        self.user_request = user_request
        self.current_trace = current_trace

    def is_finish(self):

        return self.status == "Finish"



    def save_request_and_trace(self,file_path):
        """
        """
        # if self.is_finish():
        #     with open(file_path,encoding='utf-8') as f:
        #         f.write("")
        pass


        
         

    

    