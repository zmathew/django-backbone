from StringIO import StringIO

from django.core.serializers.python import Serializer as PythonSerializer
from django.db.models.fields import FieldDoesNotExist


class AllFieldsSerializer(PythonSerializer):
    """
    Supports serialization of fields on the model that are inherited (ie. non-local fields).
    """

    # Copied from django.core.serializers.base
    # Unfortunately, django's serializer only serializes local fields
    # NOTE: This differs from django's serializer as it REQUIRES `fields` to be specified.
    def serialize(self, queryset, fields, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", StringIO())
        self.selected_fields = fields
        self.use_natural_keys = options.pop("use_natural_keys", False)

        self.start_serialization()

        for obj in queryset:
            self.start_object(obj)
            for field_name in self.selected_fields:
                try:
                    field = obj._meta.get_field(field_name)
                except FieldDoesNotExist:
                    continue

                if field in obj._meta.many_to_many:
                    self.handle_m2m_field(obj, field)
                elif field.rel is not None:
                    self.handle_fk_field(obj, field)
                else:
                    self.handle_field(obj, field)
            self.end_object(obj)

        self.end_serialization()
        return self.getvalue()
