# Atomica App Command Line Interface (CLI)

## Providers

Providers may be specified using the `answers.conf` file or the `--provider <provider>` option. If not specified the kubernetes provider will be used by default.

Sample `answers.conf` file specifying provider

```
[general]
provider = openshift
```

Using the `--provider <provider>` option will override the provider in the answerfile.

### Supported providers

* kubernetes (default)
* openshift
* docker

