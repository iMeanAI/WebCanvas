<h1 align="center">WebCanvas: Benchmarking Web Agents in Online Environments</h1>


<p align="center">
  <a href="https://github.com/iMeanAI/WebCanvas/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License MIT"></a>
  <a href="https://www.python.org/downloads/release/python-3110/"><img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python Version 3.11"></a>
  <a href="https://github.com/iMeanAI/WebCanvas/issues"><img src="https://img.shields.io/github/issues/iMeanAI/WebCanvas" alt="GitHub Issues"></a>
  <a href="https://github.com/iMeanAI/WebCanvas/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <a href="https://github.com/iMeanAI/WebCanvas/stargazers"><img src="https://img.shields.io/github/stars/iMeanAI/WebCanvas" alt="GitHub Stars"></a>
  <a href="https://github.com/iMeanAI/WebCanvas/network/members"><img src="https://img.shields.io/github/forks/iMeanAI/WebCanvas" alt="GitHub Forks"></a>

</p>

<p align="center">
    <img src="https://img.icons8.com/color/48/000000/internet.png" alt="Website" width="15" height="15" style="vertical-align: middle;"/> <a href="https://www.imean.ai/web-canvas">Website</a> • 
    <img src="https://img.icons8.com/color/48/000000/database.png" alt="Dataset" width="15" height="15" style="vertical-align: middle;"/> <a href="https://huggingface.co/datasets/iMeanAI/Mind2Web-Live">Dataset</a> • 
    <img src="https://img.icons8.com/color/48/000000/discord-logo.png" alt="Discord" width="15" height="15" style="vertical-align: middle;"/> <a href="https://discord.com/invite/wyhH5QPf">Discord</a>
</p>

WebCanvas is a pioneering online evaluation framework designed to address the dynamic nature of web interactions. It provides a realistic assessment of autonomous web agents by utilizing live web environments and emphasizing task completion through the identification of key nodes.


## 🌟Features

- **Comprehensive Agent Framework**: Includes a universal agent framework with four key modules: Planning, Observation, Memory, and Reward, designed to perform complex tasks within real-world online web environments effectively.
- **Dynamic and Real-time Web Environment Interaction**: Utilizes live web environments to provide a realistic assessment of web agents, ensuring that evaluations reflect the actual complexities of the web.
- **Key Nodes Annotation**: Introduces the concept of "key nodes" to offer in-progress feedback and a granular, phase-based assessment system that adapts to frequent changes in web navigation.
- **Enhanced Granularity of Progress Reward**: Allows for a thorough assessment of the reward module within the framework of autonomous web agents, focusing on the pivotal influence of reward signal quality.
- **Easy to Scale with Online Web Environment**: Connected to a comprehensive suite of toolkits to define demonstration trajectories and intermediate states for real-time, open-ended web tasks, allowing for robust evaluation in dynamic web environments.
- **Mind2Web-Live Dataset**: Presents a refined version of the original Mind2Web[^1] static dataset, containing 542 tasks with 2439 intermediate evaluation states, serving as the foundation for the benchmark.

## 🔥 News

- **[2024, June 6]** We've released [WebCanvas](https://github.com/iMeanAI/WebCanvas), including Data, Plugins, and Web agents!

## 🛣️ TODOs

- [ ] Design and implement a modular architecture for the existing Agent framework (LLM, Memory, Reward, Observation, etc.).
- [ ] Support token count calculation for LLM to manage computational costs and usage.
- [ ] Enable user-defined result saving paths to enhance system flexibility and configurability.
- [ ] Support the management of more error types to improve system robustness and error handling capabilities.

## 🔍 Getting Started

### Setting Up Your Environment

First, ensure your environment is ready by installing the necessary dependencies:

```bash 
conda create -n webcanvas python=3.11
conda activate webcanvas
pip install -r requirements.txt
```

### Configuration

Before running the repos, you need to set up the required API keys as using features dependent on external APIs. Our current framework only supports the OpenAI API. We plan to release updates in the future to support additional models.

For setting up OpenAI API keys, add your API key to your environment variables:

Our current framework only supports the OpenAI API. We plan to release updates in the future to support additional models.

If using OpenAI models, set a valid OpenAI API key (starting with `sk-`) as the environment variable:

MacOS/Linux:

```
export OPENAI_API_KEY='your-api-key-here'
```

Windows:

```text
setx OPENAI_API_KEY "your-api-key-here"
```

Visit [Quickstart tutorial - OpenAI API](https://platform.openai.com/docs/quickstart?context=python) for more details.

### Usage

You can run the repos with the following command:

```
python package_evaluate.py \
    --global_reward_mode dom_reward \
    --index -1 \
    --single_task_name "Find Dota 2 game and add all DLC to cart in steam."

```

This command runs the script with DOM-based global reward calculation, processing the default task "Find Dota 2 game and add all DLC to cart in steam" and using the default data index -1.


### Parameter Descriptions

This program supports several command-line arguments to customize its behavior:

- `--global_reward_mode`: Selects the method for getting global rewards.
  - Options: `dom_vision_reward`, `dom_reward`, `vision_reward`, `no_global_reward`
  - Default: `dom_reward`
  - Description: Define how rewards are got based on the interaction mode:
    - `dom_vision_reward`: Rewards are calculated using both DOM and vision data.
    - `dom_reward`: Rewards are based solely on DOM interactions.
    - `vision_reward`: Rewards are derived from vision-based interactions only.
    - `no_global_reward`: No global rewards are calculated.

- `--index`: Decide which data index to start with.
  - Type: String
  - Default: `-1`
  - Description: Use this parameter to specify a range or specific index for data processing. For example, `0,5` will process data from index 0 to 5.

- `--single_task_name`: Defines the task name of the single task to execute.
  - Type: String
  - Default: `"Find Dota 2 game and add all DLC to cart in steam."`
  - Description: Use this parameter to specify the task that the agent should perform.


## 🤝 Contributing


We welcome contributions to WebCanvas!

In the coming updates, we will provide detailed guidelines on how to contribute to our project. This will include instructions on our coding standards, the process for submitting pull requests, and how to report issues, and more. Stay tuned for more information!

Thank you for your interest in improving WebCanvas. Your contributions are greatly appreciated and essential to the growth and success of our project.



## 🌐 Community

We are building a vibrant and inclusive community around WebCanvas! Join our community to stay up-to-date with the latest developments and to contribute to the project:

- [GitHub Discussions](https://github.com/iMeanAI/WebCanvas/discussions)
- [Discord](https://discord.com/invite/wyhH5QPf) (invitation link)

## 📢 Feedback

We value your feedback and suggestions!

We will be providing a detailed guide on how to give feedback in the upcoming documentation. This will include information on how to submit feedback, the types of feedback we are looking for, and how we plan to address and incorporate your suggestions. Stay tuned for more updates!

#### References
[^1]: Deng, Xiang, et al. "Mind2web: Towards a generalist agent for the web." Advances in Neural Information Processing Systems 36 (2024).