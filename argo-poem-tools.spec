%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       Script installs packages on ARGO mon boxes.
Name:          argo-poem-tools
Version:       0.2.7
Release:       1%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel

%if 0%{?el7}
Requires:      python36-requests

%else
Requires:      python3-requests

%endif


%description
Script which installs packages on ARGO mon boxes.


%prep
%setup -q


%build
%{py3_build}


%install
%{py3_install "--record=INSTALLED_FILES" }
install --directory %{buildroot}/%{_localstatedir}/log/argo-poem-tools/


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/%{name}/argo-poem-tools.conf
%dir %{python3_sitelib}/%{underscore %{name}}/
%{python3_sitelib}/%{underscore %{name}}/*.py

%attr(0755,root,root) %dir %{_localstatedir}/log/argo-poem-tools/

%changelog
* Thu Apr 4 2024 Katarina Zailac <kzailac@srce.hr> - 0.2.7-1%{?dist}
- ARGO-4502 Generalize method for fetching distro name
* Thu Aug 3 2023 Katarina Zailac <kzailac@srce.hr> - 0.2.6-1%{?dist}
- ARGO-4237 Add flag to install internal metrics
* Tue Jun 28 2022 Katarina Zailac <kzailac@srce.hr> - 0.2.5-1%{?dist}
- AO-657 Include tests in Jenkinsfile for argo-poem-tools
- ARGO-3908 Create separate log file
- ARGO-3888 Package version breaking the tool
* Mon Dec 6 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.4-1%{?dist}
- ARGO-3389 Handle version locking when there is a broken repo
* Fri Oct 8 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.3-1%{?dist}
- ARGO-3236 Add version lock for installed packages
* Thu Jul 29 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.2-1%{?dist}
- ARGO-3178 Package marked to be upgraded when it is not supposed to
* Fri Feb 19 2021 Katarina Zailac <kzailac@srce.hr> - 0.2.1-1%{?dist}
- ARGO-2951 Improve handing of probes versions
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
