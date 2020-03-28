from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse

# Create your views here.
class Msgs:
    def __init__(self, request):
        self.request = request

    def __getattr__(self, name):
        return lambda n=name, r=self.request,*args, **kwargs: messages.__getattr__(n)(r, *args, **kwargs)


class AtView(View):
    http_method_names = ['get', 'put', 'patch', 'delete', 'options']
    def get(request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse({
            'return': obj.serialize()
        })

    def put(request, pk):
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
            'messages': list(messages.get_messages(request)),
        })

    def patch(request, pk):
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
            'messages': list(messages.get_messages(request)),
        })

    def delete(request, pk):
        Thing.objects.filter(pk=pk).delete()
        return JsonResponse()


class CreateView(View):
    http_method_names = ['post', 'options']
    def post(request, pk):
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
            'messages': list(messages.get_messages(request)),
        })


class AtAndInsideView(View):
    http_method_names = ['get', 'options']
    def get(request, pk):
        obj = get_object_or_404(Thing, pk=pk)
        return JsonResponse({
            'return': [x.serialize() for x in obj.subtree()]
        })
