from pathlib import Path
import json
from subprocess import run, PIPE
from shlex import split as X
from tempfile import mkdtemp

from ocrd_utils import pushd_popd, getLogger
import requests as R

LOG = getLogger('kwalitee.repo')


class Repo():

    def __init__(self, config, url, official=False):
        self.url = url
        self.config = config
        self.name = Path(url).name
        self.official = official
        self.path = Path(self.config['repodir'], self.name)

    def __str__(self):
        return '<Repo %s @ %s>' % (self.url, self.path)

    def is_cloned(self):
        return self.path.is_dir()

    def pull(self):
        with pushd_popd(self.path):
            self._run('git pull origin master')

    def clone(self):
        if self.is_cloned():
            LOG.debug("Already cloned: %s" % self.path)
            return
        with pushd_popd(self.config['repodir']):
            LOG.debug("Cloning %s" % self.url)
            result = self._run('git clone --depth 1 "%s"' % self.url)
            LOG.debug("Result: %s" % result)


    def get_git_stats(self):
        ret = {}
        LOG.info("  Fetching git info")
        with pushd_popd(self.path):
            ret['number_of_commits'] = self._run('git rev-list HEAD --count').stdout
            ret['last_commit'] = self._run(r'git log -1 --format=%cd ').stdout
            ret['url'] = self._run('git config --get remote.origin.url').stdout
            ret['latest_tag'] = self._run('git describe --abbrev=0 --tags').stdout
        return ret

    def get_file_contents(self):
        ret = {}
        LOG.info("  Getting file contents")
        with pushd_popd(self.path):
            for path in [Path(x) for x in ['ocrd-tool.json', 'Dockerfile', 'README.md', 'setup.py']]:
                if path.is_file():
                    with path.open() as f:
                        ret[path.name] = f.read()
                else:
                    ret[path.name] = None
        return ret

    def get_python_info(self):
        ret = {}
        with pushd_popd(self.path):
            ret['url'] = self._run('python3 setup.py --url').stdout
            ret['name'] = self._run('python3 setup.py --name').stdout
            ret['author'] = self._run('python3 setup.py --author').stdout
            ret['author-email'] = self._run('python3 setup.py --author-email').stdout
        LOG.info("  Fetching pypi info")
        response = R.get('https://pypi.python.org/pypi/%s/json' % ret['name'])
        ret['pypi'] = json.loads(response.text) if response.status_code == 200 else None
        return ret

    def to_json(self):
        desc = {}
        desc['url'] = self.url
        desc['official'] = self.official
        desc['org_plus_name'] = '/'.join(self.url.split('/')[-2:])
        desc['name'] = self.name
        desc['files'] = self.get_file_contents()
        if desc['files']['ocrd-tool.json']:
            desc['ocrd_tool'] = json.loads(desc['files']['ocrd-tool.json'])
            with pushd_popd(self.path):
                desc['ocrd_tool_validate'] = self._run('ocrd ocrd-tool ocrd-tool.json validate').stdout
        else:
            desc['ocrd_tool'] = ''
            desc['ocrd_tool_validate'] = 'NO ocrd-tool.json'
        desc['git'] = self.get_git_stats()
        if desc['files']['setup.py']:
            desc['python'] = self.get_python_info()
        return desc

    def _run(self, cmd, **kwargs):
        result = run(X(cmd), stdout=PIPE, encoding='utf-8', **kwargs)
        LOG.info('%s' % cmd)
        if result.stdout:
            result.stdout = result.stdout.strip()
        return result

    def _run_in_venv(self, venv_dir, cmd, **kwargs):
        cmd = '. %s/bin/activate; %s;' % (venv_dir, cmd)
        LOG.info('$ %s' % cmd)
        result = run(cmd, stdout=PIPE, encoding='utf-8', shell=True, **kwargs)
        if result.stdout:
            result.stdout = result.stdout.strip()
        return result

    def install_to_venv(self, venv_dir=None):
        if not venv_dir:
            venv_dir = mkdtemp(prefix='ocrd-kwalitee-venv-')
            self._run('python -mvenv %s' % (venv_dir))
        self._run_in_venv(venv_dir, 'pip install .')
        return venv_dir
