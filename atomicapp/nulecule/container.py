import distutils
import os
import subprocess
import uuid
import logging

from atomicapp.constants import APP_ENT_PATH

logger = logging.getLogger(__name__)


class DockerHandler(object):
    """Interface to interact with Docker."""

    def __init__(self, dryrun=False, docker_cli='/usr/bin/docker'):
        self.dryrun = dryrun
        self.docker_cli = docker_cli

    def pull(self, image, update=False):
        """
        Pulls a Docker image if not already present in the host.

        Args:
            image: String, container image name
            update: Boolean, always pull image if True even if image already
                    exists on host
        """
        if not self.is_image_present(image) or update:
            logger.info('Pulling Docker image: %s' % image)
            pull_cmd = [self.docker_cli, 'pull', image]
            logger.debug(' '.join(pull_cmd))
            if not self.dryrun:
                subprocess.call(pull_cmd)
        else:
            logger.info('Skipping pulling Docker image: %s' % image)

    def extract(self, image, source, dest, update=False):
        """
        Extracts content from a directory in a Docker image to specified
        destination.

        Args:
            image: String, docker image name
            source: String, source directory in Docker image to copy from
            dest: String, path to destination directory on host
            update: Boolean, update destination directory if it exists when
                    True
        """
        logger.info(
            'Extracting nulecule data from image: %s to %s' % (image, dest))
        if self.dryrun:
            return
        run_cmd = [
            self.docker_cli, 'run', '-d', '--entrypoint', '/bin/true', image]
        logger.debug('Running Docker container: %s' % ' '.join(run_cmd))
        container_id = subprocess.check_output(run_cmd).strip()
        tmpdir = '/tmp/nulecule-{}'.format(uuid.uuid1())
        cp_cmd = [self.docker_cli, 'cp',
                  '%s:/%s' % (container_id, source),
                  tmpdir]
        logger.debug(
            'Copying data from Docker container: %s' % ' '.join(cp_cmd))
        subprocess.call(cp_cmd)
        src = os.path.join(tmpdir, APP_ENT_PATH)
        if not os.path.exists(src):
            src = tmpdir
        logger.debug('Copying nulecule data from %s to %s' % (src, dest))
        distutils.dir_util.copy_tree(src, dest, update)
        logger.debug('Removing tmp dir: %s' % tmpdir)
        distutils.dir_util.remove_tree(tmpdir)
        rm_cmd = [self.docker_cli, 'rm', '-f', container_id]
        logger.debug('Removing Docker container: %s' % ' '.join(rm_cmd))
        subprocess.call(rm_cmd)

    def is_image_present(self, image):
        """
        Check if a Docker image is present in the host.

        Args:
            image: String, Docker image name.
        """
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
