from django.urls import path

import plan.views as views

app_name = 'plan'
urlpatterns = [
    path('thing/<int:pk>', views.ThingView.as_view(), name='thing'),
    path('thing/<int:pk>/at-and-inside', views.AtAndInsideThingView.as_view(), name='thing.at_and_inside'),
    path('thing/create', views.CreateThingView.as_view(), name='thing.create'),
    path('layer/<int:pk>', views.LayerView.as_view(), name='layer'),
    path('layer/create', views.CreateLayerView.as_view(), name='layer.create'),
]

# coming soon : search by attribute value
