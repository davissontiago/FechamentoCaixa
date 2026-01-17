from django.shortcuts import render, redirect
from django.conf import settings

class SitePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se já estiver logado na sessão, deixa passar
        if request.session.get('site_unlocked'):
            return self.get_response(request)

        # Se for a página de login ou assets estáticos, deixa passar
        if request.path == '/site-login/' or request.path.startswith('/static/'):
            return self.get_response(request)

        # Se enviou a senha (POST)
        if request.method == 'POST' and request.path == '/site-login/':
            senha = request.POST.get('password')
            if senha == getattr(settings, 'SITE_PASSWORD', 'admin'):
                request.session['site_unlocked'] = True
                return redirect('/')
            else:
                return render(request, 'site_login.html', {'error': 'Senha incorreta'})

        # Se não está logado, manda para o login
        return redirect('/site-login/')