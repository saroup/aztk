### install dependencies
# required packages:
# azure-nspkg azure-mgmt-nspkg azure-common azure-cli-core msrestazure azure-graphrbac ...



try:
    from azure.common import credentials
    from azure.cli.core._profile import Profile
    from azure.mgmt.authorization import AuthorizationManagementClient
    from azure.mgmt.authorization.models import RoleAssignmentCreateParameters, RoleDefinitionFilter
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.resource.resources.models import ResourceGroup
    from azure.mgmt.batch import BatchManagementClient
    from azure.mgmt.batch.models import BatchAccountCreateParameters, AutoStorageBaseProperties
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
    from azure.mgmt.subscription import SubscriptionClient
    from azure.graphrbac import GraphRbacManagementClient
    from azure.graphrbac.models import ServicePrincipalCreateParameters, ApplicationCreateParameters
    from azure.graphrbac.models.graph_error import GraphErrorException
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.network.models import VirtualNetwork, Subnet, AddressSpace
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
except ImportError:
    import pip
    pip.main(['install', '--force-reinstall', '--upgrade', '--user', 'azure==3.0.0'])
    from azure.common import credentials
    from azure.cli.core._profile import Profile
    from azure.mgmt.authorization import AuthorizationManagementClient
    from azure.mgmt.authorization.models import RoleAssignmentCreateParameters, RoleDefinitionFilter
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.resource.resources.models import ResourceGroup
    from azure.mgmt.batch import BatchManagementClient
    from azure.mgmt.batch.models import BatchAccountCreateParameters, AutoStorageBaseProperties
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
    from azure.mgmt.subscription import SubscriptionClient
    from azure.graphrbac import GraphRbacManagementClient
    from azure.graphrbac.models import ServicePrincipalCreateParameters, ApplicationCreateParameters
    from azure.graphrbac.models.graph_error import GraphErrorException
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.network.models import VirtualNetwork, Subnet, AddressSpace
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD



class AccountSetupError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class DefaultSettings():
    iteration = "b1"
    resource_group = 'aztk' + iteration
    storage_account = 'aztkstorage' + iteration
    batch_account = 'aztkbatch' + iteration
    virtual_network_name = "aztkvnet" + iteration
    subnet_name = 'aztksubnet' + iteration
    application_name = 'aztkapplication' + iteration
    service_principal = 'aztksp' + iteration
    region = 'brazilsouth'


def create_resource_group(credentials, subscription_id, **kwargs):
    """
        Create a resource group
        :param credentials: msrestazure.azure_active_directory.AdalAuthentication
        :param subscription_id: str
        :param **resource_group: str
        :param **region: str
    """
    resource_client = ResourceManagementClient(credentials, subscription_id)
    resource_client.resource_groups.list()
    resource_group = resource_client.resource_groups.create_or_update(
        resource_group_name=kwargs.get("resource_group", DefaultSettings.resource_group),
        parameters={
            'location': kwargs.get("region", DefaultSettings.region),
        }
    )
    return resource_group.id

def create_storage_account(credentials, subscription_id, **kwargs):
    """
        Create a Storage account
        :param credentials: msrestazure.azure_active_directory.AdalAuthentication
        :param subscription_id: str
        :param **resource_group: str
        :param **storage_account: str
        :param **region: str
    """
    storage_management_client = StorageManagementClient(credentials, subscription_id)
    storage_account = storage_management_client.storage_accounts.create(
        resource_group_name=kwargs.get("resource_group", DefaultSettings.resource_group),
        account_name=kwargs.get("storage_account", DefaultSettings.storage_account),
        parameters=StorageAccountCreateParameters(
            sku=Sku(SkuName.standard_lrs),
            kind=Kind.storage,
            location=kwargs.get('region', DefaultSettings.region)
        )
    )
    return storage_account.result().id



def create_batch_account(credentials, subscription_id, **kwargs):
    """
        Create a Batch account
        :param credentials: msrestazure.azure_active_directory.AdalAuthentication
        :param subscription_id: str
        :param **resource_group: str
        :param **batch_account: str
        :param **region: str
        :param **storage_account_id: str
    """
    batch_management_client = BatchManagementClient(credentials, subscription_id)
    batch_account = batch_management_client.batch_account.create(
        resource_group_name=kwargs.get("resource_group", DefaultSettings.resource_group),
        account_name=kwargs.get("batch_account", DefaultSettings.batch_account),
        parameters=BatchAccountCreateParameters(
            location=kwargs.get('region', DefaultSettings.region),
            auto_storage=AutoStorageBaseProperties(
                storage_account_id=kwargs.get('storage_account_id', DefaultSettings.region)
            )
        )
    )
    return batch_account.result().id


