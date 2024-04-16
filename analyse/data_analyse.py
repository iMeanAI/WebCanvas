import pandas as pd
import json5
import json
import re
import os


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

def to_dict(input_string):
    # 正则表达式模式
    # pattern = r"('action_type'|'element_id'|'url'|'fill_text'):\s*(<[^>]+>|\d+|'[^']+')"
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
    elif "goto" in extracted_fields["action_type"].lower():
        action = "goto" + "[" + extracted_fields["url"] + "]"
    elif "click" in extracted_fields["action_type"].lower():
        action = "click" + "[" + str(extracted_fields["element_id"]) + "]"
    elif "none" in extracted_fields["action_type"].lower():
        action = "None"
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
    if dict_str.lower() == "x":
        dict_str = {}
    elif dict_str.lower() == "finished":
        dict_str = {"score:": 10, "description": "finished"}
    else:
        dict_str = parse_step_reward(dict_str)
    return dict_str


def write_to_json(file_path):
    df = pd.read_csv(file_path, index_col=False)
    df = df.drop(df.columns[0], axis=1)
    df["step_index"] += 1
    df["trace_to_dict"] = df["trace"].apply(lambda x: parse_thought_action(x))
    df["action_to_str"] = df["action"].apply(lambda x: to_dict(x))
    df["score_rate"] = df["score"].apply(lambda x: score_rate(x))
    df["step_reward"] = df["step_reward"].apply(
        lambda x: process_step_reward(x))
    df["selector"] = df["selector"].fillna("None")
    df_copy = df[
        [
            "step_index",
            "trace_to_dict",
            "selector",
            "action_to_str",
            "score",
            "score_rate",
            "step_reward",
            "step url"
        ]
    ]

    def summary(x):
        dic = {
            "step_index": x["step_index"],
            "trace_description": x["trace_to_dict"] if x["trace_to_dict"] else {},
            "selector": x["selector"] if x["selector"] != "None" else "",
            "action": x["action_to_str"] if x["action_to_str"] else "",
            "task_score": x["score"],
            "task_score_rate": x["score_rate"],
            "current_reward_score_description": x["step_reward"],
            "url": x["step url"] if x["step url"] != "finished" else ""
        }
        return dic
    step_list = []
    df_copy.apply(lambda x: step_list.append(summary(x)), axis=1)
    return step_list


def read_file(file_path):
    '''读取标签数据'''
    return_list = []
    with open(file_path, encoding='gbk') as f:
        test_data = json5.load(f)
    for task in test_data:
        task_name = task["task"]
        return_list.append(task_name)
    return return_list

# --------------------------------------------

task_name_list = read_file(file_path="./data/data_update_0326/group_sample_all_data_0327.json")
print(task_name_list)

folder_path = './csv_results/group_sample_20240415/dom_20240415-170153'
task_list = []
for _, filename in enumerate(os.listdir(folder_path)):
    out_json = {}
    out_json["task_id"] = int(filename.split("_")[0])
    out_json["task_name"] = task_name_list[out_json["task_id"]]
    task_status = filename.split("_")[-2]
    out_json["task_status"] = task_status
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path):
        task_step_list = write_to_json(file_path)
        out_json["step_list"] = task_step_list
        task_list.append(out_json)
print(task_list)
task_list = sorted(task_list, key=lambda x: x['task_id'])
if not os.path.exists("./results/group_sample_20240415/dom_20240415-170153"):
    os.makedirs("./results/group_sample_20240415/dom_20240415-170153")
out_json_file_path = './results/group_sample_20240415/dom_20240415-170153/out.json'
with open(out_json_file_path, 'w') as json_file:
    json.dump(task_list, json_file)


def read_csv_result():
    with open('./results/group_sample_20240415/dom_20240415-170153/out.json') as f:
        data = json.load(f)
    last_action_result_list = []
    for items in data:
        data_dic = {}
        data_dic["task_id"] = items["task_id"]
        data_dic["task_name"] = items["task_name"]
        data_dic["status"] = items["task_status"]
        data_dic["steps"] = items["step_list"][-1]["step_index"]
        data_dic["task_score"] = items["step_list"][-1]["task_score"]
        data_dic["task_score_rate"] = items["step_list"][-1]["task_score_rate"]
        data_dic["selector"] = items["step_list"][-1]["selector"]
        data_dic["action"] = items["step_list"][-1]["action"]
        data_dic["url"] = items["step_list"][-2]["url"]
        last_action_result_list.append(data_dic)
    # result_list = sorted(data,key=lambda x: x["step_list"]["task_score_rate"],reverse=True)
    return last_action_result_list


last_action_result_list = read_csv_result()
# last_action_result_list

df = pd.DataFrame(last_action_result_list)

# df["task_score_rate"].mean()
print("df['task_score_rate'].mean() :", df["task_score_rate"].mean())

df_score_limit = df[df["status"].apply(lambda x: x) == "limit"]
# df_score_limit
print("df_score_limit.shape[0] :", df_score_limit.shape[0])
print("df_score_limit.shape[0] / df.shape[0] :", df_score_limit.shape[0] / df.shape[0])


# Split the 'task_score' into two columns 'numerator' and 'denominator'
df[['numerator', 'denominator']] = df['task_score'].str.split(' / ', expand=True).astype(float)

# Calculate the sums
numerator_sum = df['numerator'].sum()
denominator_sum = df['denominator'].sum()

# Calculate the overall task score rate
overall_score_rate = numerator_sum / denominator_sum

print("numerator_sum :", numerator_sum)
print("denominator_sum :", denominator_sum)
print("overall_score_rate :", overall_score_rate)

df_score = df[df["task_score_rate"] == 1.0]
print(df_score.value_counts())

print("\nTask completion number: ", df_score.shape[0])
print("Task completion rate: ", df_score.shape[0] / df.shape[0])
