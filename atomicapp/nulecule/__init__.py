# -*- coding: utf-8 -*-
import anymarkup
import copy
import logging
import os
import shutil
import subprocess
import uuid
from atomicapp.utils import Utils
from atomicapp.constants import CACHE_DIR, APP_ENT_PATH, EXTERNAL_APP_DIR

logger = logging.getLogger(__name__)


class NuleculeBase(object):
    def load(self):
        pass

    def load_config(self, config, params, namespace):
        for param in params:
            value = config.get(namespace, {}).get(param['name']) or \
                config.get('general', {}).get(param['name']) or \
                param.get('default')
            if value is None:
                value = Utils.askFor(param['name'], param)
            if config.get(namespace) is None:
                config[namespace] = {}
            config[namespace][param['name']] = value
        return config

    def load_params(self, params):
        pass

    def run(self, provider):
        raise NotImplementedError

    def stop(self, provider):
        raise NotImplementedError

    def install(self):
        raise NotImplementedError

    def uninstall(self):
        raise NotImplementedError


class Nulecule(NuleculeBase):
    """
    This represents an application compliant with Nulecule specification.
    A Nulecule instance can have instances of Nulecule and Nulecule as
    components. A Nulecule instance knows everything about itself and its
    componenents, but does not have access to it's parent's scope.
    """
    def __init__(self, id, specversion, metadata, graph, basepath,
                 requirements=None, params=None, config=None,
                 namespace='general'):
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
    def unpack(cls, image, path, config={}):
        docker_handler = DockerHandler()
        docker_handler.pull(image)
        docker_handler.extract(image, APP_ENT_PATH, path)
        nulecule_data = anymarkup.parse_file(
            os.path.join(path, 'Nulecule'))
        nulecule = Nulecule(config=config, basepath=path, **nulecule_data)
        nulecule.load()
        return nulecule

    def load(self, config={}):
        self.config = self.load_config(config, self.params, self.namespace)
        self.components = self.load_components(self.graph)

    def load_components(self, graph):
        components = []
        for node in graph:
            node_name = node['name']
            config = {}
            if node.get('artifacts'):
                config['general'] = copy.deepcopy(self.config.get('general')) or {}
                config[node_name] = copy.deepcopy(self.config.get(node_name)) or {}
            component = NuleculeComponent(
                node_name, self.basepath, node.get('source'),
                node.get('params'), node.get('artifacts'), config=config)
            component.load()
            if self.config.get(node_name) is None:
                self.config[node_name] = {}
            self.config[node_name].update(component.config.get(node_name))
            components.append(component)
        return components

    def install(self):
        for component in self.components:
            component.install()

    def run(self):
        for component in self.components:
            component.run()

    def stop(self):
        # stop the Nulecule application
        for component in self.components:
            component.stop()

    def uninstall(self):
        # uninstall the Nulecule application
        for component in self.components:
            component.uninstall()

    def render(self):
        pass


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
        self.name = name
        self.basepath = basepath
        self.source = source
        self.params = params or []
        self.artifacts = artifacts
        self.config = self.load_config(config, self.params, name)
        self.app = None

    def load(self):
        dest = os.path.join(EXTERNAL_APP_DIR, self.name)
        if not self.artifacts:
            self.load_external_application(dest)

    def load_external_application(self, dest):
        nulecule = Nulecule.unpack(
            self.source,
            os.path.join(self.basepath, EXTERNAL_APP_DIR, self.name),
            config=copy.deepcopy(self.config))
        self.app = nulecule
        self.config = nulecule.config


class DockerHandler(object):
    """Interface to interact with Docker."""

    def __init__(self, docker_cli='/usr/bin/docker'):
        self.docker_cli = docker_cli

    def pull(self, image, update=False):
        if not self.is_image_present(image) or update:
            logger.debug('Pulling Docker image: %s' % image)
            pull_cmd = [self.docker_cli, 'pull', image]
            subprocess.call(pull_cmd)
        else:
            logger.debug('Skipping pulling Docker image: %s' % image)

    def extract(self, image, source, dest):
        container_id = None
        run_cmd = [
            self.docker_cli, 'run', '-d', '--entrypoint', '/bin/true', image]
        logger.debug(run_cmd)
        container_id = subprocess.check_output(run_cmd).strip()
        tmpdir = '/tmp/nulecule-{}'.format(uuid.uuid1())
        cp_cmd = [self.docker_cli, 'cp',
                  '%s:/%s/.' % (container_id, source),
                  tmpdir]
        logger.debug('%s' % cp_cmd)
        subprocess.call(cp_cmd)
        shutil.copytree(os.path.join(tmpdir, APP_ENT_PATH), dest)
        shutil.rmtree(tmpdir)
        rm_cmd = [self.docker_cli, 'rm', '-f', container_id]
        subprocess.call(rm_cmd)

    def is_image_present(self, image):
        output = subprocess.check_output([self.docker_cli, 'images'])
        image_lines = output.strip().splitlines()[1:]
        for line in image_lines:
            words = line.split()
            image_name = words[0]
            registry = repo = None
            if image_name.find('/') >= 0:
                registry, repo = image_name.split('/', 1)
            if image_name == image or repo == image:
                return True
        return False


class NuleculeManager(object):

    def __init__(self, image):
        self.image = image
        self.initialize()

    def initialize(self):
        self.app_name = '{}-{}'.format(
            Utils.sanitizeName(self.image), uuid.uuid1())
        self.nulecule = None
        self.unpack_path = os.path.join(CACHE_DIR, self.app_name)
        self.nulecule = None

    def unpack(self, update=False):
        if not os.path.isdir(self.unpack_path) or update:
            self.nulecule = Nulecule.unpack(self.image, self.unpack_path)

    def install(self):
        self.unpack()
        self.nulecule.install()

    def run(self):
        self.install()
        self.nulecule.run()

    def stop(self):
        self.nulecule.stop()

    def uninstall(self):
        self.stop()
        self.nulecule.uninstall()

    def clean(self, force=False):
        self.uninstall()
        shutil.rmtree(self.unpack_path)
        self.initialize()