def create_vnet(credentials, subscription_id, **kwargs):
    """
        Create a Batch account
        :param credentials: msrestazure.azure_active_directory.AdalAuthentication
        :param subscription_id: str
        :param **resource_group: str
        :param **virtual_network_name: str
        :param **subnet_name: str
        :param **region: str
    """
    network_client = NetworkManagementClient(credentials, subscription_id)
    virtual_network = network_client.virtual_networks.create_or_update(
        resource_group_name=kwargs.get("resource_group", DefaultSettings.resource_group),
        virtual_network_name=kwargs.get("virtual_network_name", DefaultSettings.virtual_network_name),
        parameters=VirtualNetwork(
            location=kwargs.get("region", DefaultSettings.region),
            address_space=AddressSpace(["10.0.0.0/24"])
        )
    )
    # virtual_network.result()
    subnet = network_client.subnets.create_or_update(
        resource_group_name=kwargs.get("resource_group", DefaultSettings.resource_group),
        virtual_network_name=kwargs.get("virtual_network_name", DefaultSettings.virtual_network_name),
        subnet_name=kwargs.get("subnet_name", DefaultSettings.subnet_name),
        subnet_parameters=Subnet(
            address_prefix='10.0.0.0/24'
        )
    )
    return virtual_network.result().id, subnet.result().id


def create_aad_user(credentials, tenant_id, **kwargs):
    graph_rbac_client = GraphRbacManagementClient(
        credentials,
        tenant_id,
        base_url=AZURE_PUBLIC_CLOUD.endpoints.active_directory_graph_resource_id
    )
    # try:
    application = graph_rbac_client.applications.create(
        parameters=ApplicationCreateParameters(
            available_to_other_tenants=False,
            identifier_uris=["http://aztk.com"],
            display_name=kwargs.get("application_name", DefaultSettings.application_name)
        )
    )
    service_principal = graph_rbac_client.service_principals.create(
        ServicePrincipalCreateParameters(
            app_id=application.app_id,
            account_enabled=True
        )
    )
    # except GraphErrorException:
    #     pass

    return application.app_id, service_principal, application.object_id


def create_role_assignment(credentials, subscription_id, scope, principal_id):
    authorization_client = AuthorizationManagementClient(credentials, subscription_id)
    # role_defs = [role_def for role_def in authorization_client.role_definitions.list(scope=scope, ]
    # [print(role_def.id) for role_def in role_defs if role_def.properties.role_name == "Contributor"]
    # contributor_role_def_id = authorization_client.role_definitions.get(scope="/", role_definition_id="Contributor").id
    # print(contributor_role_def_id)
    # Get "Contributor" built-in role as a RoleDefinition object
    role_name = 'Contributor'
    roles = list(authorization_client.role_definitions.list(
        scope,
        filter="roleName eq '{}'".format(role_name)
    ))
    assert len(roles) == 1
    contributor_role = roles[0]
    print(principal_id)
    print(contributor_role)

    import uuid
    authorization_client.role_assignments.create(
        scope,
        uuid.uuid4(),
        {
            'role_definition_id': contributor_role.id,
            'principal_id': principal_id
        }
    )


def format_secrets(**kwargs):
    pass


def prompt_with_default(key, value):
    user_value = input(key, ": [", value, "]")
    if user_value != "":
        return user_value
    else:
        return value

if __name__ == "__main__":
    # get credentials and tenant_id
    creds, subscription_id = credentials.get_azure_cli_credentials()
    subscription_client = SubscriptionClient(creds)
    tenant_ids = [tenant.id for tenant in subscription_client.tenants.list()]
    if len(tenant_ids) != 1:
        raise AccountSetupError("More than one tenant configured on your subscription.")
    else:
        tenant_id = tenant_ids[0]

    # create resource group
    resource_group_id = create_resource_group(creds, subscription_id)

    # create storage account
    storage_account_id = create_storage_account(creds, subscription_id)

    # create batch account
    create_batch_account(creds, subscription_id, **{'storage_account_id': storage_account_id})

    # create vnet
    create_vnet(creds, subscription_id)

    # create AAD application and service principal
    profile = credentials.get_cli_profile()
    aad_cred, _, tenant_id = profile.get_login_credentials(
        resource=AZURE_PUBLIC_CLOUD.endpoints.active_directory_graph_resource_id
    )

    application_id, service_principal, application_object_id = create_aad_user(aad_cred, tenant_id)
    print(dir(service_principal))
    print("SERVICE_PRINCIPAL app_id:", service_principal.app_id)
    print("SERVICE_PRINCIPAL add props:", service_principal.additional_properties)
    service_principal_object_id = service_principal.object_id
    create_role_assignment(creds, subscription_id, resource_group_id, service_principal_object_id)
