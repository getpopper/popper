import click
import os
import sys
import popper.utils as pu
from popper.cli import pass_context
from io import BytesIO
import requests
import json

# For compatibility between python 2.x and 3.x versions
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


@click.command(
    'search',
    short_help='Used to search for an experiment in your pipeline folder')
@click.argument('keywords', required=False)
@click.option(
    '--skip-update',
    help=('Skip updating the metadata and search on the local cache'),
    is_flag=True
)
@click.option(
    '--add',
    help=('Add an org/repo to the popperized list in .popper.yml'),
)
@click.option(
    '--rm',
    help=('Remove an org/repo from the popperized list in .popper.yml'),
)
@click.option(
    '--ls',
    help=('List all the repositories available to search'),
    is_flag=True
)
@pass_context
def cli(ctx, keywords, skip_update, add, rm, ls):
    """Searches for pipelines on GitHub matching the given keyword(s).

    The list of repositories or organizations scraped for Popper pipelines is
    specified in the 'popperized' list in the .popper.yml file. By default,
    https://github.com/popperized is added to the configuration.

    If no keywords are specified, a list of all the pipelines from all
    organizations (in the .popper.yml file) and repositories will be returned.

    Example:

        popper search quiho

    would result in:

        popperized/quiho-popper

    To add or remove orgs/repos to/from the 'popperized' ,
    use the --add and --rm flags while searching.

        popper search --add org/repo

    To remove an organization/person do:

        popper search --rm org/repo

    To view the list repositories that are available to the search command:

        popper search --ls

    """
    if (rm or add or ls) and (keywords):
        pu.fail("'add', 'rm' and 'ls' flags cannot be combined with others.")

    project_root = pu.get_project_root()

    config = pu.read_config()
    popperized_list = config['popperized']

    if add:
        add = 'github/' + add
        if add not in popperized_list:
            popperized_list.append(add)

        config['popperized'] = popperized_list
        pu.write_config(config)
        sys.exit(0)

    if rm:
        rm = 'github/' + rm
        if rm in popperized_list:
            popperized_list.remove(rm)

        config['popperized'] = popperized_list
        pu.write_config(config)
        sys.exit(0)

    gh_token = os.environ.get('POPPER_GITHUB_API_TOKEN', None)

    headers = {}
    if gh_token:
        headers = {
            'Authorization': 'token ' + gh_token
        }

    result = []  # to store the result of the search query as a list

    if ls:
        for p in popperized_list:
            if p.count('/') == 1:
                org_name = p.split('/')[1]
                org_url = ('https://api.github.com/users/{}/repos')
                org_url = org_url.format(org_name)

                response = requests.get(org_url, headers=headers)

                if response.status_code != 200:
                    pu.fail("Unable to connect. Please check your network"
                            " and try again.")
                else:
                    repos = response.json()
                    temp = [r["full_name"] for r in repos]
                    result.extend(temp)
            else:
                result.extend(p[7:])

        if len(result) > 0:
            pu.info("The list of available poppperized repositories are:\n")
            pu.print_yaml(result)
            sys.exit()
        else:
            fail_msg = "There are no popperized repositores available"
            "for search. Use the --add flag to add an org/repo."

            pu.fail(fail_msg)

        sys.exit(0)

    empty_query = False

    if not keywords:  # checks if the query is empty or not
        empty_query = True

    cache_dir = os.path.join(project_root, '.cache')

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    for popperized in popperized_list:
        if popperized.count('/') == 1:
            # it is an organization
            org_name = popperized.split('/')[1]

            repos = ""

            if not skip_update:
                org_url = ('https://api.github.com/users/{}/repos'
                           .format(org_name))

                response = requests.get(org_url, headers=headers)

                if response.status_code != 200:
                    pu.fail("Unable to connect. Please check your network"
                            " and try again.")

                with open(os.path.join(cache_dir, org_name + '_repos.json'),
                          'w') as f:
                    json.dump(response.json(), f)

            try:
                with open(os.path.join(cache_dir, org_name + '_repos.json'),
                          'r') as f:
                    repos = json.load(f)
            except FileNotFoundError:
                pu.fail('No cached metadata has been downloaded')

            with click.progressbar(
                    repos,
                    show_eta=False,
                    label='Searching in ' + org_name,
                    bar_template='[%(bar)s] %(label)s | %(info)s',
                    show_percent=True) as bar:

                for r in bar:
                    if l_distance(r["name"].lower(),
                                  keywords.lower()) < 1:
                        temp = ' {}/{}' \
                            .format(org_name, r['name'])
                        result.append(temp)

                    else:
                        result.extend(
                            search_pipeline(
                                r["url"],
                                keywords,
                                org_name,
                                empty_query,
                                gh_token,
                                cache_dir,
                                skip_update))
        else:
            # it is a repository
            user, repo = popperized.split('/')[1:]
            repo_url = ('https://api.github.com/repos/{}/{}'
                        .format(user, repo))

            headers = {}
            pu.info("Searching in repository : {}".format(repo))
            result.extend(
                search_pipeline(repo_url, keywords,
                                user, empty_query, gh_token,
                                cache_dir, skip_update)
            )

    if len(result) != 0:
        pu.info("\nSearch results:\n", fg="green")
        pu.print_yaml(result)
    else:
        pu.fail("Unable to find any matching pipelines")


