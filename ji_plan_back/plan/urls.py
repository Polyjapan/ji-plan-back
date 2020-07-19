from django.urls import path

import plan.views as views

app_name = 'plan'
urlpatterns = [
    path('thing/<slug:client_id>', views.ThingView.as_view(), name='thing'),
    path('thing/<slug:client_id>/at-and-inside', views.AtAndInsideThingView.as_view(), name='thing.at_and_inside'),
    path('thing/<slug:client_id>/create', views.CreateThingView.as_view(), name='thing.create'),
    path('layer/<slug:client_id>', views.LayerView.as_view(), name='layer'),
    path('layer/<slug:client_id>/create', views.CreateLayerView.as_view(), name='layer.create'),
]

# coming soon : search by attribute value
