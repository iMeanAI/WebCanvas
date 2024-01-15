from urllib.parse import unquote
from urllib.parse import parse_qs, urlparse
import json5

f = open("1.json", "r", encoding="utf-8")
json_file = json5.load(f)

output = []

for task in json_file:
    task_name = task["title"]
    evaluation = []
    print("task_name:", task_name)
    steps = task["steps"]
    reference_steps = len(steps)
    print("reference_steps:", reference_steps)
    for step in steps:
        if "rewardFunction" in step.keys() and len(step["rewardFunction"]) > 0:
            for func in step["rewardFunction"]:
                if len(func) == 0:
                    break
                temp = {}
                temp["match_function_name"] = func["name"]
                print("function:", func)
                if "element_path_exact" in temp["match_function_name"]:
                    temp["method"] = "selector"
                    temp["content"] = {"reference_answer": step["path"]}

                elif "element_value_exact" in temp["match_function_name"]:
                    temp["content"] = {"value": step["value"]}
                elif "element_value_include" in temp["match_function_name"]:
                    temp["content"] = {"reference_answer": func["required"], "value": step["value"]}
                elif "element_value_semantic" in temp["match_function_name"]:
                    temp["content"] = {"reference_answer": func["optional"]}

                elif "url_include" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    temp["content"] = {"key": key, "reference_answer": func["required"]}
                elif "url_exact" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    if "optional" in func.keys():
                        reference_answer = func["optional"]
                    elif len(key) > 0:
                        try:
                            parsed_url = urlparse(step["href"])
                            print(key)
                            url_params = parse_qs(parsed_url.query)
                            print(url_params)
                            reference_answer = url_params[key][0]
                        except:
                            print("Error in parsing URL!")
                    else:
                        reference_answer = step["href"]
                        print(reference_answer)
                    reference_answer = unquote(reference_answer)

                    # reference_answer = func["optional"] if "optional" in func.keys() else step["href"]
                    temp["content"] = {"key": key, "reference_answer": reference_answer}
                elif "url_semantic" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    temp["content"] = {"key": key, "reference_answer": func["optional"]}
                else:
                    print("*"*50, "\n", "other match function, coming soon!")
                # print(temp)
                evaluation.append(temp)
    print(evaluation)
    input()
    output.append({"task": task_name, "reference_task_length": reference_steps, "evaluation": evaluation})
print(output)

f_out = open("output.json", "w")
json5.dump(output, fp=f_out, ensure_ascii=False, indent=4, quote_keys=True, trailing_commas=False)
