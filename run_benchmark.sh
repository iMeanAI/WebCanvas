#!/bin/bash

# Create Logs directory if it doesn't exist
mkdir -p Logs

# Get current timestamp for log file
timestamp=$(date +"%Y%m%d_%H%M%S")
log_file="Logs/benchmark_${timestamp}.log"

# Run the benchmark with nohup and redirect output to log file
nohup bash OM2W_Benchmarking/eval.sh > "${log_file}" 2>&1 &

# Print the process ID and log file location
echo "Process started with PID: $!"
echo "Log file: ${log_file}"

# rm /home/azureuser/wln/Code/WebCanvas/results/WebJudge_Online_Mind2Web_eval_gpt-4o_score_threshold_3_auto_eval_results.json
python OM2W_Benchmarking/statistic.py 