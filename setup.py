"""
The setup.py file is an essential part of packaging and distributing Python projects. It is used by setuptools (or distutils in older Python versions) to define the configuration of your project, such as its metadata, dependencies, and more
"""


from setuptools import setup, find_packages
from typing import List

def get_requirements() -> List[str]:
    """ This function will return a list of requirements """

    requirements_lst: List[str] = []
    try:
        with open('requirements.txt') as f:
            # Read Lines from the file
            lines = f.readlines()

            #Process each line
            for line in lines:
                requirement = line.strip()

                #Ignore Empty lines and -e .
                if requirement and requirement != '-e .':
                    requirements_lst.append(requirement)


    except FileNotFoundError:
        print('requirements.txt not found')

    return requirements_lst

# print(get_requirements())

setup(
    name='NetworkSecurity',
    description='Network Security Project',
    version='1.0.0',
    author='Priyanshu',
    packages=find_packages(),
    install_requires=get_requirements(),
)