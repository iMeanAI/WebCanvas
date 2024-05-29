from setuptools import setup, find_packages

# Read the requirements file
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='webcanvas',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A brief description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/to_be_determined/webcanvas',
    packages=find_packages(),
    install_requires=required,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
