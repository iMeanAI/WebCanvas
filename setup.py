from setuptools import setup, find_packages
import os


# dynamically load dependencies in requirements.txt
def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line and not line.startswith("#")]


setup(
    name="WebCanvas",
    version="0.0.4",
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
    author="Cheng Cui, Sida Zhou, Dehan Kong, Yichen Pan",
    author_email="dehan@imean.ai",
    description="A universal agent framework with four key modules: Planning, Observation, Memory, and Reward, designed to perform complex tasks within real-world online web environments effectively.",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/iMeanAI/WebCanvas",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
