### install dependencies
# required packages:
# azure-nspkg azure-mgmt-nspkg azure-common azure-cli-core msrestazure azure-graphrbac ...



try:
    from azure.common import credentials
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.batch import BatchManagementClient
    from azure.mgmt.batch.models import BatchAccountCreateParameters, AutoStorageBaseProperties
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.subscription import SubscriptionClient
    from azure.graphrbac import GraphRbacManagementClient
    from azure.graphrbac.models import ServicePrincipalCreateParameters
except ImportError:
    import pip
    pip.main(['install', '--force-reinstall', '--upgrade', '--user', 'azure==3.0.0'])
    from azure.common import credentials
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.batch import BatchManagementClient
    from azure.mgmt.batch.models import BatchAccountCreateParameters, AutoStorageBaseProperties
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
    from azure.mgmt.subscription import SubscriptionClient
    from azure.graphrbac import GraphRbacManagementClient
    from azure.graphrbac.models import ServicePrincipalCreateParameters


class AccountSetupError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class DefaultSettings():
    resource_group = 'aztk'
    storage_account = 'aztk-storage'
    batch_account = 'aztk-batch'
    service_principal = 'aztksp'


def create_resource_group(credentials, subscription_id):
    resource_client = ResourceManagementClient(credentials, subscription_id)
    resource_client.resource_groups.list()


def create_storage_account(credentials, subscription_id):
    storage_management_client = StorageManagementClient(credentials, subscription_id)
    storage_account = storage_management_client.storage_accounts.create(
        resource_group_name="",
        account_name="",
        parameters=StorageAccountCreateParameters(
            sku=Sku(SkuName.standard_lrs),
            kind=Kind.storageV2,
            localtion=""
        )
    )
    return storage_account.id



def create_batch_account(credentials, subscription_id):
    batch_management_client = BatchManagementClient(credentials, subscription_id)
    batch_account = batch_management_client.batch_account.create(
        resource_group_name="",
        account_name="",
        parameters=BatchAccountCreateParameters(
            location="",
            auto_storage=AutoStorageBaseProperties(
                storage_account_id=""
            )
        )
    )
    return batch_account.id

def create_vnet(credentials, subscription_id):
    pass


def create_aad_user(credentials, tenant_id):
    print(credentials, tenant_id)
    graph_rbac_client = GraphRbacManagementClient(credentials, tenant_id)
    print([sp for sp in graph_rbac_client.service_principals.list()])
    # graph_rbac_client.service_principals.create(ServicePrincipalCreateParameters(app_id="aztkaccount", account_enabled=True))


def format_secrets(**kwargs):
    pass


def prompt_with_default(key, value):
    pass



# get credentials and tenant_id
credentials, subscription_id = credentials.get_azure_cli_credentials()
subscription_client = SubscriptionClient(credentials)
tenant_ids = [tenant.tenant_id for tenant in subscription_client.tenants.list()]
if len(tenant_ids) != 1:
    raise AccountSetupError("More than one tenant configured on your subscription.")
else:
    tenant_id = tenant_ids[0]

# create resource group
create_resource_group(credentials, subscription_id)

# create storage account
create_storage_account(credentials, subscription_id)

# create batch account
create_batch_account(credentials, subscription_id)

# create vnet
create_vnet(credentials, subscription_id)

# create service principal
create_aad_user(credentials, tenant_id)
