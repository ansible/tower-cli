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

clean:
	rm -rf dist
	rm -rf ansible_tower_cli.egg-info
	rm -rf rpm-build

dist/ansible-tower-cli-$(VERSION).tar.gz: bin/tower-cli HISTORY.rst LICENSE MANIFEST.in README.rst requirements.txt setup.py setup.cfg
	@python setup.py sdist

rpm-build/.exists:
	mkdir -p rpm-build
	touch rpm-build/.exists

# For devel convenience
install:
	sudo rm -rf dist/ build/ 
	sudo python setup.py install
	
clean_v1:
	rm -rf tower_cli_v1
	rm -rf ansible_tower_cli_v1.egg-info
	rm -rf setup_v1.py
	rm -f bin/tower-cli-v1

setup_v1.py:
	cp -R tower_cli tower_cli_v1/
	cp bin/tower-cli bin/tower-cli-v1
	cp setup.py setup_v1.py
	python version_swap.py

prep_v1: setup_v1.py

install_v1: setup_v1.py
	sudo rm -rf dist/ build/
	sudo python setup_v1.py install

v1-refresh: clean_v1 install_v1
