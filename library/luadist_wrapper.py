#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Antonio Torres <atorresm@protonmail.com>
# GNU General Public License v3.0
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: luadist_wrapper

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
    name:
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
"""

EXAMPLES = r"""
- name: Create Lua environment
  luadist_wrapper:
    path: /home/myuser/lua

- name: Create Lua environment with additional packages
  luadist_wrapper:
    path: /home/myuser/lua
    name:
      - luacurl
      - luagl
      - md5

- name: Create Lua environment with custom repo and only using binary dists
  luadist_wrapper:
    path: /home/myuser/lua
    allow_dists: binary
    dists_repo: "git://example.org/myluarepo.git"
    name:
      - luacurl
      - luagl
      - md5
"""

RETURN = r"""
cmd:
  description: luadist command used by the module
  returned: success
  type: str
  sample: ./LuaDist/bin/luadist install -source=true -binary=true md5 luagl -repos="git://github.com/LuaDist/Repository.git"
name:
  description: List of Lua packages present in the environment
  returned: success
  type: list
  sample: ['md5', 'luagl']
env_path:
  description: path where the Lua environment is located
  returned: success
  type: str
  sample: /home/luauser/lua
"""

import os

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        path=dict(type="str", required=True),
        name=dict(type="list", elements="str"),
        allow_dists=dict(
            type="str", default="all", choices=["all", "binary", "source"]
        ),
        dists_repo=dict(type="str", default="git://github.com/LuaDist/Repository.git"),
    )

    module = AnsibleModule(argument_spec=module_args)

    path = module.params["path"]
    packages = module.params["name"]
    allow_dists = module.params["allow_dists"]
    dists_repo = module.params["dists_repo"]

    # define module result
    result = dict(changed=False, cmd="", env_path=path, name=packages)

    # Setup the Lua environment in the desired path
    if not _luadist_is_present(path):
        result["changed"] = True
        _setup_luadist(module, path)

    # Ensure desired packages are installed
    all_present = True
    for package in packages:
        if not _is_present(module, path, package):
            all_present = False
            break
    if not all_present:
        result["changed"] = True
        result["cmd"] = _install_packages(
            module, path, packages, allow_dists, dists_repo
        )

    module.exit_json(**result)


def _luadist_is_present(path):
    """Returns whether luadist environment is in the specified path"""
    return os.path.exists(os.path.join(path, "LuaDist/bin/luadist"))


def _setup_luadist(module, path):
    """Creates luadist environment in the specified path"""
    cmd = "curl -fksSL https://tinyurl.com/luadist | bash"
    ret_code, out, err = module.run_command(cmd, cwd=path, use_unsafe_shell=True)
    if not _luadist_is_present(path):
        module.fail_json(
            rc=ret_code,
            stdout=out,
            stderr=err,
            msg="Cannot create LuaDist environment in the specified path.",
        )


def _is_present(module, path, pkgname):
    """Returns whether package is installed"""
    cmd = "./LuaDist/bin/luadist list " + pkgname
    ret_code, out, err = module.run_command(cmd, cwd=path)
    if ret_code != 0:
        module.fail_json(
            rc=ret_code,
            stdout=out,
            stderr=err,
            msg="Cannot check the status of one or more packages.",
        )
    return pkgname in out


def _install_packages(module, path, packages, allowed_dists, repo):
    """Installs the specified packages. Returns the command used for installation"""
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
    cmd += ' -repos="' + repo + '"'

    ret_code, out, err = module.run_command(cmd, cwd=path)
    already_installed = "No packages to install" in out

    if ret_code != 0 and not already_installed:
        module.fail_json(
            rc=ret_code,
            stdout=out,
            stderr=err,
            msg="Cannot install one or more of the specified packages, "
            + "make sure all packages exist in the configured repository.",
        )

    return cmd


def main():
    run_module()


if __name__ == "__main__":
    main()
