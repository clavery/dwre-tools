# dwre-tools

Various tools for use with Demandware instances. Written in python

## Installation

```sh
pip install git+ssh://git@bitbucket.org/pixelmedia/dwre-dwre-tools.git#egg=DwreTools
```

__Windows Users__: Recommend using the Anaconda distribution of python as it comes pre-installed with many useful packages with native binaries: [http://continuum.io/downloads](http://continuum.io/downloads).

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

```sh
$ dwre --help
```
