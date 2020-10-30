# luadist_test

This role provides support for handling Lua environments and packages via LuaDist. Intended as a programming exercise.

## Role Variables

#### `packages`
List of packages to install in the Lua environment. These packages
must be present in the repository specified in the `dists_repo` variable.

#### `env_directory`
Where to create the Lua environment. All Lua related packages will be 
installed in this directory. This must be an absolute path.

#### `allow_dists`
Type of dists to allow when installing packages. Values can be:

* `all`: All types of dists are allowed.
* `source`: Only dists that are built from source are allowed.
* `binary`: Only dists that are distributed as binaries are allowed.

#### `dists_repo`
Directory to use as package repository. Must follow [LuaDist guidelines](https://github.com/LuaDist/Repository/wiki/LuaDist:-Configuration#repositories).

## Dependencies

None

## Example Playbook

```yaml
- hosts: all
  tasks:
    - name: Install Lua environment with packages
      import_role:
        name: luadist_test
      vars:
        env_directory: "/opt"
        allow_dists: "all"
        packages:
          - md5
          - luagl
    - name: Demonstrate role is idempotent
      import_role:
        name: luadist_test
      vars:
        env_directory: "/opt"
        allow_dists: "all"
        packages:
          - md5
          - luagl
```

## License

MIT License.
