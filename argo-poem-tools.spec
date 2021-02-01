%define underscore() %(echo %1 | sed 's/-/_/g')
%define stripc() %(echo %1 | sed 's/el7.centos/el7/')
%define mydist %{stripc %{dist}}

Summary:       Script installs packages on ARGO mon boxes.
Name:          argo-poem-tools
Version:       0.2.0
Release:       2%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel
Requires:      python36-requests


%description
Script which installs packages on ARGO mon boxes.


%prep
%setup -q


%build
%{py3_build}


%install
%{py3_install "--record=INSTALLED_FILES" }


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/%{name}/argo-poem-tools.conf
%dir %{python3_sitelib}/%{underscore %{name}}/
%{python3_sitelib}/%{underscore %{name}}/*.py

%changelog
* Mon Feb 1 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.0-2%{?dist}
- ARGO-2858 argo-poem-tools wrongly marking packages as not available
* Wed Jan 13 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.0-1%{?dist}
- ARGO-2564 Switch argo-poem-tools to Py3
* Mon Dec 7 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.5-1%{?dist}
- ARGO-2565 Use SysLogHandler instead of FileHandler in argo-poem-tools
* Mon Aug 31 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.4.-1%{?dist}
- ARGO-2538 Packages missing for a given distro should be reported
- ARGO-2549 Improve return messages from argo_poem_packages
* Wed Jul 8 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.3-1%{?dist}
- ARGO-2471 Create dry-run for argo-poem-tools
- ARGO-2456 Fetching packages fails when API is unavailable
* Mon Mar 16 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.2-1%{?dist}
- ARGO-2292 Load parameters from config file
* Fri Feb 28 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.1-1%{?dist}
- ARGO-2266 Refactor argo-poem-tools to handle new tags in package
* Thu Feb 20 2020 Katarina Zailac <kzailac@srce.hr> - 0.1.0-1%{?dist}
- ARGO-2230 Create script which will install packages for given metric profiles
