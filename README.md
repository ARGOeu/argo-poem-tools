#argo-poem-tools
Configuration is in file `/etc/argo-poem-tools/argo-poem-tools.conf`. It consists of 2 sections: `[GENERAL]` and `[PROFILES]`. In the first section, tenant hostname and token are defined, and in second, there should be a comma separated list of metric profiles. Profile list must be the same as the one in NCG config file. 

Example config file:
```
[GENERAL]
Host = egi.tenant.com
Token = some-token-1234
[PROFILES]
MetricProfiles = ARGO_TEST, TEST_PROFILE
```

Host should correspond to tenant’s fqdn and token may be obtained from POEM UI. The profiles must be defined in POEM.

The tool is run by calling `argo-poem-packages.py` and it is invoked as a part of NCG configuration. All the output is redirected to syslog.

Example output:
```
2020-03-17 08:06:35,442 - argo-poem-packages - INFO - Sending request for profile(s): ARGO_TEST, TEST_PROFILE
2020-03-17 08:06:37,261 - argo-poem-packages - INFO - Creating YUM repo files...
2020-03-17 08:07:31,091 - argo-poem-packages - INFO - Packages installed: nagios-plugins-lfc-0.9.6, nagios-plugins-argo-0.1.11, nagios-plugins-cert-1.0.0; Packages installed with different version: nagios-plugins-http-2.2.2 -> nagios-plugins-http-2.3.1
2020-03-17 08:07:31,091 - argo-poem-packages - INFO - ok!
```
