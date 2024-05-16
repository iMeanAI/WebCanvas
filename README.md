<h1 align="center">WebCanvas: Benchmarking Web Agents in Online Environments</h1>

<hr>

<p align="center">
  <a href="https://github.com/imean-ai/WebCanvas/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License Apache 2.0"></a>
  <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python Version 3.11">
  <a href="https://github.com/imean-ai/WebCanvas/issues"><img src="https://img.shields.io/github/issues/imean-ai/WebCanvas" alt="GitHub Issues"></a>
  <a href="https://github.com/imean-ai/WebCanvas/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <a href="https://github.com/imean-ai/WebCanvas/stargazers"><img src="https://img.shields.io/github/stars/imean-ai/WebCanvas" alt="GitHub Stars"></a>
  <a href="https://github.com/imean-ai/WebCanvas/network/members"><img src="https://img.shields.io/github/forks/imean-ai/WebCanvas" alt="GitHub Forks"></a>
</p>
<p align="center">
    <a href="https://arxiv.org/pdf/">[📄 Paper待定]</a> 
    <a href="">[📄 Doc(可选的)]</a>
    <a href="https://www.imean.ai/web-canvas">[🌐 Website]</a>
    <a href="#web-demos">[🤖️ Demos(可选的)]</a> 
    <a href="">[🔥 Discord(可选的)]</a> 
</p>

WebCanvas is a pioneering online evaluation framework designed to address the dynamic nature of web interactions. It provides a realistic assessment of autonomous web agents by utilizing live web environments and emphasizing task completion through the identification of key nodes.

（如果有框架图片的话可以在这里放一张图片）

## 🌟Features

- **Comprehensive Agent Framework**: Includes a universal agent framework with four key modules: Planning, Observation, Memory, and Reward, designed to perform complex tasks within real-world online web environments effectively.

- **Dynamic and Real-time Web Environment Interaction**: Utilizes live web environments to provide a realistic assessment of web agents, ensuring that evaluations reflect the actual complexities of the web. 

- **Key Nodes Annotation**: Introduces the concept of "key nodes" to offer in-progress feedback and a granular, phase-based assessment system that adapts to frequent changes in web navigation.
- **Enhanced Granularity of Progress Reward**: Allows for a thorough assessment of the reward module within the framework of autonomous web agents, focusing on the pivotal influence of reward signal quality.
- **Easy to Scale with Online Web Environment**: Developed a comprehensive suite of functions to assess intermediate states during real-time, open-ended tasks, allowing for robust evaluation in dynamic web environments.
- **Mind2Web-Online Dataset**: Presents a refined version of the original Mind2Web static dataset, containing 438 live data and 1995 intermediate evaluation states, serving as the foundation for the benchmark.

## 🔥 News

- **[2023, Aug 8 日期根据实际情况修改]** We've released [WebCanvas](), including Data, Plugins, and Web agents! Check [tutorials]() and [use cases]()!等等的修改

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
python evaluate.py \
    --observation_mode dom \
    --ground_truth_mode True \
    --global_reward_mode dom_reward
```

This command runs the script in DOM-based observation mode, with ground truth data enabled and DOM-based global reward calculation.


### Parameter Descriptions

This program supports several command-line arguments to customize its behavior:


- `--ground_truth_mode`: Determines whether to use Ground Truth data in global reward function.
  - Options: `True`, `False`
  - Default: `True`
  - Description: Enable this to use real, verified Ground Truth data for global reward. Disable it to use purely LLMs-generated global reward.


- `--global_reward_mode`: Selects the method for getting global rewards.
  - Options: `dom_vision_reward`, `dom_reward`, `vision_reward`
  - Default: `dom_reward`
  - Description: Define how rewards are got based on the interaction mode:
    - `dom_vision_reward`: Rewards are calculated using both DOM and vision data.
    - `dom_reward`: Rewards are based solely on DOM interactions.
    - `vision_reward`: Rewards are derived from vision-based interactions only.


- `--index`: Specifies the data subset or specific tests to run.（这个不是很了解，等写这个的同学来check一下）
  - Type: String
  - Default: `-1`
  - Description: Use this parameter to specify a range or specific index for data processing. For example, `0,5` will process data from index 0 to 5.


```bash
python -m script_name --observation_mode dom --ground_truth_mode True --global_reward_mode dom_reward --index 0,5

