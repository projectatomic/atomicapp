# -*- coding: utf-8 -*-
import anymarkup
import copy
import distutils
import logging
import os
import shutil
import uuid
from collections import defaultdict
from string import Template

from atomicapp.constants import (APP_ENT_PATH, EXTERNAL_APP_DIR,
                                 GLOBAL_CONF, CACHE_DIR,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 MAIN_FILE)
from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.nulecule.container import DockerHandler
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.utils import Utils

logger = logging.getLogger(__name__)


class NuleculeManager(object):

    @staticmethod
    def do_install(answers, APP, nodeps=False, update=False, target_path=None,
                   answers_format=ANSWERS_FILE_SAMPLE_FORMAT, dryrun=False,
                   **kwargs):
        m = NuleculeManager(answers, answers_format)
        m.install(APP, target_path, nodeps, update, dryrun, **kwargs)
        return m

    @staticmethod
    def do_run(answers, APP, cli_provider, answers_output, ask=False,
               answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        m = NuleculeManager(answers, answers_format)
        m.run(APP, cli_provider, answers_output, ask, **kwargs)
        return m

    @staticmethod
    def do_stop(answers, APP, cli_provider,
                answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        m = NuleculeManager(answers, answers_format)
        m.stop(APP, cli_provider, **kwargs)
        return m

    def __init__(self, answers, answers_format, **kwargs):
        self.answers = Utils.loadAnswers(answers)
        self.answers_format = answers_format
        # self.initialize(unpack_path)

    def initialize(self, unpack_path=None):
        if unpack_path:
            self.unpack_path = unpack_path
        else:
            self.app_name = '{}-{}'.format(
                Utils.sanitizeName(self.image), uuid.uuid1())
            self.nulecule = None
            self.unpack_path = os.path.join(CACHE_DIR, self.app_name)
        self.nulecule = None

    def unpack(self, image, unpack_path, update=False, dryrun=False,
               nodeps=False):
        logger.debug('Unpacking %s to %s' % (image, unpack_path))
        if not os.path.exists(os.path.join(unpack_path, MAIN_FILE)) or \
                update:
            logger.debug(
                'Nulecule application found at %s. Unpacking and updating...'
                % unpack_path)
            Nulecule.unpack(image, unpack_path, nodeps=nodeps,
                            dryrun=dryrun, update=update)
        else:
            logger.debug(
                'Nulecule application found at %s. Loading...')
            return Nulecule.load_from_path(unpack_path, dryrun)

    def install(self, APP, target_path=None, nodeps=False, update=False,
                dryrun=False, **kwargs):
        target_path = target_path or os.getcwd()
        if os.path.exists(APP):
            self.nulecule = Nulecule.load_from_path(
                APP, target_path, dryrun=dryrun)
        else:
            self.nulecule = self.unpack(APP, target_path, update, dryrun)

    def run(self, APP, cli_provider, answers_output, ask, **kwargs):
        if not self.answers:
            self.answers = Utils.loadAnswers(
                os.path.join(APP, 'answers.conf'))
        answers_path = answers_output or os.path.join(APP, 'answers.conf')
        dryrun = kwargs.get('dryrun') or False
        self.nulecule = Nulecule.load_from_path(APP, config=self.answers,
                                                dryrun=dryrun) 
        self.nulecule.run(cli_provider, dryrun)
        self._write_answers(answers_path)

    def stop(self, APP, cli_provider, **kwargs):
        if not self.answers:
            self.answers = Utils.loadAnswers(
                os.path.join(APP, 'answers.conf'))
        dryrun = kwargs.get('dryrun') or False
        self.nulecule = Nulecule.load_from_path(APP, config=self.answers,
                                                dryrun=dryrun)
        self.nulecule.stop(cli_provider, dryrun)

    def uninstall(self):
        self.stop()
        self.nulecule.uninstall()

    def clean(self, force=False):
        self.uninstall()
        shutil.rmtree(self.unpack_path)
        self.initialize()

    def _write_answers(self, path):
        anymarkup.serialize_file(
            self.nulecule.config, path, format=self.answers_format)


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
        self.id = id
        self.specversion = specversion
        self.metadata = metadata
        self.graph = graph
        self.basepath = basepath
        self.requirements = requirements
        self.params = params or []
        self.namespace = namespace
        self.config = None

    @classmethod
    def unpack(cls, image, path, config={}, namespace=GLOBAL_CONF,
               nodeps=False, dryrun=False, update=False):
        if not dryrun:
            docker_handler = DockerHandler()
            docker_handler.pull(image)
            docker_handler.extract(image, APP_ENT_PATH, path)
            return cls.load_from_path(
                path, config=config, namespace=namespace, nodeps=nodeps,
                dryrun=dryrun, update=update)
        else:
            logger.debug('Skipping unpacking image: %s' % image)

    @classmethod
    def load_from_path(cls, src, dest=None, config={}, namespace=GLOBAL_CONF,
                       nodeps=False, dryrun=False, update=False):
        dest = dest or src
        distutils.dir_util.copy_tree(src, dest, update)
        nulecule_data = anymarkup.parse_file(
            os.path.join(dest, 'Nulecule'))
        nulecule = Nulecule(config=config, basepath=dest,
                            namespace=namespace, **nulecule_data)
        nulecule.load_components(nodeps, dryrun)
        return nulecule

    def run(self, provider_key=None, dry=False):
        self.load_config(config=self.config)
        self.render(provider_key)
        provider_key, provider = self.get_provider(provider_key, dry)
        for component in self.components:
            component.run(provider_key, dry)

    def stop(self, provider_key=None, dryrun=False):
        self.load_config(config=self.config)
        self.render(provider_key)
        provider_key, provider = self.get_provider(provider_key)
        # stop the Nulecule application
        for component in self.components:
            component.stop(provider_key, dryrun)

    def uninstall(self):
        # uninstall the Nulecule application
        for component in self.components:
            component.uninstall()

    def load_config(self, config={}):
        super(Nulecule, self).load_config(config=config)
        for component in self.components:
            _config = {}
            _config[GLOBAL_CONF] = copy.deepcopy(
                self.config.get(GLOBAL_CONF)) or {}
            if self.namespace != GLOBAL_CONF:
                _config[GLOBAL_CONF].update(
                    self.config.get(self.namespace) or {})
            _config[component.name] = copy.deepcopy(
                self.config.get(component.name)) or {}
            component.load_config(config=_config)
            self.merge_config(self.config, component.config)

    def load_components(self, nodeps=False, dryrun=False):
        components = []
        for node in self.graph:
            node_name = node['name']
            component = NuleculeComponent(
                node_name, self.basepath, node.get('source'),
                node.get('params'), node.get('artifacts'))
            component.load(nodeps, dryrun)
            components.append(component)
        self.components = components

    def render(self, provider_key=None):
        for component in self.components:
            component.render(provider_key=provider_key)


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
        self.name = self.namespace = name
        self.basepath = basepath
        self.source = source
        self.params = params or []
        self.artifacts = artifacts
        self.rendered_artifacts = defaultdict(list)
        self._app = None

    def load(self, nodeps=False, dryrun=False):
        dest = os.path.join(EXTERNAL_APP_DIR, self.name)
        if not self.artifacts:
            if nodeps:
                logger.debug(
                    'Skipping loading external application: %s' % self.name)
            else:
                self.load_external_application(dest, dryrun)

    def run(self, provider_key, dry=False):
        if self._app:
            self._app.run(provider_key, dry)
            return
        provider_key, provider = self.get_provider(provider_key, dry)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        if not dry:
            provider.deploy()

    def stop(self, provider_key=None, dryrun=False):
        if self._app:
            self._app.stop(provider_key)
            return
        provider_key, provider = self.get_provider(provider_key)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        provider.undeploy()

    def load_config(self, config={}):
        super(NuleculeComponent, self).load_config(config)
        if isinstance(self._app, Nulecule):
            self._app.load_config(config=copy.deepcopy(self.config))
            self.merge_config(self.config, self._app.config)

    def load_external_application(self, dest, dryrun=False, update=False):
        external_app_path = os.path.join(
            self.basepath, EXTERNAL_APP_DIR, self.name)
        if os.path.isdir(external_app_path):
            nulecule = Nulecule.load_from_path(
                external_app_path, dryrun=dryrun, update=False)
        else:
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

    def render(self, provider_key=None):
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
        artifact_paths = []
        artifacts = self.artifacts.get(provider_key)
        for artifact in artifacts:
            if isinstance(artifact, basestring):
                path = Utils.sanitizePath(artifact)
                path = os.path.join(self.basepath, path) \
                    if path[0] != '/' else path
            else:
                logger.error('Invalid artifact file')
                continue
            artifact_paths.append(path)
        return artifact_paths

    def render_artifact(self, path, context):
        basepath, tail = os.path.split(path)
        render_path = os.path.join(basepath, '.{}'.format(tail))

        with open(path, 'r') as f:
            content = f.read()
            template = Template(content)
            rendered_content = template.safe_substitute(context)

        with open(render_path, 'w') as f:
            f.write(rendered_content)

        render_path = render_path.split(
            self.basepath + '' if self.basepath.endswith('/') else '/', 1)[1]
        return render_path
