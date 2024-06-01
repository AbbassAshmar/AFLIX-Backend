from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist


def get_object_or_404(object, pk, error_message):
    try:
        obj = object.objects.get(pk = pk)
        return obj
    except ObjectDoesNotExist:
        raise NotFound(error_message)