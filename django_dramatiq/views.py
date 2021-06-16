from django.http import HttpResponse
from django.shortcuts import render

from .forms import DramatiqLoadGraphForm
from .apps import DjangoDramatiqConfig

# load_graph permission function
DRAMATIQ_LOAD_GRAPH_PERM_FN = DjangoDramatiqConfig.load_graph_perm_fn()
# plotly lib
DRAMATIQ_LOAD_GRAPH_PLOTLY_LIB = DjangoDramatiqConfig.load_graph_plotly_lib()


def _has_load_graph_perm(request):
    return request.user.is_superuser


def load_graph(request):
    if request.method != "GET":
        return HttpResponse('GET only')
    if not (DRAMATIQ_LOAD_GRAPH_PERM_FN or _has_load_graph_perm)(request):
        return HttpResponse('Access denied, <a href="/">go home 🏠</a>')
    response = {}
    if request.GET:
        form = DramatiqLoadGraphForm(request.GET)
        if form.is_valid():
            response.update(form.get_graph_data())
    else:
        form = DramatiqLoadGraphForm()
    response.update({
        'form': form,
        'plotly_lib': DRAMATIQ_LOAD_GRAPH_PLOTLY_LIB
    })
    return render(request, 'django_dramatiq/load_graph.html', response)
