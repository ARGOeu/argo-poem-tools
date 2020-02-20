%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       Script installs packages on ARGO mon boxes.
Name:          argo-poem-tools
Version:       0.1.0
Release:       1%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       GPL
Group:         Development/Libraries
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
%if 0%{?el6}
%dir %{python_sitelib}/%{underscore %{name}}/
%{python_sitelib}/%{underscore %{name}}/*.py[co]
%else
%dir %{python2_sitelib}/%{underscore %{name}}/
%{python2_sitelib}/%{underscore %{name}}/*.py[co]
%endif
%defattr(-,root,root)
