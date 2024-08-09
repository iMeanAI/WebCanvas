import pandas as pd
from pandas import json_normalize
import json5
import json
import re
import os
from logs import logger


def parse_thought_action(dict_str):
    thought_action = {}
    thought_match = re.search(r"'thought':\s*(.+?)\s*,\s*'action'", dict_str)
    action_match = re.search(r"'action':\s*(.+?)\s*}", dict_str)
    thought = thought_match.group(1) if thought_match else None
    thought = thought.replace("\\", "").replace("\"", "").replace("\'", "")
    action = action_match.group(1) if action_match else None
    action = action.replace("\\", "").replace("\"", "").replace("\'", "")
    thought_action = {"thought": thought, "action": action}
    return thought_action


def enum_to_action_str():
    action_types = [
        ("NONE", 0),
        ("CLICK", 1),
        ("GOTO", 2),
        ("GOOGLE_SEARCH", 3),
        ("FILL_FORM", 4),
        ("SWITCH_TAB", 5),
        ("GO_BACK", 6),
        ("FILL_SEARCH", 7),
        ("SELECT_OPTION", 8),
        ("HOVER", 9),
        ("SCROLL_DOWN", 10),
        ("SCROLL_UP", 11),
        ("CACHE_DATA", 12),
        ("GET_FINAL_ANSWER", 13)
    ]
    action_dict = {str(value): name for name,
    value in action_types if name.isupper()}
    return action_dict


def to_dict(input_string):
    pattern = r"('action_type'|'element_id'|'url'|'fill_text'):\s*(<[^>]+>|\d+|'[^']+'|\"[^\"]+\")"
    matches = re.findall(pattern, input_string)
    extracted_fields = {}
    for match in matches:
        field_name, field_value = match
        if field_value.startswith('<') and field_value.endswith('>'):
            enum_name = field_value.split('.')[-1].strip('<> ')
            extracted_fields[field_name.strip("'")] = enum_name
        else:
            extracted_fields[field_name.strip("'")] = field_value.strip("'")
    action_dict = enum_to_action_str()
    extracted_fields["action_type"] = action_dict[str(
        extracted_fields["action_type"])].lower()
    extracted_fields["fill_text"] = extracted_fields["fill_text"] if extracted_fields.get(
        "fill_text") else ""
    action = ""
    if "google_search" in extracted_fields["action_type"].lower():
        action = "google_search" + "[" + extracted_fields["fill_text"] + "]"
    elif "fill_search" in extracted_fields["action_type"].lower():
        action = "fill_search" + \
                 "[" + str(extracted_fields["element_id"]) + "," + \
                 extracted_fields["fill_text"] + "]"
    elif "fill_form" in extracted_fields["action_type"].lower():
        action = "fill_search" + \
                 "[" + str(extracted_fields["element_id"]) + "," + \
                 extracted_fields["fill_text"] + "]"
    elif "select_option" in extracted_fields["action_type"].lower():
        action = "select_option" + \
                 "[" + str(extracted_fields["element_id"]) + "," + \
                 extracted_fields["fill_text"] + "]"
    elif "goto" in extracted_fields["action_type"].lower() and extracted_fields.get('url'):
        action = "goto" + "[" + extracted_fields["url"] + "]"
    elif "click" in extracted_fields["action_type"].lower():
        action = "click" + "[" + str(extracted_fields["element_id"]) + "]"
    elif "go_back" in extracted_fields["action_type"].lower():
        action = "go_back" + "[" + str(extracted_fields["element_id"]) + "]"
    elif "none" in extracted_fields["action_type"].lower():
        action = "None"
    elif "cache_data" in extracted_fields["action_type"].lower():
        action = "cache_data" + "[" + extracted_fields["fill_text"] + "]"
    elif "final_answer" in extracted_fields["action_type"].lower():
        action = "get_final_answer" + "[" + extracted_fields["fill_text"] + "]"
    return action


def score_rate(score):
    first, second = score.split("/")
    return float(first) / float(second)


def parse_step_reward(dict_str):
    score_description = {}
    score_match = re.search(r"'score':\s*(.+?)\s*,\s*'description'", dict_str)
    description_match = re.search(r"'description':\s*(.+?)\s*}", dict_str)
    score = score_match.group(1) if score_match else None
    score = score.replace("\\", "").replace("\"", "").replace("\'", "")
    description = description_match.group(1) if description_match else None
    description = description.replace(
        "\\", "").replace("\"", "").replace("\'", "")
    score_description = {"score": score, "description": description}
    return score_description


def process_step_reward(dict_str):
    if dict_str.lower() == "{}":
        dict_str = {}
    elif dict_str.lower() == "finished":
        dict_str = {"score:": 10, "description": "finished"}
    else:
        dict_str = parse_step_reward(dict_str)
    return dict_str


def write_task_result_to_df(each_task_json_file_path):
    with open(each_task_json_file_path) as f:
        data = json.load(f)
    step_list = data["step_list"]
    task_name = data["task_name"]
    task_status = data["status"]
    reference_task_length = data["reference_task_length"]
    evaluate_steps = data["evaluate_steps"]
    for idx, item in enumerate(step_list):
        for key in item:
            step_list[idx][key] = str(step_list[idx][key])
    data_df = json_normalize(step_list, errors='ignore')
    return task_name, task_status, reference_task_length, evaluate_steps, data_df


