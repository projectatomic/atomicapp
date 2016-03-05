---
specversion: 0.0.2
id: ${app_name}

metadata:
  name: ${app_name}
  appversion: ${app_version}
  description: ${app_desc}

graph:
  - name: ${app_name}
    params:
      - name: image
        description: Container image to use
        default: centos/httpd
    artifacts:
      kubernetes:
        - file://artifacts/kubernetes/${app_name}_pod.yaml
      docker:
        - file://artifacts/docker/${app_name}_run
