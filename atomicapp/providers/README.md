# Providers

Provider is a way for **atomicapp** to interact with a container engine.
Currently, **atomicapp** has support for multiple providers:
- docker
- kubernetes
- openshift
- docker-compose


## Adding a new provider

It's pretty simple to add a new provider to **atomicapp**.
Create a new file, say, ``your_provider.py`` in the directory
``atomicapp/providers/`` and edit it as required, following the snippet
below.

```
import logging
import os
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
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            # Do something with artifact file
            ...
            ...
            ...
            if self.dryrun:
                # print log
                logger.info(
                    'DRY-RUN: %s',
                    'some message about how container will be deployed')
            else:
                # deploy container
                ...
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
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            # Do something with artifact file
            ...
            ...
            ...
            if self.dryrun:
                # print log
                logger.info(
                    'DRY-RUN: %s',
                    'some message about how container will be undeployed')
            else:
                # undeploy container
                ...
        ...
        ...
        ...
```
Yay! You have successfully written a new provider.
