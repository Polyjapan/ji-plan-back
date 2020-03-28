from django.urls import path

import plan.views as views

app_name = 'plan'
urlpatterns = [
    path('at/<int:pk>', views.AtView.as_view(), name='at'),
    path('create', views.CreateView.as_view(), name='create'),
    path('at-and-inside/<int:pk>', views.AtAndInsideView.as_view(), name='at_and_inside'),
]

# coming soon : search by attribute value
