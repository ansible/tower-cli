VERSION := $(shell python -c "exec(open('''tower_cli/constants.py''').read(), globals()); print VERSION")

DISTS = el6 el7
DIST_SUFFIX_el6 = 
DIST_SUFFIX_el7 = .centos
MOCK_CFG_el6 = epel-6-x86_64
MOCK_CFG_el7 = epel-7-x86_64

.PHONY: all clean $(DISTS)
.DEFAULT_GOAL = all

define RPM_DIST_RULE

$(eval $(1)_SRPM=rpm-build/ansible-tower-cli-$(VERSION)-1.$(1)$(DIST_SUFFIX_$(1)).src.rpm)
$(eval $(1)_RPM=rpm-build/ansible-tower-cli-$(VERSION)-1.$(1)$(DIST_SUFFIX_$(1)).noarch.rpm)
SRPMS += $($(1)_SRPM)
RPMS += $($(1)_RPM)

$($(1)_SRPM): rpm-build/.exists dist/ansible-tower-cli-$(VERSION).tar.gz packaging/rpm/ansible-tower-cli.spec
	mock -r $(MOCK_CFG_$(1)) --buildsrpm --spec packaging/rpm/ansible-tower-cli.spec --sources dist/ --resultdir rpm-build

$($(1)_RPM): $($(1)_SRPM)
	mock -r $(MOCK_CFG_$(1)) --rebuild $($(1)_SRPM) --resultdir rpm-build

$(1): $($(1)_RPM)

endef

$(foreach DIST, $(DISTS), $(eval $(call RPM_DIST_RULE,$(DIST))))

all: $(RPMS)

remove_complied:
	find . -type d -name "__pycache__" -delete
	find . -name '*.pyc' -delete

clean: remove_complied
	rm -rf dist
	rm -rf build
	rm -rf ansible_tower_cli.egg-info
	rm -rf rpm-build

dist/ansible-tower-cli-$(VERSION).tar.gz: bin/tower-cli HISTORY.rst LICENSE MANIFEST.in README.rst requirements.txt setup.py setup.cfg
	@python setup.py sdist

rpm-build/.exists:
	mkdir -p rpm-build
	touch rpm-build/.exists

# For devel convenience
install:
	python setup.py install

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