```
This command will start the program with DOM-based observation, using real data, focusing on DOM-based rewards, and processing the data subset from index 0 to 5.


## 📚 Documentation（可选，如果我们有写Documentation就可以放）

Please check our [documentation](https://agents-readthedocsio.readthedocs.io/en/latest/index.html) for detailed documentation of the framework.

## 🤝 Contributing

**根据实际情况选择要不要写这一节，可以根据后期的Contributing的规划再添加这一节**

待定，估计后面再加进去Contributing这一节也问题不大

We welcome contributions to WebCanvas. Please read our [Contribution Guidelines](CONTRIBUTING.md) before getting started.

If you're interested in contributing to the `WebCanvas` project, please

- refer to [CONTRIBUTING.md](https://github.com//CONTRIBUTING.md)
- open an [issue](https://github.com//issues) or submit a PR
- join us on [discord](https://discord.gg/)
- or reach out to [@aaaa](https://twitter.com/) on Twitter

[self-operating-computer/CONTRIBUTING.md at main · OthersideAI/self-operating-computer (github.com)](https://github.com/OthersideAI/self-operating-computer/blob/main/CONTRIBUTING.md)

[prompt2model/CONTRIBUTING.md at main · neulab/prompt2model (github.com)](https://github.com/neulab/prompt2model/blob/main/CONTRIBUTING.md)



We appreciate your interest in contributing to our open-source initiative. Please feel free to submit a PR or share your thoughts on how to improve the library in Issues!



This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit [https://cla.opensource.microsoft.com](https://cla.opensource.microsoft.com/).

If you are new to GitHub, [here](https://opensource.guide/how-to-contribute/#how-to-submit-a-contribution) is a detailed help source on getting involved with development on GitHub.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.



Encourage contributions and detail the process for submitting pull requests:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -am 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information on our code of conduct and the process for submitting pull requests.



Thanks to open-sourced communities’ efforts, such as [LangChain](https://github.com/langchain-ai/langchain), [ChatBot UI](https://github.com/mckaywrigley/chatbot-ui), [Taxy.ai browser extension](https://github.com/TaxyAI/browser-extension) and others. We are able to build our interface prototype much more conveniently and efficiently.

We welcome contributions and suggestions, together we move further to make it better! Following the steps will be well-received:

- **Step1:** Post an [issue](https://github.com/xlang-ai/OpenAgents/issues) if you want to add any additional features, enhancements, or encounter any problems during your experience. We would appreciate it if you follow the [issue template](https://github.com/xlang-ai/OpenAgents/blob/main/CONTRIBUTING.md). The issues will be discussed and assigned there.
- **Step2:** Whenever an issue is assigned, you can contribute by creating a [Pull Request](https://github.com/xlang-ai/OpenAgents/pulls) by following the [PR template](https://github.com/xlang-ai/OpenAgents/blob/main/CONTRIBUTING.md). You can also claim for any open issues. Together we can make OpenAgents better!
- **Step3:** PR will be merged or iterated after review and discussion. Thanks for your contribution!

Before you start, we highly recommend taking a moment to check [here](https://github.com/xlang-ai/OpenAgents/blob/main/CONTRIBUTING.md) before contribution.


## 💬 FAQ（可选的）

根据实际情况选择要不要写这一节

**Q: How do I set up the project?**

A: Refer to the Getting Started section above.

**Q: Where can I find more documentation?**

A: Check the `docs` folder in this repository. 根据实际情况（如果有documentation 和 documentation的位置）修改

## **Community**（可选的）

根据实际情况（有没有Community）选择要不要写这一节

Join our community to stay up-to-date with the latest developments and to contribute to the project:

- [GitHub Discussions](https://github.com/imean-ai/WebCanvas/discussions)
- [Community Slack](https://imean-ai.slack.com/) (invitation link available in the repo Wiki)

## 📢 Feedback

Encourage users to provide feedback and where/how they can do it.

## ✏️Citation

If you find our work helpful, please consider starring our repos and using the following BibTeX to cite our work:

```angular2
@software{pku_yuan_lab_and_tuzhan_ai_etc_2024_10948109,根据实际情况修改
  author       = {PKU-Yuan Lab and Tuzhan AI etc.},
  title        = {Open-Sora-Plan},
  month        = apr,
  year         = 2024,
  publisher    = {GitHub},
  doi          = {10.5281/zenodo.10948109},
  url          = {https://doi.org/10.5281/zenodo.10948109}
}
```

## 💡 Acknowledgments（可选的）

根据实际情况选择要不要写这一节

We would like to thank Google Research, Amazon AWS, and Salesforce Research for their research gift funds to this open-source effort!