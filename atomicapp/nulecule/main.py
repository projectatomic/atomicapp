# -*- coding: utf-8 -*-
import anymarkup
import copy
import logging
import os
import shutil

from atomicapp.constants import (GLOBAL_CONF,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 ANSWERS_FILE,
                                 ANSWERS_FILE_SAMPLE,
                                 ANSWERS_RUNTIME_FILE,
                                 DEFAULT_NAMESPACE,
                                 DEFAULT_PROVIDER,
                                 MAIN_FILE)
from atomicapp.nulecule.base import Nulecule
from atomicapp.utils import Utils

logger = logging.getLogger(__name__)


class NuleculeManager(object):

    @staticmethod
    def do_install(APP, answers, nodeps=False, update=False, target_path=None,
                   dryrun=False, answers_format=ANSWERS_FILE_SAMPLE_FORMAT,
                   **kwargs):
        m = NuleculeManager()
        m.install(APP, answers, target_path, nodeps, update, dryrun,
                  answers_format, **kwargs)
        return m

    @staticmethod
    def do_run(answers, APP, cli_provider, answers_output, ask=False,
               answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        m = NuleculeManager()
        m.run(APP, answers, cli_provider, answers_output, ask,
              answers_format=answers_format, **kwargs)
        return m

    @staticmethod
    def do_stop(APP, cli_provider, **kwargs):
        m = NuleculeManager()
        m.stop(APP, cli_provider, **kwargs)
        return m

    def __init__(self):
        self.APP = None
        self.answers = {}
        self.answers_format = None

    def unpack(self, image, unpack_path, update=False, dryrun=False,
               nodeps=False):
        logger.debug('Unpacking %s to %s' % (image, unpack_path))
        if not os.path.exists(os.path.join(unpack_path, MAIN_FILE)) or \
                update:
            logger.debug(
                'Nulecule application found at %s. Unpacking and updating...'
                % unpack_path)
            return Nulecule.unpack(image, unpack_path, nodeps=nodeps,
                                   dryrun=dryrun, update=update)
        else:
            logger.debug(
                'Nulecule application found at %s. Loading...')
            return Nulecule.load_from_path(unpack_path, dryrun=dryrun)

    def install(self, APP, answers, target_path=None, nodeps=False,
                update=False, dryrun=False,
                answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        self.answers = Utils.loadAnswers(
            answers or os.path.join(APP, ANSWERS_FILE))
        self.answers_format = answers_format or ANSWERS_FILE_SAMPLE_FORMAT
        target_path = target_path or os.getcwd()
        if os.path.exists(APP):
            Utils.copy_dir(APP, target_path, dryrun=dryrun)
            # Since directory is not copied to target_path during dry run
            # we fall back to load the app from APP.
            self.nulecule = Nulecule.load_from_path(
                APP if dryrun else target_path, dryrun=dryrun, update=update,
                config=self.answers)
        else:
            self.nulecule = self.unpack(APP, target_path, update, dryrun,
                                        config=self.answers)
        self.nulecule.load_config(config=self.nulecule.config)
        runtime_answers = self._get_runtime_answers(
            self.nulecule.config, None)
        self._write_answers(os.path.join(target_path, ANSWERS_FILE_SAMPLE),
                            runtime_answers, answers_format,
                            dryrun=dryrun)

    def run(self, APP, answers, cli_provider, answers_output, ask,
            answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        self.answers = Utils.loadAnswers(
            answers or os.path.join(APP, ANSWERS_FILE))
        self.answers_format = answers_format or ANSWERS_FILE_SAMPLE_FORMAT
        dryrun = kwargs.get('dryrun') or False
        if os.path.exists(APP):
            self.nulecule = Nulecule.load_from_path(APP, config=self.answers,
                                                    dryrun=dryrun)
            app_path = APP
        else:
            app_path = os.getcwd()
            self.nulecule = Nulecule.unpack(APP, app_path, update=True,
                                            dryrun=dryrun,
                                            config=self.answers)
        self.nulecule.load_config(config=self.nulecule.config)
        self.nulecule.render(cli_provider, dryrun)
        self.nulecule.run(cli_provider, dryrun)
        runtime_answers = self._get_runtime_answers(
            self.nulecule.config, cli_provider)
        self._write_answers(os.path.join(app_path, ANSWERS_RUNTIME_FILE),
                            runtime_answers,
                            self.answers_format, dryrun=dryrun)
        if answers_output:
            self._write_answers(answers_output, runtime_answers,
                                self.answers_format, dryrun)

    def stop(self, APP, cli_provider, **kwargs):
        self.answers = Utils.loadAnswers(
            os.path.join(APP, ANSWERS_RUNTIME_FILE))
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

    def _write_answers(self, path, answers, answers_format, dryrun=False):
        if not dryrun:
            anymarkup.serialize_file(
                answers, path, format=answers_format)
        else:
            logger.info('ANSWERS: %s' % answers)

    def _get_runtime_answers(self, config, cli_provider):
        _config = copy.deepcopy(config)
        _config[GLOBAL_CONF] = config.get(GLOBAL_CONF) or {}
        _config[GLOBAL_CONF]['provider'] = cli_provider or \
            _config[GLOBAL_CONF].get('provider') or DEFAULT_PROVIDER
        _config[GLOBAL_CONF]['namespace'] = _config[GLOBAL_CONF].get(
            'namespace') or DEFAULT_NAMESPACE
        return _config
