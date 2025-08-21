from django.shortcuts import render

from .tasks import add


def calc(req):
    if req.method == "POST":
        add.send(float(req.POST["a"]), float(req.POST["b"]))
    return render(req, "calc.html")
