# Contributing

Thank you for contributing to Django Dramatiq!

We are a [small team of contributors](/CONTRIBUTORS.md) that make this library possible. We are always looking for more help and support. 

Please follow the guidelines provided below to receive the best support possible. 

## Reporting an Issue

All issues reported to Djang Dramatiq MUST follow the issue template. Any issues that do not follow this template can and will be closed. 

## Running the Project Locally

1. `git clone` the project
2. Create a virtual environment and install the dev dependencies with `pip install -e '.[dev]'` .
3. Run tests with `python -m pytest`

Follow the [README.md](/examples/basic/README.md) in the example app for more details. 

## Deploying A New Version

1. Update [CHANGELOG.md](/CHANGELOG.md)
2. Create a new branch, and bump the version in [`django_dramatiq/__init__.py`](/django_dramatiq/__init__.py) following SEMVER
3. Merge the branch
4. Create a release via the Github UI. Please allow Github to create the changelog
5. Submit the release and tag. 
6. Confirm that the github workflow finishes successfully and publishes to pypi.


