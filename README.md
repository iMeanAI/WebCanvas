# WebCanvas Online-Mind2Web-eval

## 🔍 Evaluation on Existing WebCanvas Benchmarks

### Setting Up the Environment

First, ensure your environment is ready by installing the necessary dependencies:

```bash 
conda create -n webcanvas python=3.11
conda activate webcanvas
pip install -r requirements.txt
```

Before running the repos, you need to set up the required API keys as using features dependent on external APIs. Please refer to this [docs](agent/LLM/README.md).

Also, you need to install the Node.js dependencies:

```bash
npm init -y
npm install axios
```
Then you need to set the google search api key and custom search engine id to perform google search action, for **Google blocked GUI agent based search lately**.

```bash
export GOOGLE_API_KEY=your_api_key
export GOOGLE_CX=your_custom_search_engine_id
```

See [How to set up google search](https://developers.google.com/custom-search/v1/overview?hl=zh-cn) for more details.

OPEN_AI api setting
```bash
export OPENAI_API_KEY=your_api_key
```

Tips: To run in a Linux environment without a visual interface, use the following command to start:

```bash
    sudo yum install -y xorg-x11-server-Xvfb
```
Ubantu/Debian users can use the following command to install xvfb:
```bash    
    sudo apt-get update
    sudo apt-get install -y xvfb
```


### 👁 Evaluation process
See "configs/setting.toml" and "batch_eval.py" for parameter Settings for evaluation.

Set the log path in "log.py"

Start evaluation：

```bash
xvfb-run -a python batch_eval.py
```

#### tips:

1. If you want to inspect the Prompt output of the rag construct, you can set the output path in agent/Utils/rag_logger.py and inspect it.


### Evaluate dataset processing
After getting the evaluation data set, use "utils/parser.py" to parse the log log file to get the json parsed file

Please set the parameters for the json file parsing step in "configs/log_config.json"

And then run the program
```bash
python utils/parser.py
python utils/dataset_process.py
```
The directory of the processed data set is：
```bash
results/
- task_id
-- trajectory
--- step_0_20250520-000604.png
--- step_2_20250520-000604.png
  ...
-- result.json
```

### Online-Mind2Web Benchmarking
Run the following command to generate the benchmark file:
```bash
bash OM2W_Benchmarking/eval.sh
```

Display evaluation results:
```bash
python OM2W_Benchmarking/statistic.py 
```