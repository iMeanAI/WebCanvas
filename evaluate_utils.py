async def adjust_max_action_step(conditions, current_info, encountered_errors, increase_step):
    total_increase = 0
    for condition_type, keywords in conditions.items():
        for keyword in keywords:
            if keyword in current_info[condition_type] and keyword not in encountered_errors:
                print(f"Detected '{keyword}' in {current_info[condition_type]}, suggesting increase by {increase_step} steps.")
                total_increase += increase_step
                encountered_errors.add(keyword)
    return total_increase, encountered_errors
