from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from plan.models import Thing

import json

# Create your views here.
class Msgs:
    def __init__(self, request):
        self.request = request

    def info(self, *args, **kwargs):
        messages.info(self.request, *args, **kwargs)

class AtView(View):
    http_method_names = ['get', 'put', 'patch', 'delete', 'options']
    def get(self, request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse({
            'return': obj.serialize(),
            'messages': [],
        })

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

        obj = get_object_or_404(Thing, pk=pk)
        try:
            obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse({
            'return': obj.serialize(),
            'messages': [x.__dict__ for x in messages.get_messages(request)],
        })

    def patch(self, request, pk):
        if request.headers['content-type'] != 'application/json':
            return HttpResponseBadRequest()

        dict = json.loads(request.body)
        # No completeness check - PATCH modifies objects partially
        obj = get_object_or_404(Thing, pk=pk)
        try:
            obj.deserialize(dict, Msgs(request))
        except ValueError:
            return HttpResponseBadRequest()
        return JsonResponse({
            'return': obj.serialize(),
            'messages': [x.__dict__ for x in messages.get_messages(request)],
        })

    def delete(self, request, pk):
        Thing.objects.filter(pk=pk).delete()
        return JsonResponse()


@method_decorator(csrf_exempt, name='dispatch')
class CreateView(View):
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
        obj.deserialize(dict, Msgs(request))
        return JsonResponse({
            'return': obj.serialize(),
            'messages': [{
                'message': x.message,
                'tags': x.tags,
            } for x in messages.get_messages(request)],
        }, status_code=201)


class AtAndInsideView(View):
    http_method_names = ['get', 'options']
    def get(self, request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse({
            'return': [x.serialize() for x in obj.subtree()],
            'messages': [],
        })
