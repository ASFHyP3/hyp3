# Contributing

Thank you for your interest in helping make custom on-demand SAR processing accessible!

We're excited you would like to contribute to HyP3! Whether you're finding bugs, adding new features, fixing anything broken, or improving documentation, get started by submitting an issue or pull request!

## Submitting an Issue

If you have any questions or ideas, or notice any problems or bugs, first [search open issues](https://github.com/ASFHyP3/hyp3/issues) to see if the issue has already been submitted. We may already be working on the issue. If you think your issue is new, you're welcome to [create a new issue](https://github.com/ASFHyP3/hyp3/issues/new).

## Pull Requests are welcome

Found a typo, know how to fix a bug, want to update the docs, want to add a new feature? Great!

The smaller the PR, the easier it is to review and test and the more likely it is to be successful.

For major contributions, consider opening [an issue](https://github.com/ASFHyP3/hyp3/issues/new) describing the contribution so we can help guide and breakup the work into digestible pieces.

### Workflow
If you want to submit your own contributions, please use a [forking workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow).

The basic steps are:
1. Fork the repository

2. Clone your fork
   ```
   git clone https://github.com/[OWNER]/hyp3.git
   ```
3. Add this repository as an `upstream` remote
   ```
   git remote add upstream https://github.com/ASFHyP3/hyp3.git
   ```  
4. Create a feature branch based on the upstream/develop branch
   ```
   git fetch --all --prune
   git checkout --no-track -b [NAME] upstream/develop
   ```
5. Make your changes! Then push them to your fork
   ```
   git push -u origin [NAME]
   ```
6. Propose your changes by opening a pull request to `ASFHyP3/hyp3`'s `develop` branch

## Guidelines

We ask that you follow these guidelines with your contributions

### Style

We generally follow python community standards ([PEP8](https://pep8.org/)), except we allow line lengths up to 120 characters. We recommend trying to keep lines 80--100 characters long, but allow up to 120 when it improves readability.

### Documentation

We are working to improve our documentation!

For all public-facing functions/methods (not [marked internal use](https://www.python.org/dev/peps/pep-0008/#naming-conventions)), please include [type hints](https://google.github.io/styleguide/pyguide.html#221-type-annotated-code) (when reasonable) and a [docstring](https://www.python.org/dev/peps/pep-0257/) formatted [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).


### Tests

All of the automated tests for this project need to pass before your submission will be accepted.

If you add new functionality, please add tests for that functionality as well.

### Commits

* Make small commits that show the individual changes you are making
* Write descriptive commit messages that explain your changes

Example of a good commit message;

```
Improve contributing guidelines. Fixes #10

Improve contributing docs and consolidate them in the standard location
https://help.github.com/articles/setting-guidelines-for-repository-contributors/
```
