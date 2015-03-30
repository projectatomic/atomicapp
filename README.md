# ContainerApp
ContainerApp tool is a reference implementation of [Container Application Specification](https://github.com/aweiteka/containerapp-spec). It can be used to bootstrap container application and to install and run them

## How To

### Create
```
containerapp.py [--dry-run] create APP_NAME
```
### Build
```
containerapp.py [--dry-run] build [TAG]
```
### Install
```
containerapp.py [--dry-run] [-a answers.conf] install [--recursive] APP 
```
### Run
```
containerapp.py [--dry-run] [-a answers.conf] run APP
```

## Providers

Providers represent various deployment targets. They are based on yapsy plugin system and can be added by implementing interface explained in [Providers](providers/README.md)

## Examples

### Mariadb App

### Wordpress App


