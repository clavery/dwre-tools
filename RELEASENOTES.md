
# Release Notes

## 1.14.8

- allow forcing of account manager login

## 1.14.6

- tty detection for sync

## 1.14.5

- support zip files with `migrate run` subcommand
- double time to wait for imports

## 1.14.3

- issue with on demand sandbox login

## 1.14.2

- bugfix error in account manager login

## 1.14.1

- decode `tail` logs as utf-8 with less strict replacement

## 1.14.0

- provisional support for account manager logins for supporting sandboxes (i.e. CCDX/AWS)
    - auto detects when necessary or utilizes environment configuration (`useAccountManager=true`)
- fixes bug in password input when password is not in environment configuration
- adds support for retrieving and storing passwords from the users login keychain
    - should work on macos, windows and linux
    - will ask to store passwords typed in via the password input (requires a terminal)
    - these can be managed with the `dwre pw` set of commands (it will choose the system keychain when the password is NOT stored in `dwre.json`)
- fixes issues with hardcoded public key in GPG support when saving GPG encrypted `dwre.json`
- adds top level configuration key (`accountManager`) to `dwre.json` for storing account manager username and password (also supports keychain) to avoid repeating in environments;
    - `useAccountManager` must be `true` in the environment to use this global configuration

## 1.13.18

- update to 18.10 schemas
- bug fix gpg encryption

## 1.13.17

- dependency issue

## 1.13.16

- fixes initial compatibility issue with CCDX and account manager based federated logins/account merge requests and CSRF tokens

## 1.13.15

- update to 18.9 schemas and docs

## 1.13.14

- exception output fix for windows

## 1.13.13

- regression


## 1.13.12

- bugfixes
- adds `nozip` option to watch

## 1.13.10

- update docs to 18.8
- NEW: adds OCAPI documentation to dash docset

## 1.13.9

- regression in some scenarios with migration uploads due to recent changes

## 1.13.8

- remove workaround for pyyaml python 3.7 issue; should be resolved now with 3.13
- defensive coding for use as library

## 1.13.7

- using latest version of requests library; will fix any windows regressions directly if applicable

## 1.13.5

- regression fix for non-terminal use-cases

## 1.13.4

- update for 18.7
- support zip files for most `migrate` subcommands

## 1.13.3

- bug fixes for beta vim integration


## 1.13.2

- `sync` now has a progress bar

## 1.13.1

- regression from previous release

## 1.13.0

- refactors and updates `debug` to use v2.0 of script debugger; performance enhancements; some initial service unit tests; etc
- creates skeleton for external integration (i.e. direct VIM integration)

## 1.12.0

- adds global `--codeversion` argument to support specification of code version on cli
- adds `zip` command for collecting and zipping cartridges in given path
- sync now supports zip files in addition to directories (still defaults to current dir)
- cleans up some code and further removes deprecated update functionality
- adds `watch` subcommend to replicate watch and upload functionality usually done by nodejs based scripts

## 1.11.1

- deprecating `update` command; Use Pixel Homebrew tap or manually install using python dependency management of choice

## 1.11.0

- deprecating python2

## 1.10.3

- fixes issue with python2

## 1.10.2

- support `dw.json` files if present; falling back to `~/.dwre.json`

## 1.10.1

- 18.6 schema updates; docset update

## 1.10.0

- adds `pw refresh` command to refresh all credentials or report login errors

## 1.9.5

- `tail` will now show deprecation logs by default

## 1.9.4

- updated to 18.4

## 1.9.3

- added a `put` subcommand to `pw` management (BETA: not responsible if this blows us your dwre.json file)

## 1.9.2

- updated to 18.3

## 1.9.1

- adds workaround for `tail` when SFCC webdav does not report content length headers

## 1.9.0

- adds `pw` subcommand to list and retrieve passwords from `.dwre.json`
- adds support for encrypting `.dwre.json` with GnuPG; If a file `.dwre.json.gpg` is found it will be decrypted using the GPG agent of the user; See `README.md` for shell scripts that use this


## 1.8.7

- updated to 18.2

