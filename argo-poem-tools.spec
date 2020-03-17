%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       Script installs packages on ARGO mon boxes.
Name:          argo-poem-tools
Version:       0.1.2
Release:       1%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

%if 0%{?el6}
BuildRequires: python-devel
Requires:      python-argparse
%else
BuildRequires: python2-devel
%endif
Requires:      python-requests


%description
Script which installs packages on ARGO mon boxes.


%prep
%setup -q


%build
%if 0%{?el6}
%{py_build}
%else
%{py2_build}
%endif


%install
%if 0%{?el6}
%{py_install "--record=INSTALLED_FILES" }
%else
%{py2_install "--record=INSTALLED_FILES" }
%endif


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)
%if 0%{?el6}
%dir %{python_sitelib}/%{underscore %{name}}/
%{python_sitelib}/%{underscore %{name}}/*.py[co]
%else
%dir %{python2_sitelib}/%{underscore %{name}}/
%{python2_sitelib}/%{underscore %{name}}/*.py[co]
%endif

%changelog
* Mon Mar 16 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.2-1%{?dist}
- ARGO-2292 Load parameters from config file
* Fri Feb 28 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.1-1%{?dist}
- ARGO-2266 Refactor argo-poem-tools to handle new tags in package
* Thu Feb 20 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.0-1%{?dist}
- ARGO-2230 Create script which will install packages for given metric profiles
