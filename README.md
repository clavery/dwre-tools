# dwre-tools

Various tools for use with Demandware instances. Written in python

## References

- [Export Cheat Sheet](EXPORT-CHEAT-SHEET.md)
- [Migrations Cheat Sheet](CHEAT-SHEET.md)

## Installation

### Easy Method

Copy this command into your terminal (must have a suitable version of python: see [Windows Notes](#Windows_Notes) blow):

```sh
pip install --upgrade https://devops-pixelmedia-com.s3.amazonaws.com/packages-374e8dc7/dwre-tools-latest.zip
# or if using python3 
pip install --upgrade https://devops-pixelmedia-com.s3.amazonaws.com/packages-374e8dc7/dwre-tools-latest.zip
```

### Development

```sh
python setup.py develop
```

### Windows Notes

Recommend using the Anaconda distribution of python as it comes pre-installed with many useful packages with native binaries: [http://continuum.io/downloads](http://continuum.io/downloads).

### OS X Notes

Highly recommend using the latest homebrew version of python **and** installing libxml2 from homebrew. Additionally you should run `brew doctor` and ensure any dependencies it complains about are satisfied (like having XCode with Command Line Tools installed)

```sh
brew install libxml2
brew install python3
```

## Config Setup
The tools requires at least one environment setup in your `.dwre.json` file.

- On windows: `C:\Users\[username]\.dwre.json`
- On Mac/Linux: `${HOME}/.dwre.json`

### Example File

```javascript
{
  "defaultProject" : "vbi",
  "projects" : {
    "vbi" : {
      "defaultEnvironment" : "dev02",
      "environments": {
        "dev02" : {
          "username" : "clavery",
          "password" : "password",
          "codeVersion" : "clavery",
          "server" : "dev02-us-vibram.demandware.net"
        }
      }
    }
  }
}
```

## Usage

Use the command line help to get updated commands/syntax:

All subcommands also have a help with `-h` or `--help`


```sh
$ dwre --help
```

Be default, all commands will execute against the default project specified in your .dwre.json file. If you'd like to use one of the alternative projects, you can use the `--project` flag.

```sh
$ dwre --project XXX
```


### `tail`

The tail command outputs and follows logfiles on your default or specified instance:

```
usage: dwre tail [-h] [-f FILTERS] [-i I]

optional arguments:
  -h, --help            show this help message and exit
  -f FILTERS, --filters FILTERS
                        logfile prefix filter [default 'warn,error,fatal']
  -i I                  refresh interval in seconds [default 5]
```

### `validate`

The validate command will validate an XML file or directory tree against the DWRE schemas included in the module.

```
usage: dwre validate [-h] target

positional arguments:
  target      filename or directory to validate

optional arguments:
  -h, --help  show this help message and exit
```

### `reindex`

The `reindex` subcommand will initiate a rebuild of all search indexes in the environment. This will rebuild across all sites configured.

```sh
dwre reindex
```

### `migrate`

The migrate command will perform "site imports" against the specified instance in the order specified in the `migrations.xml` file inside the migrations directory (default directory name: `migrations`).

#### Installation

This command requires that the cartridge `bm_dwremigrate` be installed and activated into the business manager site and that the BM user to be used is given the appropriate BM module permissions ("DWREMigrate"). **NOTE: As of version 1.5.0 the DWRE tools can perform this activation and access role step for you. The cartridge must simply be uploaded to the current code version (i.e. through eclipse or `dwre sync`**

- Copy the `bm_dwremigrate` directory into your project's cartridges directory. In Eclipse, import the cartridge into your project and link it to the Demandware server. Perform a full upload.
- In the Business Manager, go to *Administration -> Manage Sites*. Under the *Business Manager Site* section, click on the *Manage the Business Manager site* link. Add `bm_dwremigrate` to the end of the cartidge path.
- Go to *Administration -> Roles &amp; Permissions*. Select the user used to manage the site. Select the Business Manager Modules tab. Check the entry for `DWREMigrate` and click *Update*.

This command also requires that metadata be added to the instance however this will be done automatically, if required, at first run time. Metadata will also be automatically added as a migration in future versions.

An example `migrations.xml` follows (the XML will be validated against a schema in the module at run time):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<migrations xmlns="http://www.pixelmedia.com/xml/dwremigrate">
	<migration id="2015-07-10_initial">
		<description>Initial Site Migration</description>
		<location>2015-07-10_initial</location>
	</migration>
	<migration id="2015-07-10_m2">
		<description>m2 description</description>
		<location>2015-07-10_m2</location>
		<parent>2015-07-10_initial</parent>
	</migration>
	<migration id="2015-07-10_m3">
		<location>2015-07-10_m3</location>
		<parent>2015-07-10_m2</parent>
	</migration>
</migrations>
```

The command has a number of subcommands

```
usage: dwre migrate [-h] [-n] [-d DIR]
                    {add,apply,validate,reset,run,set,runall} ...

optional arguments:
  -h, --help            show this help message and exit
  -n                    test run; do not execute migrations
  -d DIR, --dir DIR     migrations directory (default: migrations)

Sub Commands:
  {add,apply,validate,reset,run,set,runall}
    add                 add a new migration
    apply               apply migrations to environment
    validate            validate migrations directory
    reset               reset migration state to current code version
    run                 run a single site import without validating or
                        updating migrations
    set                 set the current migration version
    runall              run all migrations not currently applied without
                        validating or updating/applying migrations
```

#### Adding a Migration

```sh
usage: dwre migrate add [-h] [-d DESCRIPTION] [-r] [--hotfix] [--id ID]
                        directory

positional arguments:
  directory             migration directory (within migrations/)

optional arguments:
  -h, --help            show this help message and exit
  -d DESCRIPTION, --description DESCRIPTION
                        description of migration (default: empty)
  -r, --rename          rename folder to generated or specified ID
  --hotfix              create migration as a hotfix
  --id ID               id of migration (default: generated)
```

Use the `--hotfix` switch when adding a migration to add it as a hotfix. i.e. `dwre migrate add --hotfix -r -d 'some hotfix' hotfixdir`

### `export`

This commands opens a web browser with the ability to create an export file in the same manner
as business manager. It will then automatically download, extract and cleanup in business manager.

This command is intended to streamline the process of making migrations.

```
usage: dwre export [-h] directory

positional arguments:
  directory   destination directory

optional arguments:
  -h, --help  show this help message and exit
```

### `update`

This performs a self-update of the tools

### `sync`

The `sync` command syncs cartridges found in the current directory (and all subdirectories) to the specified server and code version (or default)

### `debug`

The `debug` command launches an interactive Script Debugging session with the specified instance and breakpoints given on the command line (filename:line_num). At least one breakpoint is required.

Some commands once launched (most are only relevant on a HALTED thread; i.e. a breakpoint has been hit)

- `continue,c` - continue execution to next breakpoint or running
- `next,n` - continue to next line, over any functions
- `into,i` - continue into function on current line
- `out,o` - jump out of function
- `print,p [objectpath] [re]` - prints the current stack frame members or a specific member/member path; if `re` is specified will further filter down the list to those matching (case insensitively) the regex pattern specified. (i.e. `p order total` to see members with names containing "total" in the order object)
- `stack,s` - print stack frame
- `list,l` - print current code surrounding breakpoint
- `eval,e` - eval an expression in the context of the HALTED thread.

Additionally any commands not defined will instead be "evaled" as if they were passed to the `eval` command (i.e. "1+2" will echo 3)

## Development / Contributing

To install in development mode first ensure the package is uninstalled

```sh
pip uninstall dwre_tools
```

Then run `pip install -e .[dev]` in the root directory to install the package in development mode. You can use a virtual environment to further contain the dependencies. (Note: the `[dev]` specification means install the extras used for development, like testing tools.

### Testing

Install testing requirements (already done if you installed in `[dev]` mode above) with: `pip install -e .[test]`

Tests are created via docstrings and the unittest modules in `dwre_tools/tests/`. We use the `pytest` library to simplify test discovery and flexibility.

The simplest way to run the tests is to run `python setup.py test` which will ensure the correct test libraries are installed. This will use `pytest` under the hood (as configured in `setup.py`)

`tox` is used to test multiple python versions at once. In particular we test against python 2.7 and python 3.6. See the `tox.ini` file for the setup. Run it with: `tox`. This will read the `tox.ini` and execute the test suite(s) in each environment.

**Note: it is a good idea to run the full test suite with `tox` before publishing code or new versions to ensure some manner of test coverage over both python2 and py3**

### Testing Tips

- Use the `responses` library and decorator to mock responses to the `requests` library (which is used for all http requests)
- Use the `unittest.mock` (or just `mock` in py2) to mock uncontrolled libraries like some filesystem and other standard library functions.
- Use the data in the `testdata` directory to simulate existing projects (i.e. migration directories and XML files). Use the `setUp` and `tearDown` methods to copy to a temporary directory for testing live filesystem affecting code.
- The quickest and most informative way to run tests is to use `pytest` directly and use verbose mode: `pytest --pyargs dwre_tools -v`.

## Todo

- Abstract sessions for all commands to better support session management (SSL, etc)
- Proper logging instead of print statements w/ "disable color if not a TTY"

## Notes

### Running Against Staging Server (Two Factor Auth)

You'll need a certificate and public key signed by CA key received from DWRE.

```sh
dwre --server cert.staging.web.stonewall.demandware.net \
--username clavery \
--password passwordhere \
--noverify \
--clientcert ~/code/swk/pki/cert.staging.web.stonewall.demandware.net_01.crt \
--clientkey ~/code/swk/pki/cert.staging.web.stonewall.demandware.net_01.key \
migrate -n apply
```

# License

This software is Copyright 2015-2017 PixelMEDIA, Inc. All Rights Reserved.

Use of this software is only allowed under the expressed written permission of PixelMEDIA, Inc. Any other use is strictly prohibited.
