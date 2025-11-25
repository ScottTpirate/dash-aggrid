import json
from pathlib import Path

from setuptools import setup

here = Path(__file__).parent
about = {}
about_path = here / "dash_aggrid_js" / "__about__.py"
exec(about_path.read_text(), about)
__version__ = about["__version__"]

with open("package.json") as f:
    package = json.load(f)
long_description = (here / "README.md").read_text()

setup(
    name=package["name"],
    version=__version__,
    author="Scott Kilgore",
    author_email="skilgore@landmarktx.com",
    packages=["dash_aggrid_js", "dash_aggrid"],
    include_package_data=True,
    license=package["license"],
    description=package.get("description", package["name"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "dash>=2.0.0",
    ],
    extras_require={
        "dev": ["pre-commit>=3.6", "build>=1.0", "twine>=4.0"],
        "test": ["pytest>=7.4", "dash[testing]>=2.14", "selenium>=4.15"],
    },
    python_requires=">=3.8",
    url="https://github.com/ScottTpirate/dash-aggrid",
    project_urls={
        "Source": "https://github.com/ScottTpirate/dash-aggrid",
        "Tracker": "https://github.com/ScottTpirate/dash-aggrid/issues",
    },
    classifiers=[
        "Framework :: Dash",
    ],
)