def search_pipeline(repo_url, keywords, org_name, empty_query,
                    gh_token, cache_dir, skip_update):
    """Searches for the pipeline inside a github repository.
       Word level levenshtein distances are being calculated to find
       appropriate results for a given query.
    """

    repo_name = repo_url.split('/')[-1]
    results = []

    pipelines = ""
    headers = {}
    if gh_token:
        headers = {'Authorization': 'token ' + gh_token}

    if not skip_update:
        pipelines_url = repo_url + "/contents/pipelines"

        response = requests.get(pipelines_url, headers=headers)

        if response.status_code != 200:
            return results

        else:
            with open(os.path.join(cache_dir, repo_name + '.json'), 'w') as f:
                json.dump(response.json(), f)
    try:
        with open(os.path.join(cache_dir, repo_name + '.json'), 'r') as f:
            pipelines = json.load(f)
    except FileNotFoundError:
        return results

    for pipeline in pipelines:
        if empty_query:
            temp = "{}/{}/{}".format(org_name, repo_name, pipeline['name'])
            results.append(temp)

        else:
            if l_distance(keywords.lower(),
                          pipeline['name'].lower()) < 1:

                temp = "{}/{}/{}" \
                    .format(org_name, repo_name, pipeline['name'])

                readme_url = "https://raw.githubusercontent.com"
                readme_url += "/{}/{}/master".format(org_name, repo_name)
                readme_url += "/pipelines/{}/README.md".format(
                    pipeline['name'])

                r = requests.get(readme_url, headers=headers)
                if r.status_code != 200:
                    pass
                else:
                    content = str(BytesIO(r.content).getvalue(), 'utf-8')
                    # print(type(content)
                    content = "\n".join(content.split("\n")[:3])
                    temp += "\n" + content + "..."

                results.append(temp)

    return results


def l_distance(a, b):
    """ A modified version of the Levenshtein Distance algorithm to find
    word level edit distances between two sentences. """

    arr1 = a.split("-")
    arr2 = b.split("-")

    l1 = len(arr1)
    l2 = len(arr2)

    dist = [[0 for j in range(l2 + 1)] for i in range(l1 + 1)]

    dist[0][0] = 0

    for i in range(1, l1 + 1):
        dist[i][0] = i
    for i in range(1, l2 + 1):
        dist[0][i] = i

    for i in range(1, l1 + 1):
        for j in range(1, l2 + 1):
            temp = 0 if arr1[i - 1] == arr2[j - 1] else 1
            dist[i][j] = min(dist[i - 1][j] + 1, dist[i][j - 1] + 1,
                             dist[i - 1][j - 1] + temp)

    ldist = float(dist[l1][l2]) / max(l1, l2)

    return ldist
