from setuptools import setup, find_packages


setup(
    name="sabotage",
    version="0.2.0",
    description="Infra-tests made easy",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nikita Tsvetkov",
    author_email="nikitanovosibirsk@yandex.com",
    python_requires=">=3.6.0",
    url="https://github.com/nikitanovosibirsk/sabotage",
    license="Apache 2",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "docker>=2.4,<=3.7",
    ],
    tests_require=[
        "mypy==0.670",
        "flake8==3.7.7",
        "coverage==4.5.3",
        "codecov==2.0.15",
    ],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
