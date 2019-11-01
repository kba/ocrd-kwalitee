import click
from ocrd.decorators import ocrd_loglevel
from ocrd_utils import getLogger
from yaml import safe_load
import json
from pkg_resources import resource_filename

from .repo import Repo

LOG = getLogger('kwalitee.cli')

def _check_cloned(ctx):
    uncloned = []
    for repo in ctx.repos:
        if not repo.is_cloned():
            uncloned.append(repo)
    if uncloned:
        raise Exception("Some repos not yet cloned: %s" % [str(r) for r in uncloned])

class CliCtx():
    def __init__(self, config_file):
        with open(config_file, 'r') as f_config_file:
            self.config = safe_load(f_config_file.read())
            self.repos = []
            for repo_desc in self.config['repolist']:
                url = repo_desc['url']
                official = repo_desc.get('official', False)
                self.repos.append(Repo(self.config, url, official))
pass_ctx = click.make_pass_decorator(CliCtx)

@click.group()
@click.option('-c', '--config-file', help="", default=resource_filename(__name__, 'config.yml'))
@ocrd_loglevel
@click.pass_context
def cli(ctx, config_file, **kwargs): # pylint: disable=unused-argument
    ctx.obj = CliCtx(config_file)

@cli.command('clone', help='''

        Clone all repos
''')
@pass_ctx
def clone_all(ctx):
    for repo in ctx.repos:
        if repo.is_cloned():
            LOG.info("Already cloned %s" % repo)
        else:
            LOG.info("Cloning %s" % repo)
            repo.clone()

@cli.command('pull', help='''

        Pull all repos
''')
@pass_ctx
def pull_all(ctx):
    _check_cloned(ctx)
    for repo in ctx.repos:
        LOG.info("Pulling %s" % repo)
        repo.pull()


@cli.command('json', help='''

    Generate JSON

''')
@pass_ctx
def generate_json(ctx):
    ret = []
    _check_cloned(ctx)
    for repo in ctx.repos:
        LOG.info("# Assessing %s" % repo.name)
        repo.clone()
        ret.append(repo.to_json())
        #  print('%s %s -> %s' % (repo.path.is_dir(), repo.url, repo.path))
    print(json.dumps(ret, indent=4, sort_keys=True))

@cli.command('venv', help='''

    Install repos to venv
''')
@pass_ctx
def venv(ctx):
    _check_cloned(ctx)
    for repo in ctx.repos:
        LOG.info("%s: installing to venv" % repo)
        repo.install_to_venv()
