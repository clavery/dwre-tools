
# Release Notes

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
