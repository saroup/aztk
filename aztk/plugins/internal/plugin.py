from aztk.plugins import PluginDefinition
from aztk.error import InvalidPluginDefinitionError, InvalidPluginConfigurationError


class Plugin:
    def __init__(self, path: str, module):
        """
        Internal container for a plugin.
        :param path: Location of the plugin
        """
        self.path = path
        self.module = module
        self.definition = module.definition()
        if not isinstance(self.definition, PluginDefinition):
            raise InvalidPluginDefinitionError(
                "Plugin {0} definition method doesn't return a PluginDefinition object".
                format(path))
        self.name = self.definition.name

    def validate_args(self, args: dict):
        """
        Validate the given args are valid for the plugin
        """
        for arg, v in args.items():
            if arg not in self.definition.args:
                message = "Plugin {0} doesn't have an argument called '{1}'".format(self.name, arg)
                raise InvalidPluginConfigurationError(message, self.definition)

        if hasattr(self.module, "validate_args"):
            try:
                self.module.validate_args(**args)
            except InvalidPluginConfigurationError as e:
                if e.pluginDefinition is None:
                    e.pluginDefinition = self.definition
                raise e
