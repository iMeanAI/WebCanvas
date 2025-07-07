
# api_key=API_KEY
# model_name=MODEL_NAME
api_key=${OPENAI_API_KEY}
model_name=gpt-4o
# model_name=o4-mini

#Automatic evaluation method
modes=(
    "WebJudge_Online_Mind2Web_eval"
    # "WebJudge_general_eval"
    # "Autonomous_eval"
    # "WebVoyager_eval"
    # "AgentTrek_eval"
)

# base_dir="./data/example"
base_dir="../WebCanvas/dataset_new/exp"

for mode in "${modes[@]}"; do
    python ./OM2W_Benchmarking/src/run.py \
        --mode "$mode" \
        --model "${model_name}" \
        --trajectories_dir "$base_dir" \
        --api_key "${api_key}" \
        --output_path results_new/exp \
        --num_worker 1 \
        --score_threshold 3
done
