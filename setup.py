import json
from setuptools import setup
from pathlib import Path

here = Path(__file__).parent
with open('package.json') as f:
    package = json.load(f)
long_description = (here / 'README.md').read_text()

package_name = package["name"].replace(" ", "_").replace("-", "_")

setup(
    name="dash-aggrid",
    version=package["version"],
    author=package['author'],
    packages=['aggrid_js'],
    include_package_data=True,
    license=package['license'],
    description=package.get('description', package_name),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'dash>=2.0.0',
    ],
    python_requires='>=3.8',
    url='https://github.com/ScottTpirate/dash-aggrid',
    project_urls={
        'Source': 'https://github.com/ScottTpirate/dash-aggrid',
        'Tracker': 'https://github.com/ScottTpirate/dash-aggrid/issues',
    },
    classifiers = [
        'Framework :: Dash',
    ],    
)
