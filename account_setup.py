import argparse
import json
import subprocess
import yaml

# Colors
class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Default variables
class Defaults:
    command_init = 'init'
    command_get_secretes_shared_key = 'get-shared-key-secrets'
    command_get_secrets = 'get-sp-secrets'
    resource_group = 'aztk'
    storage_account = 'aztkstorage'
    batch_account = 'aztkbatch'
    service_principal = 'aztksp'

def call_shell(commands):
    command = ' '.join(str(x) for x in commands)
    cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, errs = cmd.communicate()
    returncode = cmd.returncode
    return returncode, out.decode("utf-8")

def setup_parsers(parser):
    subparsers = parser.add_subparsers(dest='subparser_name',
                                    help='command help')

    setup_init_parser(subparsers)
    setup_shared_key_secrets_parser(subparsers)
    setup_aad_secrets_parser(subparsers)

def setup_init_parser(subparsers):
    init_parser = subparsers.add_parser('init',
                                        help='A command to initialze a new AZTK environmnent')
    init_parser.add_argument('-r',
                            dest='region',
                            required=True,
                            help='Region to create AZTK resources')
    init_parser.add_argument('-an',
                            dest='aad_name',
                            default=Defaults.service_principal,
                            help='AAD Service Principal name. [Default = "{}"].'
                                .format(Defaults.service_principal))
    init_parser.add_argument('-pw',
                            dest='aad_password',
                            help='AAD Service Principal password. If not specified, a strong\
                            password will be created automatically.')
    init_parser.add_argument('-rg',
                            default=Defaults.resource_group,
                            dest='resource_group',
                            help='Resource group name. Will create a new one if it doesn''t exist.\
                            Default = ["{}"]'.format(Defaults.resource_group))
    init_parser.add_argument('-ba',
                            default=Defaults.batch_account,
                            dest='batch_account',
                            help='Batch account name. Will create a new one if it doesn''t exist.\
                            Default = ["{}"]'.format(Defaults.batch_account))
    init_parser.add_argument('-sa',
                            default=Defaults.storage_account,
                            dest='storage_account',
                            help='Storage account name. Will create a new one if it doesn''t exist.\
                            Default = ["{}"]'.format(Defaults.storage_account))

def setup_shared_key_secrets_parser(subparsers):
    sk_secrets_parser = subparsers.add_parser('get-shared-key-secrets',
                                              help="A command to generate your secrets file using shared-key auth.")
    sk_secrets_parser.add_argument('-rg',
                            default=Defaults.resource_group,
                            dest='resource_group',
                            help='Resource group name. Default = ["{}"]'.format(Defaults.resource_group))
    sk_secrets_parser.add_argument('-ba',
                            default=Defaults.batch_account,
                            dest='batch_account',
                            help='Batch account name. Default = ["{}"]'.format(Defaults.batch_account))
    sk_secrets_parser.add_argument('-sa',
                            default=Defaults.storage_account,
                            dest='storage_account',
                            help='Storage account name. Default = ["{}"]'.format(Defaults.storage_account))

def setup_aad_secrets_parser(subparsers):
    sp_secrets_parser = subparsers.add_parser('get-sp-secrets',
                                                help="A command to generate your secrets file using AAD auth using a Service Principal.")
    sp_secrets_parser.add_argument('-tid',
                            dest='tenant_id',
                            required=True,
                            help='Tenant ID of the Service Principal')
    sp_secrets_parser.add_argument('-cid',
                            dest='client_id',
                            required=True,
                            help='Client ID of the Service Principal')
    sp_secrets_parser.add_argument('-pw',
                            dest='password',
                            required=True,
                            help='Password for the Service Principal')
    sp_secrets_parser.add_argument('-rg',
                            default=Defaults.resource_group,
                            dest='resource_group',
                            help='Resource group name. Default = ["{}"]'.format(Defaults.resource_group))
    sp_secrets_parser.add_argument('-ba',
                            default=Defaults.batch_account,
                            dest='batch_account',
                            help='Batch account name. Default = ["{}"]'.format(Defaults.batch_account))
    sp_secrets_parser.add_argument('-sa',
                            default=Defaults.storage_account,
                            dest='storage_account',
                            help='Storage account name. Default = ["{}"]'.format(Defaults.storage_account))

def parse_sp_user_output(return_code, data):
    if (return_code > 0):
        print('There was an error creating the Service Principal. Aborting.\
        Resource may have been created but will not be charged for unless used.')
        return None
    return json.loads(data)

def parse_create_resource_group_output(return_code, data):
    if (return_code > 0):
        print('There was an error creating the Resource Group. Aborting.\
        Resource may have been created but will not be charged for unless used.')
        return None
    return json.loads(data)

def parse_create_storage_account_output(return_code, data):
    if (return_code > 0):
        print('There was an error creating the Storage account. Aborting.\
        Resource may have been created but will not be charged for unless used.')
        return None
    return json.loads(data)

def parse_create_batch_account_output(return_code, data):
    if (return_code > 0):
        print('There was an error creating the Batch account. Aborting.\
        Resource may have been created but will not be charged for unless used.')
        return None
    return json.loads(data)

