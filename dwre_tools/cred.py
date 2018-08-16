"""SSM Credentials Retrieval and Storage"""
from __future__ import print_function

import sys
import re
import pprint

import botocore
import boto3

from colorama import Fore


def err(*args, **kwargs):
    print("%s%s%s" % (Fore.RED, str(*args), Fore.RESET), file=sys.stderr, **kwargs)


def get_credential(name):
    client = boto3.client('ssm')
    try:
        resp = client.get_parameter(Name=name, WithDecryption=True)
    except botocore.exceptions.NoCredentialsError as e:
        print(Fore.RED + "Unable to connect to AWS; do you have IAM credentials?" + Fore.RESET)
        sys.exit(1)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            err("Credential not found")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            err("Credential found but you do not have the permissions to access/decrypt")
        else:
            err("Unknown error: %s".format(e.response['Error']['Code']))
        sys.exit(1)
    print(resp.get("Parameter").get("Value"))


def get_credential_info(name):
    client = boto3.client('ssm')
    try:
        resp = client.describe_parameters(Filters=[{
            'Key': 'Name',
            'Values': [name]
        }])
    except botocore.exceptions.NoCredentialsError as e:
        print(Fore.RED + "Unable to connect to AWS; do you have IAM credentials?" + Fore.RESET)
        sys.exit(1)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            err("Credential not found")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            err("Credential found but you do not have the permissions to access/decrypt")
        else:
            err("Unknown error: %s".format(e.response['Error']['Code']))
        sys.exit(1)
    pprint.pprint(resp.get('Parameters')[0], indent=2)


def put_credential(name, value, description=''):
    client = boto3.client('ssm')
    if description is None:
        description = ''
    try:
        resp = client.put_parameter(Name=name, Value=value, Type='SecureString',
                                    Description=description, Overwrite=True)
    except botocore.exceptions.NoCredentialsError as e:
        print(Fore.RED + "Unable to connect to AWS; do you have IAM credentials?" + Fore.RESET)
        sys.exit(1)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            err("Credential not found")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            err("Access denied writing parameter")
        else:
            err("Unknown error: %s".format(e.response['Error']['Code']))
        sys.exit(1)
    print("OK. Wrote version %s of %s" % (resp['Version'], name))


def list_credentials(param_filter=None):
    client = boto3.client('ssm')
    try:
        parameters = []
        resp = client.describe_parameters(MaxResults=50)
        parameters = parameters + resp.get('Parameters')
        while resp.get('NextToken'):
            resp = client.describe_parameters(MaxResults=50, NextToken=resp.get('NextToken'))
            parameters = parameters + resp.get('Parameters')

        if param_filter is not None:
            regex = re.compile(param_filter)
        else:
            regex = re.compile('')

        parameters = [p for p in parameters
                      if regex.search(p.get('Name'))]
    except botocore.exceptions.NoCredentialsError as e:
        print(Fore.RED + "Unable to connect to AWS; do you have IAM credentials?" + Fore.RESET)
        sys.exit(1)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            err("Credential not found")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            err("Access denied writing parameter")
        else:
            err("Unknown error: {}".format(e.response['Error']['Code']))
        sys.exit(1)
    [print(p.get('Name')) for p in parameters]
