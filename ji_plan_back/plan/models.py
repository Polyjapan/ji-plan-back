from django.db import models


from jsonfield import JSONField


import json

# Create your models here.
class Layer(models.Model):
    name = models.CharField(max_length=64)
    # user permissions ?

    def serialize(self):
        data = {
            'name': self.name,
            'pk': self.pk,
            'things': [thing.pk for thing in self.thing_set.all()]
        }
        return data

    def deserialize(self):
        to_save = [self]
        to_delete = []

        if 'name' in dict.keys():
            self.name = dict['name']

        for x in to_save:
            x.save()
        for x in to_delete:
            x.delete()
        return

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

    tag_name = models.CharField(max_length=16, choices=[('plan', 'Plan'), ('zone', 'Zone'), ('object', 'Object')])
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
            'where': {
                'parent': self.parent.pk if self.parent else None,
                'position': None if self.pos_implicit else {'x': self.pos_x, 'y': self.pos_y},
                'layer': self.pos_layer.pk if self.pos_layer else None,
            },
            'what': {
                'tag': self.tag_name,
                'attrs': {x.attr.name: json.loads(x.value) for x in self.attributething_set.all()}
            },
        }
        return data

    def deserialize(self, dict, messages):
        to_save = [self]
        to_delete = []

        if 'where' in dict.keys():

            if 'parent' in dict['where'].keys():
                # parent must refer to an existing thing, or it can be null
                parent = None
                if dict['where']['parent']:
                    parent = Thing.objects.filter(pk=dict['where']['parent'])
                    if dict['where']['parent'] and not parent.exists():
                        raise ValueError()
                    parent = parent.get()
                    if parent.tag_name not in ['zone', 'plan']:
                        raise ValueError()

                self.parent = parent

            if 'layer' in dict['where'].keys():
                layer = None
                if dict['where']['layer']:
                    try:
                        layer = Layer.objects.get(pk=dict['where']['layer'])
                    except Layer.DoesNotExist:
                        messages.error('Layer {} does not exist'.format(dict['where']['layer']))
                        raise ValueError()

                self.pos_layer = layer

            if 'position' in dict['where'].keys():
                pos = dict['where']['position']

                self.pos_x = pos['x'] if pos else None
                self.pos_y = pos['y'] if pos else None
                self.pos_implicit = (pos is None)

        if 'what' in dict.keys():

            if 'tag' in dict['what'].keys():
                if dict['what']['tag'] == 'plan' and self.parent is not None:
                    raise ValueError()

                self.tag_name = dict['what']['tag']

            if 'attrs' in dict['what'].keys():
                for k, v in dict['what']['attrs'].items():
                    attr, created = Attribute.objects.get_or_create(name=k)
                    if created:
                        messages.info('Attribute `{}` was created'.format(k))

                    if v is None:
                        # remove key !
                        try:
                            at = AttributeThing.objects.get(attr=attr, thing=self)
                            to_delete.append(at)
                        except AttributeThing.DoesNotExist:
                            pass
                    else:
                        try:
                            at = AttributeThing.objects.get(attr=attr, thing=self)
                        except AttributeThing.DoesNotExist:
                            at = AttributeThing(attr=attr, thing=self)
                        at.value = json.dumps(v)
                        to_save.append(at)

        for x in to_save:
            x.save()
        for x in to_delete:
            x.delete()
        return

    def subtree(self):
        ret = [self]
        def recurse(root):
            children = list(Thing.objects.filter(parent__pk=root.pk))
            nonlocal ret
            ret = ret + children
            for x in children:
                recurse(x)
        recurse(self)
        return ret
