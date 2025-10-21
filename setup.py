from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["pydantic>=2.6.0", "PyJWT>=2.8.0", "requests>=2.31.0"]

setup(
    name="amo_crm_api",
    version="0.1.30",
    author="damir-2000",
    author_email="gilemhonov.damir@gmail.com",
    description="Amo CRM Api",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/damir-2000/amo_crm_api",
    packages=find_packages(),
    install_requires=requirements,
    license="MIT",
    python_requires=">=3.9.13",
    # classifiers=[
    #     "Programming Language :: Python :: 3.7",
    #     "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    # ],
)