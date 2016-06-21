VERSION = $(shell cat VERSION)

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

dist/ansible-tower-cli-$(VERSION).tar.gz: bin/tower-cli HISTORY.rst LICENSE MANIFEST.in README.rst VERSION requirements.txt setup.py setup.cfg
	@python setup.py sdist

rpm-build/.exists:
	mkdir -p rpm-build
	touch rpm-build/.exists


