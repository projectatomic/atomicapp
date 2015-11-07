# Providers

Provider is a way for **atomicapp** to interact with a container engine.
Currently, **atomicapp** has support for multiple providers:
- docker
- kubernetes
- openshift
- docker-compose


## Adding a new provider

It's pretty simple to add a new provider to **atomicapp**.
Create a new file, say, ``your_provider.py`` in this package, i.e.,
``atomicapp.providers``, and edit it as required, following the snippet
below.

```
import logging
import os
import subprocess
from atomicapp.plugins import Provider

logger = logging.getLogger(__name__)


class YourProvider(Provider):
    """Your provider"""

    # identifier string for this provider
    key = 'new-provider'

    def init(self):
        """Do any initialization required for your provider"""
        ...
        ...
        ...


    def deploy(self):
        """
        Deploy containers or similar entities on provider.

        You'll need to access the following instance attributes here:
        - path: basepath of the Nulecule application
        - artifacts: A list of relative paths (from basepath of Nulecule
                     application) to artifacts for this provider
        - dryrun: whether it's a dryrun or not
        """
        ...
        ...
        ...
        from artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            # Do something with artifact file
            ...
            ...
            ...
            cmd = ['command', 'to', 'deploy', 'artifact', 'on',
                   'new-provider']
            if self.dryrun:
                # print log
                logger.info('DRY-RUN: %s', " ".join(cmd))
            else:
                subprocess.check_call(cmd)
        ...
        ...
        ...

     def undeploy(self):
        """
        Undeploy container or similar entities on provider.

        You'll need to access the following instance attributes here:
        - path: basepath of the Nulecule application
        - artifacts: A list of relative paths (from basepath of Nulecule
                     application) to artifacts for this provider
        - dryrun: whether it's a dryrun or not
        """
        ...
        ...
        ...
        from artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            # Do something with artifact file
            ...
            ...
            ...
            cmd = ['command', 'to', 'undeploy', 'artifact', 'on',
                   'new-provider']
            if self.dryrun:
                # print log
                logger.info('DRY-RUN: %s', " ".join(cmd))
            else:
                subprocess.check_call(cmd)
        ...
        ...
        ...
```
Yay! You have successfully written a new provider.
