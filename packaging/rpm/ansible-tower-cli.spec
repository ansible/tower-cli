%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%global srcname tower-cli

Name:           ansible-%{srcname}
Version:        3.2.0
Release:        2%{?dist}
Summary:        Commandline interface for Ansible Tower
Group:          Development/Tools
License:        ASL 2.0
URL:            https://github.com/ansible/tower-cli
Source0:        https://pypi.python.org/packages/f7/7d/ee885225933bb498c34e2ad704194ed188662489a4ca4936a2d82248b6e8/%{srcname}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildArch:      noarch
Requires:	python-six >= 1.7.2
Requires:	PyYAML >= 3.10
Requires: 	python-requests >= 2.3.0
Requires:	python-click >= 2.1
%if 0%{?rhel} == 6
Requires: python-importlib >= 1.0.2
Requires: python-ordereddict >= 1.1
Requires: python-simplejson >= 3.5.3
%endif

%description
ansible-tower-cli is a command line tool for Ansible Tower. It allows Tower
commands to be easily run from the Unix command line. It can also be
used as a client library for other python apps, or as a reference for
others developing API interactions with Tower's REST API.

%prep
%setup -q -n %{srcname}-%{version}

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/tower
touch $RPM_BUILD_ROOT/etc/tower/tower_cli.cfg

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc LICENSE README.rst HISTORY.rst
%config(noreplace) %ghost %{_sysconfdir}/tower/tower_cli.cfg
%{python_sitelib}/ansible*
%{python_sitelib}/tower_cli*

%changelog
* Sun Mar 26 2017 Satoru SATOH <satoru.satoh@gmail.com> - 3.1.3-2
- Fix the source archive name

* Fri Jun 17 2016 Bill Nottingham <notting@ansible.com> - 2.3.1-1
- initial spec file
