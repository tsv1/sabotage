from setuptools import setup, find_packages
import sabotage


setup(
    name="sabotage",
    version=sabotage.__version__,
    author="Nikita Tsvetkov",
    author_email="nikitanovosibirsk@yandex.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nikitanovosibirsk/sabotage",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
    ],
)
