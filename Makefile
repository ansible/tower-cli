PYTHON=python

# Get the branch information from git
GIT_DATE := $(shell git log -n 1 --format="%ai")
DATE := $(shell date -u +%Y%m%d%H%M)

.PHONY: clean rebase push sdist install

# Remove temporary build files, compiled Python files.
clean:
	rm -rf dist build
	rm -rf *.egg-info
	find . -type f -regex ".*\.py[co]$$" -delete

# Fetch from origin, rebase local commits on top of origin commits.
rebase:
	git pull --rebase origin master

# Push changes to origin.
push:
	git push origin master

sdist: clean
	$(PYTHON) setup.py sdist

install:
	$(PYTHON) setup.py install
