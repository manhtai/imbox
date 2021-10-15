from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView

from apps.activity.forms import ActivityForm
from apps.activity.models import Activity


class RouteView(TemplateView):
    template_name = "page/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        activity_id = kwargs.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id)
        context["activity"] = activity

        return context


class DetailView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    pk_url_kwarg = "activity_id"
    template_name = "activity/detail.html"

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        if obj.user != self.request.user:
            raise Http404()
        return obj
