# -*- coding: utf-8 -*-
import anymarkup
import copy
import logging
import os

from collections import defaultdict
from string import Template

from atomicapp.constants import (APP_ENT_PATH,
                                 EXTERNAL_APP_DIR,
                                 GLOBAL_CONF,
                                 MAIN_FILE)
from atomicapp.utils import Utils
from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.nulecule.container import DockerHandler

logger = logging.getLogger(__name__)


class Nulecule(NuleculeBase):
    """
    This represents an application compliant with Nulecule specification.
    A Nulecule instance can have instances of Nulecule and Nulecule as
    components. A Nulecule instance knows everything about itself and its
    componenents, but does not have access to it's parent's scope.
    """
    def __init__(self, id, specversion, metadata, graph, basepath,
                 requirements=None, params=None, config=None,
                 namespace=GLOBAL_CONF):
        super(Nulecule, self).__init__(basepath, params, namespace)
        self.id = id
        self.specversion = specversion
        self.metadata = metadata
        self.graph = graph
        self.requirements = requirements
        self.config = config or {}

    @classmethod
    def unpack(cls, image, dest, config=None, namespace=GLOBAL_CONF,
               nodeps=False, dryrun=False, update=False):
        """
        Pull and extracts a docker image to the specified path, and loads
        the Nulecule application from the path.

        Args:
            image: String, a Docker image name.
            dest: String, destination path where Nulecule data from Docker
                  image should be extracted.
            config: Dictionary, config data for Nulecule application.
            namespace: String, namespace for Nulecule application.
            nodeps: Boolean, don't pull external Nulecule dependencies when
                    True.
            update: Boolean, don't update contents of destination directory
                    if False, else update it.

        Returns:
            A Nulecule instance, or None in case of dry run.
        """
        logger.info('Unpacking image: %s to %s' % (image, dest))
        docker_handler = DockerHandler(dryrun=dryrun)
        docker_handler.pull(image)
        docker_handler.extract(image, APP_ENT_PATH, dest)
        return cls.load_from_path(
            dest, config=config, namespace=namespace, nodeps=nodeps,
            dryrun=dryrun, update=update)

    @classmethod
    def load_from_path(cls, src, config=None, namespace=GLOBAL_CONF,
                       nodeps=False, dryrun=False, update=False):
        """
        Load a Nulecule application from a path in the source path itself, or
        in the specified destination path.

        Args:
            src: String, path to load Nulecule application from.
            config: Dictionary, config data for Nulecule application.
            namespace: String, namespace for Nulecule application.
            nodeps: Boolean. Do not pull external applications if True.
            dryrun: Boolean. Do not make any change to underlying host.
            update: Boolean, update existing application if True, else
                    reuse it.

        Returns:
            A Nulecule instance or None in case of some dry run (installing
            from image).
        """
        nulecule_path = os.path.join(src, MAIN_FILE)
        if dryrun and not os.path.exists(nulecule_path):
            return
        nulecule_data = anymarkup.parse_file(nulecule_path)
        nulecule = Nulecule(config=config, basepath=src,
                            namespace=namespace, **nulecule_data)
        nulecule.load_components(nodeps, dryrun)
        return nulecule

    def run(self, provider_key=None, dryrun=False):
        """
        Runs a nulecule application.

        Args:
            provider_key: String, provider to use for running Nulecule
                          application
            dryrun: Boolean, Do not make changes to host when True
        """
        provider_key, provider = self.get_provider(provider_key, dryrun)
        for component in self.components:
            component.run(provider_key, dryrun)

    def stop(self, provider_key=None, dryrun=False):
        provider_key, provider = self.get_provider(provider_key, dryrun)
        # stop the Nulecule application
        for component in self.components:
            component.stop(provider_key, dryrun)

    def uninstall(self):
        # uninstall the Nulecule application
        for component in self.components:
            component.uninstall()

    def load_config(self, config=None, ask=False, skip_asking=False):
        """
        Load config data for the entire Nulecule application, by traversing
        through all the Nulecule components in a DFS fashion.

        It updates self.config.

        Args:
            config: A dictionary, existing config data, may be from ANSWERS
                    file or any other source.
        """
        super(Nulecule, self).load_config(
            config=config, ask=ask, skip_asking=skip_asking)
        for component in self.components:
            # FIXME: Find a better way to expose config data to components.
            #        A component should not get access to all the variables,
            #        but only to variables it needs.
            component.load_config(config=copy.deepcopy(self.config),
                                  ask=ask, skip_asking=skip_asking)
            self.merge_config(self.config, component.config)

    def load_components(self, nodeps=False, dryrun=False):
        components = []
        for node in self.graph:
            node_name = node['name']
            source = Utils.getSourceImage(node)
            component = NuleculeComponent(
                node_name, self.basepath, source,
                node.get('params'), node.get('artifacts'))
            component.load(nodeps, dryrun)
            components.append(component)
        self.components = components

    def render(self, provider_key=None, dryrun=False):
        """
        Render the artifact files for the entire Nulecule application from
        config data.

        Args:
            provider_key: String, provider for which artifacts need to be
                          rendered. If it's None, we render artifacts for
                          all providers.
            dryrun: Boolean, do not make any change to the host system when
                    True
        """
        for component in self.components:
            component.render(provider_key=provider_key, dryrun=dryrun)