def write_to_json(df):
    df["step_index"] = df["step_index"].apply(lambda x: int(x))
    df["trace_to_dict"] = df["current_trace"].apply(
        lambda x: parse_thought_action(x))
    df["action_to_str"] = df["execute_action"].apply(lambda x: to_dict(x))
    df["score_rate"] = df["score"].apply(lambda x: score_rate(x))
    df["step_reward"] = df["step_reward"].apply(
        lambda x: process_step_reward(x))
    df["selector"] = df["selector"].fillna("None")
    df["match_result"] = df["match_func_result"]
    df["element_value"] = df["element_value"].fillna("None")
    df["error"] = df["error_message"].fillna("None")
    df["step_url"] = df["step_url"].fillna("None")
    df_copy = df[
        [
            "step_index",
            "trace_to_dict",
            "selector",
            "action_to_str",
            "score",
            "score_rate",
            "step_reward",
            "step_url",
            "match_result",
            "element_value",
            "error"
        ]
    ]

    def summary(x):
        dic = {
            "step_index": x["step_index"],
            "trace_description": x["trace_to_dict"] if x["trace_to_dict"] else {},
            "selector": x["selector"] if x["selector"] != "None" else "",
            "element_value": x["element_value"] if x["element_value"] != "None" else "",
            "action": x["action_to_str"] if x["action_to_str"] else "",
            "task_score": x["score"],
            "task_score_rate": x["score_rate"],
            "current_reward_score_description": x["step_reward"],
            "url": x["step_url"],
            "match_result": x["match_result"],
            "error": x["error"] if x["error"] != "None" else ""
        }
        # print(dic["match_result"])
        return dic

    step_list = []
    df_copy.apply(lambda x: step_list.append(summary(x)), axis=1)
    return step_list


def get_result(input_json_path):
    json_result_path = input_json_path + "/json_result"
    out_file_path = input_json_path + "/result"
    task_list = []
    for _, filename in enumerate(os.listdir(json_result_path)):
        file_path = os.path.join(json_result_path, filename)
        out_json = {}
        task_name, task_status, reference_task_length, evaluate_steps, data_df = write_task_result_to_df(
            file_path)
        out_json["task_id"] = int(filename.split("_")[0])
        out_json["task_name"] = task_name
        out_json["task_status"] = task_status
        if os.path.isfile(file_path):
            task_step_list = write_to_json(data_df)
            out_json["step_list"] = task_step_list
            out_json["evaluation"] = evaluate_steps
            task_list.append(out_json)

    task_list = sorted(task_list, key=lambda x: x['task_id'])

    if not os.path.exists(out_file_path):
        os.makedirs(out_file_path)
    out_json_file_path = out_file_path + '/out.json'
    with open(out_json_file_path, 'w') as json_file:
        json.dump(task_list, json_file)
    return out_file_path


def read_json_result(file_path):
    with open(file_path) as f:
        data = json.load(f)
    last_action_result_list = []
    for items in data:
        data_dic = {}
        data_dic["task_id"] = items["task_id"]
        data_dic["task_name"] = items["task_name"]
        data_dic["status"] = items["task_status"]
        data_dic["steps"] = items["step_list"][-1]["step_index"] + 1
        data_dic["task_score"] = items["step_list"][-1]["task_score"]
        data_dic["task_score_rate"] = items["step_list"][-1]["task_score_rate"]
        data_dic["reward_count"] = len(items["evaluation"])
        last_action_result_list.append(data_dic)
    return last_action_result_list


def calculate_total_score(scores):
    molecular_sum = sum(float(x.split('/')[0]) for x in scores)
    denominator_sum = sum(float(x.split('/')[1]) for x in scores)
    final_score = molecular_sum / denominator_sum
    return final_score


def evaluate(file_path, total_token_cost):
    input_file_path = file_path + "/out.json"
    result_file_path = file_path + "/result.json"
    all_data = read_json_result(input_file_path)
    df = pd.DataFrame(all_data)
    df["step_score"] = df["task_score"].apply(lambda x: float(x.split("/")[0]))
    df["efficiency_score"] = [s / sc if sc != 0 else 0 for s, sc in zip(df['steps'], df['step_score'])]
    # The agent is only one key node away from completing the task
    df["task_near_success"] = df["task_score"].apply(lambda x: float(
        x.split("/")[1]) - float(x.split("/")[0]) == 1.0)

    df_evaluate = df[["task_name", "status", "steps", "task_score",
                      "task_score_rate", "step_score", "efficiency_score", "task_near_success"]]

    key_node_completion_rate = calculate_total_score(df_evaluate['task_score'])
    key_node_completion_sum = df_evaluate['step_score'].sum()
    task_success_rate = df_evaluate[df_evaluate["status"]
                                    == "finished"].shape[0] / df_evaluate.shape[0]
    task_near_success_rate = df_evaluate[df_evaluate["task_near_success"]
                                         == True].shape[0] / df_evaluate.shape[0]

    average_step_score_rate = df_evaluate["task_score_rate"].mean()
    average_efficiency_score = df_evaluate["efficiency_score"].mean()
    if total_token_cost != 0:
        usd_efficiency_score = total_token_cost / key_node_completion_sum

    result_dict = {}
    result_dict["task_counts"] = df_evaluate.shape[0]
    result_dict["average_step_score_rate"] = average_step_score_rate
    result_dict["average_efficiency_score"] = average_efficiency_score
    if total_token_cost != 0:
        result_dict["usd_efficiency_score"] = usd_efficiency_score
    result_dict["key_node_completion_rate"] = key_node_completion_rate
    result_dict["task_success_rate"] = task_success_rate
    result_dict["task_near_success_rate"] = task_near_success_rate

    with open(result_file_path, 'w') as json_file:
        json.dump(result_dict, json_file)

    logger.info(f'\033[31mAll results write to {result_file_path} !\033[0m')


def get_evaluate_result(input_result_path, total_token_cost):
    out_file_path = get_result(input_result_path)
    evaluate(file_path=out_file_path, total_token_cost=total_token_cost)
