import json5
import requests
from evaluate import *

if __name__ == "__main__":

    evaluate_steps = []

    def read_file():
        with open("./data/test.json") as f:
            test_data = json5.load(f)

        evaluation_data = test_data[0]["evaluation"]

        for evaluation in evaluation_data:
            match_function = evaluation["match_function"]
            if match_function == "url_exact_match":
                key = evaluation["content"]["key"]
                reference_answer = evaluation["content"]["reference_answer"]
                evaluate_steps.append(
                    {"key": key, "reference_answer": reference_answer, "score": 0})

    read_file()
    print("raw data:\n",evaluate_steps)
    test_urls = ["https://zh.airbnb.com/?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&search_mode=flex_destinations_search&flexible_trip_lengths%5B%5D=one_week&location_search=MIN_MAP_BOUNDS&monthly_start_date=2023-12-01&monthly_length=3&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&category_tag=Tag%3A677&search_type=category_change",
                 "https://zh.airbnb.com/?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&search_mode=flex_destinations_search&flexible_trip_lengths%5B%5D=one_week&location_search=MIN_MAP_BOUNDS&monthly_start_date=2023-12-01&monthly_length=3&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&category_tag=Tag%3A677&search_type=filter_change&price_min=200&price_max=300"]
    for url in test_urls:
        step_score = 0
        print()
        for evaluate in evaluate_steps:
            if evaluate["score"] != 1:
                score = URLEvaluator.URL_exact_match(
                    url, evaluate["reference_answer"], evaluate["key"])
            evaluate["score"] = max(evaluate["score"], score)
            step_score += evaluate["score"]
        print("step score:", step_score)
        # print(evaluate_steps)

    total_score = 0
    for evaluate in evaluate_steps:
        total_score += evaluate["score"]
    print("\ntotal score:", total_score)
