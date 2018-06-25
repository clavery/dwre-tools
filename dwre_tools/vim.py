# vim integration
import json

def vim_call(func, *args):
    args = json.dumps(['call', func, args])
    print(f'\x1b]51;{args}\x07')
