%define underscore() %(echo %1 | sed 's/-/_/g')

Summary: Script which installs packages on ARGO mon boxes.
Name: argo-poem-tools
Version: 0.1.0
Release: 1%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix: %{_prefix}
BuildArch: noarch
Requires: python-requests
Requires: python-argparse

%description
Script which installs packages on ARGO mon boxes.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --skip-build --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%dir %{python_sitelib}/%{underscore %{name}}/
%{python_sitelib}/%{underscore %{name}}/*.py[co]
%defattr(-,root,root)
