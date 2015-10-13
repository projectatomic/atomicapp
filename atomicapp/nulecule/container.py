import distutils
import os
import subprocess
import uuid
import logging

from atomicapp.constants import APP_ENT_PATH

logger = logging.getLogger(__name__)


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

    def extract(self, image, source, dest, update=False):
        container_id = None
        run_cmd = [
            self.docker_cli, 'run', '-d', '--entrypoint', '/bin/true', image]
        logger.debug(run_cmd)
        container_id = subprocess.check_output(run_cmd).strip()
        tmpdir = '/tmp/nulecule-{}'.format(uuid.uuid1())
        cp_cmd = [self.docker_cli, 'cp',
                  '%s:/%s' % (container_id, source),
                  tmpdir]
        logger.debug('%s' % cp_cmd)
        subprocess.call(cp_cmd)
        src = os.path.join(tmpdir, APP_ENT_PATH)
        if not os.path.exists(src):
            src = tmpdir
        distutils.dir_util.copy_tree(src, dest, update)
        distutils.dir_util.remove_tree(tmpdir)
        rm_cmd = [self.docker_cli, 'rm', '-f', container_id]
        subprocess.call(rm_cmd)

    def is_image_present(self, image):
        output = subprocess.check_output([self.docker_cli, 'images'])
        image_lines = output.strip().splitlines()[1:]
        for line in image_lines:
            words = line.split()
            image_name = words[0]
            registry = repo = None
            if '/' in image_name:
                registry, repo = image_name.split('/', 1)
            if image_name == image or repo == image:
                return True
        return False