class NuleculeComponent(NuleculeBase):
    """
    Represents a component in a Nulecule application. It receives props
    from it's parent and can add new props and override props at it's local
    scope. It does not have direct access to props of sibling Nulecule
    components, but can request the value of sibling's property from it's
    parent.
    """
    def __init__(self, name, basepath, source=None, params=None,
                 artifacts=None, config=None):
        super(NuleculeComponent, self).__init__(basepath, params, name)
        self.name = name
        self.source = source
        self.artifacts = artifacts
        self.rendered_artifacts = defaultdict(list)
        self._app = None

    def load(self, nodeps=False, dryrun=False):
        if not self.artifacts:
            if nodeps:
                logger.info(
                    'Skipping to load external application: %s' % self.name)
            else:
                self.load_external_application(dryrun)

    def run(self, provider_key, dryrun=False):
        if self._app:
            self._app.run(provider_key, dryrun)
            return
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        provider.deploy()

    def stop(self, provider_key=None, dryrun=False):
        if self._app:
            self._app.stop(provider_key, dryrun)
            return
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        provider.undeploy()

    def load_config(self, config=None, ask=False, skip_asking=False):
        super(NuleculeComponent, self).load_config(
            config, ask=ask, skip_asking=skip_asking)
        if isinstance(self._app, Nulecule):
            self._app.load_config(config=copy.deepcopy(self.config),
                                  ask=ask, skip_asking=skip_asking)
            self.merge_config(self.config, self._app.config)

    def load_external_application(self, dryrun=False, update=False):
        """
        Loads an external application for the NuleculeComponent.

        Args:
            dryrun: Boolean. When True, skips pulling an external application.
            update: Boolean. When True, it ignores an already pulled external
                    application, and tries to pull the external application
                    and update the existing one.

        Returns:
            A Nulecule instance or None
        """
        nulecule = None
        external_app_path = os.path.join(
            self.basepath, EXTERNAL_APP_DIR, self.name)
        if os.path.isdir(external_app_path) and not update:
            logger.info(
                'Found existing external application for %s. '
                'Loading it.' % self.name)
            nulecule = Nulecule.load_from_path(
                external_app_path, dryrun=dryrun, update=update)
        elif not dryrun:
            logger.info('Pulling external application for %s.' % self.name)
            nulecule = Nulecule.unpack(
                self.source,
                external_app_path,
                namespace=self.namespace,
                dryrun=dryrun,
                update=update
            )
        self._app = nulecule

    @property
    def components(self):
        if self._app:
            return self._app.components

    def render(self, provider_key=None, dryrun=False):
        """
        Render the artifact files for the Nuelcule component. If the component
        is an external Nulecule application, recurse into it to load it and
        render it's artifacts. If provider_key is specified, render artifacts
        only for that provider, else, render artifacts for all providers.

        Args:
            provider_key (str or None): Provider name.

        Returns:
            None
        """
        if self._app:
            self._app.render(provider_key=provider_key)
            return
        context = self.get_context()
        for provider in self.artifacts:
            if provider_key and provider != provider_key:
                continue
            for artifact_path in self.get_artifact_paths_for_provider(
                    provider):
                self.rendered_artifacts[provider].append(
                    self.render_artifact(artifact_path, context))

    def get_artifact_paths_for_provider(self, provider_key):
        """
        Get artifact file paths of a Nulecule component for a provider.

        Args:
            provider_key (str): Provider name

        Returns:
            list: A list of artifact paths.
        """
        artifact_paths = []
        artifacts = self.artifacts.get(provider_key)
        for artifact in artifacts:
            if isinstance(artifact, basestring):
                path = Utils.sanitizePath(artifact)
                path = os.path.join(self.basepath, path) \
                    if path[0] != '/' else path
                artifact_paths.append(path)
            elif isinstance(artifact, dict) and artifact.get('inherit') and \
                    isinstance(artifact.get('inherit'), list):
                for inherited_provider_key in artifact.get('inherit'):
                    artifact_paths.extend(
                        self.get_artifact_paths_for_provider(
                            inherited_provider_key)
                    )
            else:
                logger.error('Invalid artifact file')
        return artifact_paths

    def render_artifact(self, path, context):
        """
        Render artifact file at path with context to a file at the same
        level. The rendered file has a name a dot '.' prefixed to the
        name of the the source artifact file.

        Args:
            path (str): path to the artifact file
            context (dict): data to render in the artifact file

        Returns:
            str: Relative path to the rendered artifact file from the
                 immediate parent Nuelcule application
        """
        basepath, tail = os.path.split(path)
        render_path = os.path.join(basepath, '.{}'.format(tail))

        with open(path, 'r') as f:
            content = f.read()
            template = Template(content)
            rendered_content = template.safe_substitute(context)

        with open(render_path, 'w') as f:
            f.write(rendered_content)

        render_path = render_path.split(
            self.basepath + ('' if self.basepath.endswith('/') else '/'),
            1)[1]
        return render_path
