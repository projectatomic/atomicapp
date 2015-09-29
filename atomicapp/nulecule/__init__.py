# -*- coding: utf-8 -*-
import anymarkup
import copy
import logging
import os
import subprocess
import uuid
from atomicapp.utils import Utils

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
    def __init__(self, id, specversion, metadata, graph, requirements=None,
                 params=None, config=None, namespace='general'):
        self.id = id
        self.specversion = specversion
        self.metadata = metadata
        self.graph = graph
        self.requirements = requirements
        self.params = params or []
        self.namespace = namespace
        self.config = self.load_config(config, self.params, self.namespace)
        self.load()

    @classmethod
    def load_from_dir(cls, path, config={}):
        nulecule_data = anymarkup.parse_file(
            os.path.join(path, 'Nulecule'))
        return Nulecule(config=config, **nulecule_data)

    def load(self):
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
                node_name, node.get('source'), node.get('params'),
                node.get('artifacts'), config=config)
            if self.config.get(node_name) is None:
                self.config[node_name] = {}
            self.config[node_name].update(component.config.get(node_name))
            components.append(component)
        return components

    def run(self):
        # run the Nulecule application
        pass

    def stop(self):
        # stop the Nulecule application
        pass

    def install(self):
        # install the Nulecule application
        pass

    def uninstall(self):
        # uninstall the Nulecule application
        pass


class NuleculeComponent(NuleculeBase):
    """
    Represents a component in a Nulecule application. It receives props
    from it's parent and can add new props and override props at it's local
    scope. It does not have direct access to props of sibling Nulecule
    components, but can request the value of sibling's property from it's
    parent.
    """
    def __init__(self, name, source=None, params=None, artifacts=None, config=None):
        self.name = name
        self.source = source
        self.params = params or []
        self.artifacts = artifacts
        self.config = self.load_config(config, self.params, name)
        self.app = None
        self.load()

    def load(self):
        dest = '/tmp/nulecule-{}'.format(uuid.uuid1())
        if not self.artifacts:
            self.load_external_application(dest)

    def load_external_application(self, dest):
        docker_handler = DockerHandler()
        docker_handler.pull(self.source)
        container_dir = 'application-entity'
        docker_handler.extract(self.source, container_dir, dest)
        nulecule = Nulecule.load_from_dir(
            os.path.join(dest, container_dir),
            config=copy.deepcopy(self.config))
        nulecule.load()
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
        container_id = subprocess.check_output(run_cmd).strip()
        cp_cmd = [self.docker_cli, 'cp',
                  '%s:/%s' % (container_id, source),
                  dest]
        subprocess.call(cp_cmd)
        rm_cmd = [self.docker_cli, 'rm', '-f', container_id]
        subprocess.call(rm_cmd)

    def is_image_present(self, image):
        ps = subprocess.Popen([self.docker_cli, 'images'],
                              stdout=subprocess.PIPE)
        output = subprocess.check_output(['grep', image], stdin=ps.stdout)
        ps.wait()
        if len(output.strip().splitlines()) > 0:
            return True
        return False
