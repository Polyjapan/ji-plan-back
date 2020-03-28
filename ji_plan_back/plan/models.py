from django.db import models


from jsonfield import JSONField


import json

# Create your models here.
class Layer(models.Model):
    name = models.CharField(max_length=64)
    # user permissions ?

class Attribute(models.Model):
    name = models.CharField(max_length=64)

class AttributeThing(models.Model):
    class Meta:
        unique_together = ['attr', 'thing']

    attr = models.ForeignKey('Attribute', on_delete=models.CASCADE)
    thing = models.ForeignKey('Thing', on_delete=models.CASCADE)
    value = JSONField(null=True)

class Thing(models.Model):
    parent = models.ForeignKey('Thing', null=True, blank=True, on_delete=models.CASCADE)
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True)
    pos_implicit = models.BooleanField(default=True)
    pos_layer = models.ForeignKey('Layer', null=True, blank=True, on_delete=models.SET_NULL)

    tag_name = models.CharField(max_length=16, choices = [('zone', 'Zone'), ('object', 'Object')])
    attributes = models.ManyToManyField('Attribute', through='AttributeThing')

    def serialize(self):
        thing = self.parent
        ancestors = []
        while thing:
            ancestors.append(thing.pk)
            thing = thing.parent

        data = {
            'ancestors': ancestors,
            'pk': self.pk,
            'where':{
                'parent': self.parent.pk,
                'position': None if self.pos_implicit else '{};{}'.format(self.pos_x, self.pos_y),
                'layer': self.pos_layer.name if self.pos_layer else None,
            },
            'what':{
                'tag': self.tag_name,
                'attrs': { x.attr.name : json.loads(x.value) for x in self.attributes }
            },
        }
        return data

    def deserialize(self, dict, messages):
        if 'where' in dict.keys():

            if 'parent' in dict['where'].keys():
                # parent must refer to an existing thing, or it can be null
                parent = Thing.objects.filter(pk=dict['where']['parent'])
                if dict['where']['parent'] and not parent.exists():
                    raise ValueError()
                self.parent = parent

            if 'layer' in dict['where'].keys():
                layer = None
                if dict['where']['layer']:
                    layer, created = Layer.objects.filter(name=dict['where']['layer']).get_or_create()
                    if created:
                        messages.info('Layer `{}` was created'.format(dict['where']['layer']))
                self.pos_layer = layer

            if 'position' in dict['where'].keys():
                str = dict['where']['position']
                self.pos_x = str.split(';')[0] if str else None
                self.pos_y = str.split(';')[1] if str else None
                self.pos_implicit = (str == None)

        if 'what' in dict.keys():

            if 'tag' in dict['what'].keys():
                self.tag_name = dict['what']['tag']

            if 'attrs' in dict['what'].keys():
                for k,v in dict['what']['attrs'].items():
                    attr, created = Attr.objects.get_or_create(name=k)
                    if created:
                        messages.info('Attribute `{}` was created'.format(k))

                    if v == None:
                        # remove key !
                        AttributeThing.filter(attr=attr, thing=self).delete()
                    else:
                        at = AttributeThing.get(attr=attr, thing=self)
                        at.value = json.dumps(v)
                        at.save()

        self.save()
        return

    def subtree(self):
        ret = [self]
        def recurse(root):
            children = list(Thing.objects.filter(parent__pk=root.pk))
            ret = ret + children
            for x in children:
                recurse(x)
        recurse(self)
        return ret

    # no unserialize(). this is handled by the POST view directly, as it is very specific.
