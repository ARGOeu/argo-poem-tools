%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       Script installs packages on ARGO mon boxes.
Name:          argo-poem-tools
Version:       0.3.0
Release:       1%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel
Requires:      python3-requests


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