def build_secrets_with_aad(aad_data, batch_data, storage_data):
    password = '[YOUR_AAD_USER_PASSWORD]'
    if 'password' in aad_data:
        password = str(aad_data['password'])

    tenant_id = '[YOUR_AAD_TENATN_ID]'
    if 'tenant' in aad_data:
        tenant_id = str(aad_data['tenant'])
    elif 'appOwnerTenantId' in aad_data['additionalProperties']:
        tenant_id = str(aad_data['additionalProperties']['appOwnerTenantId'])

    data = dict(
        service_principal = dict(
            tenant_id = tenant_id,
            client_id = str(aad_data['appId']),
            credential = password,
            batch_account_resource_id = str(batch_data['id']),
            storage_account_resource_id = str(storage_data['id'])
        ),
        default = dict(
            ssh_public_key = '~/.ssh/id_rsa.pub'
        )
    )

    # Note, this will dump the keys in alphabetical order.
    secrets_file = yaml.dump(data, default_flow_style=False)
    return secrets_file

def create_aad_user(args):
    # check if user exists, if so do not create.
    aad_user = {};
    commands = []
    commands.append('az')
    commands.append('ad')
    commands.append('sp')
    commands.append('show')
    commands.append('--id')
    commands.append('http://{}'.format(args.aad_name))
    commands.append('-o')
    commands.append('json')
    aad_user_result_code, aad_user_result_data = call_shell(commands)
    if aad_user_result_code == 0:
        # user exists
        print('AAD user {} already exists. Collecting required information'.format(args.aad_name))
        print(bcolors.WARNING + "Warning: The user you requested already exists. This script will reuse it. \
The password is not stored so we cannot access it again. Please replace the 'credential' section of the file \
with your password. More information on regenerating a password for a user can be found here: https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli?view=azure-cli-latest#reset-credentials" + bcolors.ENDC)
        aad_user = parse_sp_user_output(aad_user_result_code, aad_user_result_data)
    else:
        # build and run the service principal commands
        print('Creating AAD user {}'.format(args.aad_name))
        print(bcolors.WARNING + "Warning: The credentials will only be shown here once and are not stored. \
Make sure to copy this some place safe as they cannot be regenerated " + bcolors.ENDC)
        commands = []
        commands.append('az')
        commands.append('ad')
        commands.append('sp')
        commands.append('create-for-rbac')
        commands.append('-n')
        commands.append(args.aad_name)
        if args.aad_password is not None:
            commands.append('-p')
            commands.append(args.aad_password)
        commands.append('-o')
        commands.append('json')
        aad_user_result_code, aad_user_result_data = call_shell(commands)
        aad_user = parse_sp_user_output(aad_user_result_code, aad_user_result_data)
    return aad_user

def create_resource_group(args):
    # build and run the resource group commands
    commands = []
    commands.append('az')
    commands.append('group')
    commands.append('create')
    commands.append('-n')
    commands.append(args.resource_group)
    commands.append('-l')
    commands.append(args.region)
    commands.append('-o')
    commands.append('json')
    print('Creating Resource group {}'.format(args.resource_group))
    code, data = call_shell(commands)
    resource_group = parse_create_resource_group_output(code, data)

def create_storage_account(args):
    # build and run the storage account commands
    commands = []
    commands.append('az')
    commands.append('storage')
    commands.append('account')
    commands.append('create')
    commands.append('--name')
    commands.append(args.storage_account)
    commands.append('--sku')
    commands.append('Standard_LRS')
    commands.append('--location')
    commands.append(args.region)
    commands.append('--resource-group')
    commands.append(args.resource_group)
    commands.append('-o')
    commands.append('json')
    print('Creating Storage account {}'.format(args.storage_account))
    code, data = call_shell(commands)
    storage_account = parse_create_storage_account_output(code, data)
    return storage_account

def create_batch_account(args):
    # build and run the batch account commands
    commands = []
    commands.append('az')
    commands.append('batch')
    commands.append('account')
    commands.append('create')
    commands.append('--name')
    commands.append(args.batch_account)
    commands.append('--storage-account')
    commands.append(args.storage_account)
    commands.append('--location')
    commands.append(args.region)
    commands.append('--resource-group')
    commands.append(args.resource_group)
    commands.append('-o')
    commands.append('json')
    print('Creating Batch account {}'.format(args.batch_account))
    code, data = call_shell(commands)
    batch_account = parse_create_batch_account_output(code, data)

def process_init_command(args):
    aad_user = create_aad_user(args)
    if aad_user is None:
        return

    resource_group = create_resource_group(args)
    if resource_group is None:
        return

    storage_account = create_storage_account(args)
    if storage_account is None:
        return

    batch_account = create_batch_account(args)
    if batch_account is None:
        return

    # generage the secrets.yaml file
    print()
    secrets_file = build_secrets_with_aad(aad_user, batch_account, storage_account)
    print('Copy the following text into you secrets.yaml file:\n')
    print(secrets_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup AZTK environment')
    setup_parsers(parser)
    args = parser.parse_args()

    commands = []
    if args.subparser_name == 'init':
        process_init_command(args)
    else:
        print('command not supported')