## 1.8.6

- input fix for both py2 and py3

## 1.8.5

- issues with bootstrap zip file

## 1.8.4

- bugfix `tail` command to actually compare file dates and not just tuples

## 1.8.3

- potential fix for edge case migration install

## 1.8.2

- pagination credentials

## 1.8.1

- `update` command will try to better search for installed pip executable
- python compatibility fixes and CLI smoke test UnitTest

## 1.8.0

- adds `cred` command for retrieving shared credentials from AWS (requires an IAM user set up)

## 1.7.0

- adds hotfix migrations capability (`add --hotfix`)
    - hotfixes are stored separately from primary migrations and the context is controlled in a `hotfixes.xml` file
    - hotfixes are not required to match version "path" on server
- slipstream `bm_dwremigrate` cartridge into metadata update if required; tool will recommend running `upgrade-bm-cartridge` if this occurs
- adds `upgrade-bm-cartridge` command to update cartridge in filesystem w/ bundled version
- the tool can now bootstrap the installation of the cartridge, metadata, etc if used by an administrator (i.e. on fresh sandboxes). It will use the active code version.
- Missing migration context files will be created instead of throwing an error.
- Other fixes and refactorings
- Adds unit and integration test suite for various modules (work in progress)

## 1.6.8

- changes necessary for python 3 compatibility
- update to 17.8 schema and docs

## 1.6.7

- better schema map search

## 1.6.6

- consolidating code from magnet tools to use DWRE tools as source library

## 1.6.5

- update to 17.7 docs and schemas

## 1.6.4

- relaxed the version requirements on lxml

## 1.6.3

- update schemas and docs to 17.6
- make more code visible in debugger code output

## 1.6.2

- basic stack/object member completion in `debug` command (press <TAB> to complete)

## 1.6.1

- indicate to user we are launching a browser to localhost:5698

## 1.6.0

- adds `migrate runall` subcommand. This command `run`'s all migrations you do not currently have on your sandbox. It does not check for migration path conflicts nor does it update the sandbox migration path after running (i.e. just like `run` repeated `runall`'s are NOT idempotent). This command is intended for power user and other development/QA scenarios where all missing migrations should be applied but no consistency checking is performed. `apply` should still be used when getting up to date with integration branches.

## 1.5.4

- updates schemas and docs to 17.5

## 1.5.3

- updates schemas and docs to 17.4

## 1.5.2

- more fixes for 17.4 regressions
    - export command
- locking down dependencies for windows users due to jinja2 issue on latest flask
- other fixes

## 1.5.1

- Potential fix for 17.4 breaking changes to CSRF BM protection

## 1.5.0

- DWRE migrate can now add the BM configuration for the BM extension cartridge itself; dwre migrate apply will run an "install" migration prior to bootstrap if the BM cartridge path is missing the extension or the access roles for administrator are not complete. This eliminates a major install step that usually trips up developers. The cartridge must still exist in the current code version (i.e. `dwre sync` first). A future version will also install the latest version of the cartridge if missing.

## 1.4.4

- update schemas and docs to 17.3

## 1.4.3

- debugger supports unicode code files

## 1.4.2

- updates business manager sessions to use CSRF Token as per https://xchange.demandware.com/message/70079#70079

## 1.4.1

- use file history for dwre debug

## 1.4.0

- ignore common large directories in sync
- beta `debug` command

## 1.3.9

- 17.2 schemas

## 1.3.8

- make sync with delete reactivate code version

## 1.3.7

- updates to 17.1; adds new schemas for jobs, etc

## 1.3.0

- Adds `sync` command

## 1.2.1

- Update Schema to 16.5

## 1.2.0

- Changes `migrate run` command to not require migrations context

## 1.1.4

- Updates urlrules XSD to fix invalid pattern

## 1.1.3

- Adds `update` command and better release process

## 1.1.0

- new command: `export`; allows for easy export to quickly make migrations

## 1.0.2

- Increase import time limit

## 1.0.1

- Schema Updates

## 1.0.0

Initial "public API freeze".

- Double retry times in migration import for slow sandboxes
