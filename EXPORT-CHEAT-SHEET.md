# Site Export Cheat Sheet

## Slot Configurations

- The slot configurations are found in `Sites->SiteName->Slots`
- If the slot references a content asset then that Library needs to be exported as well
- If the slot directly references an image (not recommended) it can be found in `Global Data->Static Resources`

## Content Assets

- Content assets are found in libraries
- There are two types of libraries: Shared and Private Site Library
    - Private Site libraries are always assigned to 1 site
    - Shared libraries can be shared with multiple sites
    - If a site is using a Shared library it's private library will be INACTIVE
    - A site can only use 1 library at a time
- *Shared* libraries are exported from `Libraries`
- *Private* libraries are exported from `Sites->SiteName->Content` AND `Library Static Resources->SiteName`

## MetaData (custom attributes, attribute groups, custom objects, etc)

TODO

## Catalogs

TODO

## Cartridge Paths

TODO
