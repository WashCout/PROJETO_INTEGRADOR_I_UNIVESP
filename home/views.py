from django.contrib import auth, messages
from django.shortcuts import render, redirect
from django.contrib.messages import constants
from django.contrib.auth.models import User

from django.contrib import auth, messages
from django.shortcuts import render, redirect
from django.contrib.messages import constants
from django.contrib.auth.models import User

def index(request):
    if request.method == "GET":
        return render(request, 'index.html')
    elif request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get("password")

        print(f'username={username}', flush=True)
        print(f'password={password}', flush=True)

        user = auth.authenticate(request, username=username, password=password)

        print(f'user={user}', flush=True)

        if user:
            auth.login(request, user)
            return redirect('/lojistas/estoque')

        messages.add_message(request, constants.ERROR, 'Usuário ou senha incorretos')
        return redirect('/home/index')


def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get("email")
        senha = request.POST.get("senha")
        confirmar_senha = request.POST.get('confirmar_senha')

        print(f'username={username}', flush=True)
        print(f'email={email}', flush=True)
        print(f'senha={senha}', flush=True)
        print(f'confirmar_senha={confirmar_senha}', flush=True)
        
        users = User.objects.filter(username=username)

        if users.exists():
            messages.add_message(request, constants.ERROR, 'Já existe um usuário com esse ursername')
            return redirect('/home/cadastro')

        if senha != confirmar_senha:
            messages.add_message(request, constants.ERROR, 'A senha não corresponde com a confirmação da senha')
            return redirect('/home/cadastro')
        
        try:
            User.objects.create_user(
                username=username,
                email=email,
                password=senha
            )
            return redirect('/home/index')
        except Exception as e:            
            print(f'Erro ao criar o usuário: {e}', flush=True)
            messages.add_message(request, constants.ERROR, 'Erro ao criar o usuário')
            return redirect('/home/cadastro')

def sair(request):
    auth.logout(request)
    return redirect('/home/index')