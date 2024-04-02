import logging
import pandas as pd
import os
from datetime import datetime
import re


def write_result_to_excel(
    task_name,
    task_id,
    task_name_id,
    task_finished,
    task_global_status,
    step_index_list,
    score_list,
    step_reward_list,
    dict_result_list,
    url_list,
    current_trace_list,
    previous_trace_list,
    selector_list,
    action_list,
    match_func_result_list,
    element_value_list,
    error_message_list,
    invalid_vision_reward_num,
    file_path="",
):

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    print("task_name len: ", len(step_index_list))
    print("step_index_list len: ", len(step_index_list))
    print("score_list len: ", len(score_list))
    print("step_reward_list len: ", len(step_reward_list))
    print("dict_result_list len: ", len(dict_result_list))
    print("url_list len: ", len(url_list))
    print("current_trace_list len: ", len(current_trace_list))
    print("previous_trace_list len: ", len(previous_trace_list))
    print("selector_list len: ", len(selector_list))
    print("action_list len: ", len(action_list))
    print("element_value_list len", len(element_value_list))
    print("error_message_list len", len(error_message_list))
    print("invalid_vision_reward_num: ", invalid_vision_reward_num)

    if task_finished:
        url_list.append("finished")
        step_reward_list.append("finished")
        previous_trace_list.append("finished")
        error_message_list.append(" ")

    # cleaned_task_name = re.sub(r'[\\/:*?"<>|]', '', task_name)

    csv_path = ""

    if task_finished:
        csv_path = file_path + "/" +\
            str(task_id) + "_" + task_name_id + "_" + "finished" + "_" + ".csv"
    else:
        csv_path = file_path + "/" +\
            str(task_id) + "_" + task_name_id + "_" + "step_limit" + "_" + ".csv"
        if task_global_status == "finished":
            csv_path = file_path + "/" +\
                str(task_id) + "_" + task_name_id + "_" + "llm_finished" + "_" + ".csv"

    df = pd.DataFrame({
        "step_index": step_index_list,
        "score": score_list,
        "step_reward": step_reward_list,
        "dict_result_list": dict_result_list,
        "step url": url_list,
        "trace": current_trace_list,
        "previous_trace": previous_trace_list,
        "selector": selector_list,
        "action": action_list,
        "match_result": match_func_result_list,
        "element_value": element_value_list,
        "error": error_message_list
    })

    df.to_csv(csv_path)
