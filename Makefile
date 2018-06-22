VERSION := $(shell python -c "exec(open('''tower_cli/constants.py''').read(), globals()); print VERSION")
RELEASE := $(shell python -c "exec(open('''tower_cli/constants.py''').read(), globals()); print RELEASE")

MOCK_BIN ?= mock

el6: dist/ansible-tower-cli-$(VERSION).tar.gz rpm-build/ansible-tower-cli-${VERSION}.spec
	mock -r epel-6-x86_64 --buildsrpm --spec rpm-build/ansible-tower-cli-${VERSION}.spec --sources dist/ --resultdir rpm-build
	mock -r epel-6-x86_64 --rebuild rpm-build/ansible-tower-cli-${VERSION}-${RELEASE}.el6.src.rpm --resultdir rpm-build

el7: dist/ansible-tower-cli-$(VERSION).tar.gz rpm-build/ansible-tower-cli-${VERSION}.spec
	$(MOCK_BIN) -r epel-7-x86_64 --buildsrpm --spec rpm-build/ansible-tower-cli-${VERSION}.spec --sources dist/ --resultdir rpm-build
	$(MOCK_BIN) -r epel-7-x86_64 --rebuild rpm-build/ansible-tower-cli-${VERSION}-${RELEASE}.el7.src.rpm --resultdir rpm-build

all: el6 el7

remove_complied:
	find . -type d -name "__pycache__" -delete
	find . -name '*.pyc' -delete

clean: remove_complied
	rm -rf dist
	rm -rf build
	rm -rf ansible_tower_cli.egg-info
	rm -rf rpm-build

dist/ansible-tower-cli-$(VERSION).tar.gz: docs/source/HISTORY.rst LICENSE MANIFEST.in README.rst requirements.txt setup.py setup.cfg
	@python setup.py sdist

rpm-build/ansible-tower-cli-${VERSION}.spec: packaging/rpm/ansible-tower-cli.spec rpm-build/.exists
	cat packaging/rpm/ansible-tower-cli.spec | sed 's:__VERSION__:$(VERSION):' | sed 's:__RELEASE__:$(RELEASE):' > ./rpm-build/ansible-tower-cli-${VERSION}.spec

rpm-build/.exists:
	mkdir -p rpm-build
	touch rpm-build/.exists

# For devel convenience
install:
	python setup.py install

local_install:
	python setup.py install --user

refresh: clean install

clean_v2:
	rm -rf tower_cli_v2
	rm -rf ansible_tower_cli_v2.egg-info
	rm -rf setup_v2.py

setup_v2.py:
	cp -R tower_cli tower_cli_v2/
	cp setup.py setup_v2.py
	python version_swap.py

prep_v2: setup_v2.py

install_v2: setup_v2.py
	python setup_v2.py install

v2-refresh: clean clean_v2 install_v2
