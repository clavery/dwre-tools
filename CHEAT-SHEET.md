# DWRE Tools Cheat Sheet

## Migrations

### Test What Migrations Will Be Applied

1. `git pull` to update your working copy

```sh
dwre migrate -n apply
```

The `-n` switch means "dry-run". It will only print what needs to be applied.


### Apply Migrations To Your Sandbox

This will ensure your sandbox is up to date with the current migrations in the repository

1. `git pull` to update your working copy

```sh
dwre migrate apply
```

If any exceptions are output see the Errors section below

### Validate Migration Context

This will ensure that all migrations that are configured are valid. `WARNING`'s are OK. Note this will not validate migrations that have not been adding to `migrations.xml`. For that use the `dwre validate` commands

```sh
dwre migrate validate
```

### Creating a New Migration

Note: All commands should be run from the root project directory.

1. `git pull` to update your working copy
2. Create a `Site Import & Export` export in Business Manager exporting the type of Data or Metadata you wish to migrate
3. Download the zip file of your export
4. Move the extracted zip file into the `migrations/` folder
5. Edit the extracted files; paring down the migration to exactly the items you want
6. Validate the directory: `dwre validate migrations/mymigration`
7. If valid add the migration: `dwre migrate add -r -d "short description" mymigration`
8. `git pull` again to ensure no new migrations have been added in the meantime.
9. `dwre migrate apply` to apply your migration to your own sandbox
10. If everything is ok `git push` to push the migration upstream

## Logging

### Watch logs on your sandbox

This command will "tail" the logs on your current sandbox

```
dwre tail
```

You can add the `-f` switch to specify comma separated log prefixes (defaults to warn,error,fatal) to watch only the logs you are interested in:

```
dwre tail -f custom-chargelogic
```

## Errors

Use this section to debug common errors

### Failure to find status link for migration

```
Exception: Failure to find status link for dwremigrate_20150805T1713_... Check import log.
```

This exception is related to a timing issue.

**Resolution**: Rerun the migration command until they finish. This may require multiple runs.

