from django.shortcuts import get_object_or_404
from django.views import View
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from plan.models import Thing, Layer

import json


def return_format(ret, request):
    if not isinstance(ret, list):
        raise ValueError()

    return {
        'return': ret,
        'messages': [{
            'message': x.message,
            'tags': x.tags,
        } for x in messages.get_messages(request)]
    }


class Msgs:
    def __init__(self, request):
        self.request = request

    def info(self, *args, **kwargs):
        messages.info(self.request, *args, **kwargs)

    def error(self, *args, **kwargs):
        messages.error(self.request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class ThingView(View):
    http_method_names = ['get', 'put', 'patch', 'delete', 'options']

    def get(self, request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse(return_format([obj.serialize()], request))

    def put(self, request, pk):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # Completeness check - PUT modifies objects completely
        if not set(['what', 'where']).issubset(dict.keys()):
            return HttpResponseBadRequest()
        if not set(['tag', 'attrs']).issubset(dict['what'].keys()):
            return HttpResponseBadRequest()
        if not set(['parent', 'position', 'layer']).issubset(dict['where'].keys()):
            return HttpResponseBadRequest()

        obj = get_object_or_404(Thing, pk=pk)  # check object exists
        try:
            with transaction.atomic():
                obj.attributething_set.all().delete()  # clear attributes before PUTting new ones
                obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse(return_format([obj.serialize()], request))

    def patch(self, request, pk):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # No completeness check - PATCH modifies objects partially
        obj = get_object_or_404(Thing, pk=pk)
        try:
            with transaction.atomic():
                obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse(return_format([obj.serialize()], request))

    def delete(self, request, pk):
        Thing.objects.filter(pk=pk).delete()
        return JsonResponse(return_format([], request))


@method_decorator(csrf_exempt, name='dispatch')
class LayerView(View):
    http_method_names = ['get', 'put' 'options']

    def get(self, request, pk):
        obj = get_object_or_404(Layer, pk=pk)
        return JsonResponse(return_format([obj.serialize()], request))

    def put(self, request, pk):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # Format check - PUT creates complete objects
        if 'name' not in dict.keys():
            return HttpResponseBadRequest()

        obj = get_object_or_404(Layer, pk=pk)
        try:
            with transaction.atomic():
                obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse(return_format([obj.serialize()], request))


@method_decorator(csrf_exempt, name='dispatch')
class CreateThingView(View):
    http_method_names = ['post', 'options']

    def post(self, request):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # Format check - POST creates complete objects
        if not set(['what', 'where']).issubset(dict.keys()):
            return HttpResponseBadRequest()
        if not set(['tag', 'attrs']).issubset(dict['what'].keys()):
            return HttpResponseBadRequest()
        if not set(['parent', 'position', 'layer']).issubset(dict['where'].keys()):
            return HttpResponseBadRequest()

        obj = Thing()
        try:
            with transaction.atomic():
                obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse(return_format([obj.serialize()], request), status=201)


@method_decorator(csrf_exempt, name='dispatch')
class CreateLayerView(View):
    http_method_names = ['post', 'options']

    def post(self, request):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # Format check - POST creates complete objects
        if 'name' not in dict.keys():
            return HttpResponseBadRequest()

        obj = Layer()
        try:
            with transaction.atomic():
                obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse(return_format([obj.serialize()], request), status=201)


class AtAndInsideThingView(View):
    http_method_names = ['get', 'options']

    def get(self, request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse(return_format([x.serialize() for x in obj.subtree()], request))
