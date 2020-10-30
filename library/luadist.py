#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Antonio Torres <atorresm@protonmail.com>
# GNU General Public License v3.0
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: luadist

short_description: Manage Lua environment and packages via LuaDist

version_added: "2.10"

description: 
    - Manage Lua environment and packages via LuaDist. The user can 
      define a list of packages to install and the directory to install
      the Lua development environment and required packages.

options:
    path:
        description: The path to install the Lua environment to.
        required: true
        type: str
    package:
        description: Name of a Lua package to install.
        type: list
        elements: str
    allow_dists:
        description: Dists types allowed.
        type: str
        choices: [ all, binary, source ]
        default: all
    dists_repo:
        description: Repo to install dists from.
        default: "git://github.com/LuaDist/Repository.git"
        type: str

author:
    - Antonio Torres (@antoniotorresm)
'''

EXAMPLES = r'''
- name: Create Lua environment
  luadist:
    path: /home/myuser/lua

- name: Create Lua environment with additional packages
  luadist:
    path: /home/myuser/lua
    package:
      - luacurl
      - luagl
      - md5

- name: Create Lua environment with custom repo and only using binary dists
  luadist:
    path: /home/myuser/lua
    allow_dists: binary
    dists_repo: "git://example.org/myluarepo.git"
    package:
      - luacurl
      - luagl
      - md5
'''

RETURN = r''' # '''

import os

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        path=dict(type='str', required=True),
        package=dict(type='list', elements='str'),
        allow_dists=dict(type='str', default='all',
            choices=["all", "binary", "source"]),
        dists_repo=dict(type='str', default="git://github.com/LuaDist/Repository.git")
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    path = module_args["path"]
    packages = module_args["package"]
    allow_dists = module_args["allow_dists"]
    dists_repo = module_args["dists_repo"]

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(changed=False)

    state_changed = False

    # Setup the Lua environment in the desired path
    if not _luadist_is_present(path):
        state_changed = True
        _setup_luadist(module, path)

    # Ensure desired packages are installed
    all_present = True
    for package in packages:
        if not _is_present(module, path, package):
            all_present = False
            break
    if not all_present:
        state_changed = True
        _install_packages(module, path, packages, allow_dists, dists_repo)

    module.exit_json(changed=state_changed)


def _luadist_is_present(path):
    '''Returns whether luadist environment is in the specified path'''
    os.chdir(path)
    return os.path.exists("LuaDist/bin/luadist")


def _setup_luadist(module, path):
    '''Creates luadist environment in the specified path'''
    cmd = 'echo "$(curl -fksSL https://tinyurl.com/luadist)" | bash'
    module.run_command(cmd, cwd=path)


def _is_present(module, path, pkgname):
    '''Returns whether package is installed'''
    cmd = "./LuaDist/bin/luadist list " + pkgname
    _, out, _ = module.run_command(cmd, cwd=path)
    return pkgname in out


def _install_packages(module, path, packages, allowed_dists, repo):
    '''Installs the specified packages'''
    cmd = "./LuaDist/bin/luadist install "

    # Add packages to command
    for package in packages:
        cmd += package + " "

    # Add types of dists allowed to command
    source_allowed = "true"
    binary_allowed = "true"
    if allowed_dists == "binary":
        source_allowed = "false"
    elif allowed_dists == "source":
        binary_allowed = "false"
    cmd += " -source=" + source_allowed + " -binary=" + binary_allowed

    # Add repository to command
    cmd += ' --repo="' + repo + '"'

    _, out, _ = module.run_command(cmd, cwd=path)

    if not "Installation succesful" in out:
        module.fail_json(msg =
            'Cannot install one or more of the specified packages, ' +
            'make sure all packages exist in the configured repository.')


def main():
    run_module()


if __name__ == '__main__':
    main()
