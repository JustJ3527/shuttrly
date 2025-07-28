from django.shortcuts import render
from django.template.response import TemplateResponse

def home_view(request):
    if request.headers.get('Hx-Request'):
        return render(request , 'partials/home_partial.html')
    return render(request, 'home.html')