"""
Extend JSON schema validator class with ability to apply schema-defined
defaults.

Idea and code from: https://python-jsonschema.readthedocs.io/en/stable/faq/
"""

from __future__ import print_function, absolute_import
import jsonschema


def extend_with_default(validator_class):
    """
    Factory function that returns a new JSON schema validator class that
    extends the specified class by the ability to update the JSON instance
    that is being validated, by adding the schema-defined default values for
    any omitted properties.

    Parameters:

      validator_class (jsonschema.IValidator): JSON schema validator class
        that will be extended.

    Returns:

      jsonschema.IValidator: JSON schema validator class that has been
        extended.

    Example:

        import jsonschema

        MY_JSON_SCHEMA = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "http://example.com/root.json",
            "type": "object",
            . . .
        }

        ValidatorWithDefaults = extend_with_default(jsonschema.Draft7Validator)
        validator = ValidatorWithDefaults(MY_JSON_SCHEMA)
    """

    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])
        for error in validate_properties(validator, properties, instance,
                                         schema):
            yield error

    return jsonschema.validators.extend(
        validator_class, {"properties": set_defaults},
    )
