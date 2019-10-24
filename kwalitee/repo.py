from pathlib import Path
import json
from subprocess import run, PIPE
from shlex import split as X
from ocrd_utils import pushd_popd, getLogger

LOG = getLogger('kwalitee.repo')


class Repo():

    def __init__(self, config, url):
        self.url = url
        self.config = config
        self.name = Path(url).name
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
        with pushd_popd(self.path):
            ret['number_of_commits'] = self._run('git rev-list HEAD --count').stdout
            ret['last_commit'] = self._run(r'git log -1 --format=%cd ').stdout
        return ret

    def get_file_contents(self):
        ret = {}
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
        return ret

    def to_json(self, git=True, python=True, files=True):
        desc = {}
        desc['url'] = self.url
        desc['org_plus_name'] = '/'.join(self.url.split('/')[-2:])
        desc['name'] = self.name
        if files:
            desc['files'] = self.get_file_contents()
            if desc['files']['ocrd-tool.json']:
                desc['ocrd_tool'] = json.loads(desc['files']['ocrd-tool.json'])
                with pushd_popd(self.path):
                    desc['ocrd_tool_validate'] = self._run('ocrd ocrd-tool ocrd-tool.json validate').stdout
            else:
                desc['ocrd_tool'] = ''
                desc['ocrd_tool_validate'] = 'NO ocrd-tool.json'
        if git:
            desc['git'] = self.get_git_stats()
        if python:
            desc['python'] = self.get_python_info()
        return desc

    def _run(self, cmd, **kwargs):
        result = run(X(cmd), stdout=PIPE, encoding='utf-8', **kwargs)
        if result.stdout:
            result.stdout = result.stdout.strip()
        return result
