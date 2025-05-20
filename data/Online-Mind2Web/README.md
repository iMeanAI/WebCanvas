---
license: cc-by-4.0
language:
- en
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: test
    path: "Online_Mind2Web.json"
---
<div align="center">
    <a href="https://tiancixue.notion.site/An-Illusion-of-Progress-Assessing-the-Current-State-of-Web-Agents-1ac6cd2b9aac80719cd6f68374aaf4b4?pvs=4">Blog</a> |
    <a href="https://arxiv.org/abs/2504.01382">Paper</a> |
    <a href="https://github.com/OSU-NLP-Group/Online-Mind2Web">Code</a> |
    <a href="https://huggingface.co/spaces/osunlp/Online_Mind2Web_Leaderboard">Leaderboard</a>
</div>


## Online-Mind2Web
Online-Mind2Web is the online version of [Mind2Web](https://osu-nlp-group.github.io/Mind2Web/), a more diverse and user-centric dataset includes 300 high-quality tasks from 136 popular websites across various domains. The dataset covers a diverse set of user tasks, such as clothing, food, housing, and transportation, to evaluate web agents' performance in a real-world online environment.

### Data Fields
- "task_id" (str): Unique id for each task.
- "website" (str): Website url.
- "task_description" (str): Task description.
- "reference_length" (int): Number of steps required for a human annotator to complete the task.

### Update Tasks
We will regularly update Online-Mind2Web by replacing outdated or invalid tasks (e.g., due to website changes) to maintain its value as a rigorous benchmark for web agents. If you find any tasks are outdated, please reach out to us, and we will update them. 

To ensure fair comparisons, we will aim to keep the updated tasks on the same websites as before and with a similar reference length. Additionally, once agent performance saturates on Online-Mind2Web, we will also revise simple tasks to preserve its long-term value.

### Update History
**2025/04/05:** Updated task IDs: ["c03ee2be3d73556ab789c0ad1cbd3451", "c181f903ec1107b850032c17cad88393", "2c8ef01a92c71ba9ef2e59bb17eea2b3", "d8e2a81fa621ce4737e5ea85671b630e", "63d6866fc000fcb1f153e07604bd1395", "199be0b54a436daee74247971fc684ee"]

### Disclaimer
This dataset was collected and released solely for research purposes, with the goal of making the web more accessible via language technologies. The authors are strongly against any potential harmful use of the data or technology to any party.

### Citation Information
Note: Online-Mind2Web is derived from the original Mind2Web dataset. We kindly ask that you cite both the original and this work when using or referencing the data.
```
@article{xue2025illusionprogressassessingcurrent,
      title={An Illusion of Progress? Assessing the Current State of Web Agents}, 
      author={Tianci Xue and Weijian Qi and Tianneng Shi and Chan Hee Song and Boyu Gou and Dawn Song and Huan Sun and Yu Su},
      year={2025},
      eprint={2504.01382},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2504.01382}, 
}

@inproceedings{deng2023mind2web,
 author = {Deng, Xiang and Gu, Yu and Zheng, Boyuan and Chen, Shijie and Stevens, Sam and Wang, Boshi and Sun, Huan and Su, Yu},
 booktitle = {Advances in Neural Information Processing Systems},
 editor = {A. Oh and T. Naumann and A. Globerson and K. Saenko and M. Hardt and S. Levine},
 pages = {28091--28114},
 publisher = {Curran Associates, Inc.},
 title = {Mind2Web: Towards a Generalist Agent for the Web},
 url = {https://proceedings.neurips.cc/paper_files/paper/2023/file/5950bf290a1570ea401bf98882128160-Paper-Datasets_and_Benchmarks.pdf},
 volume = {36},
 year = {2023}
}
```