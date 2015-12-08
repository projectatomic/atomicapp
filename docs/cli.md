# Atomic App Command Line Interface (CLI)

## Providers

Providers may be specified using the `answers.conf` file or the `--provider <provider>` option. 
If a provider is not explicitly implied and only one provider exists within the Nulecule container, Atomic App will use said provider.
If neither are detected, Atomic App will use Kubernetes by default.

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

