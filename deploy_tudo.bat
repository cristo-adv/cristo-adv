@echo off
color 0B
title Deploy Cristo Advogados - GitHub + Render
setlocal enabledelayedexpansion

:: ==================================================================
::  DEPLOY TUDO - Cristo Advogados
::  Automatiza deploy para GitHub + Render
:: ==================================================================

echo.
echo ================================================================
echo   DEPLOY CRISTO ADVOGADOS  -  GitHub + Render
echo ================================================================
echo.
echo  [>] Este script vai automatizar TODO o deploy do sistema.
echo  [>] Certifique-se de que o arquivo app.py esta nesta pasta.
echo.

:: ----------------------------------------------------------------
:: 0. Verificar se app.py existe
:: ----------------------------------------------------------------
echo ================================================================
echo  [0] VERIFICANDO ARQUIVO app.py
echo ================================================================
echo.
if exist "app.py" (
    echo  [OK] Arquivo app.py encontrado!
) else (
    echo  [ERRO] Arquivo app.py NAO encontrado nesta pasta!
    echo  [!] Voce precisa executar este script na mesma pasta do app.py
    echo.
    pause
    exit /b 1
)
echo.

:: ----------------------------------------------------------------
:: 1. Verificar Python
:: ----------------------------------------------------------------
echo ================================================================
echo  [1] VERIFICANDO PYTHON
echo ================================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao foi encontrado no seu sistema!
    echo.
    echo  [!] Para resolver:
    echo      1. Acesse: https://www.python.org/downloads/
    echo      2. Baixe a versao mais recente do Python
    echo      3. Durante a instalacao, MARQUE a opcao:
    echo         "Add Python to PATH"
    echo      4. Apos instalar, feche e abra novamente este script
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
    echo  [OK] Python encontrado: !PYVER!
)
echo.

:: ----------------------------------------------------------------
:: 2. Criar arquivos de deploy
:: ----------------------------------------------------------------
echo ================================================================
echo  [2] CRIANDO ARQUIVOS DE DEPLOY
echo ================================================================
echo.

:: requirements.txt
echo  [>] Criando requirements.txt ...
if exist "requirements.txt" (
    echo  [!] requirements.txt ja existe - sera atualizado.
)
(
    echo flask
    echo gunicorn
    echo flask-cors
    echo python-dotenv
    echo requests
) > requirements.txt
echo  [OK] requirements.txt criado!

:: Procfile
echo  [>] Criando Procfile ...
if exist "Procfile" (
    echo  [!] Procfile ja existe - sera atualizado.
)
echo web: gunicorn app:app --workers 4 --threads 2 --timeout 120 > Procfile
echo  [OK] Procfile criado!

:: .gitignore
echo  [>] Criando .gitignore ...
if exist ".gitignore" (
    echo  [!] .gitignore ja existe - sera atualizado.
)
(
    echo __pycache__/
    echo *.pyc
    echo .env
    echo venv/
    echo env/
    echo .venv/
    echo node_modules/
    echo *.log
    echo .DS_Store
    echo instance/
) > .gitignore
echo  [OK] .gitignore criado!

echo.
echo  [OK] Todos os arquivos de deploy foram criados!
echo.

:: ----------------------------------------------------------------
:: 3. Instalar dependencias
:: ----------------------------------------------------------------
echo ================================================================
echo  [3] INSTALANDO DEPENDENCIAS
echo ================================================================
echo.
echo  [>] Instalando pacotes do requirements.txt ...
echo  [>] Usando: python -m pip install
 echo.
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha ao instalar dependencias!
    echo  [!] Tente manualmente: python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo.
echo  [OK] Dependencias instaladas com sucesso!
echo.

:: ----------------------------------------------------------------
:: 4. Verificar Git
:: ----------------------------------------------------------------
echo ================================================================
echo  [4] VERIFICANDO GIT
echo ================================================================
echo.
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Git nao foi encontrado no seu sistema!
    echo.
    echo  [!] Para resolver:
    echo      1. Acesse: https://git-scm.com/downloads
    echo      2. Baixe e instale o Git para Windows
    echo      3. Durante a instalacao, use as opcoes padrao
    echo      4. Apos instalar, feche e abra novamente este script
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('git --version 2^>^&1') do set "GITVER=%%v"
    echo  [OK] Git encontrado: !GITVER!
)
echo.

:: ----------------------------------------------------------------
:: 5. Configurar Git - email e nome
:: ----------------------------------------------------------------
echo ================================================================
echo  [5] CONFIGURANDO GIT
echo ================================================================
echo.

:: Perguntar email
set "GIT_EMAIL="
set /p GIT_EMAIL="  [>] Digite seu email do GitHub: "
if "!GIT_EMAIL!"=="" (
    echo  [ERRO] Email nao pode ser vazio!
    pause
    exit /b 1
)

:: Perguntar nome
set "GIT_NAME="
set /p GIT_NAME="  [>] Digite seu nome de usuario do GitHub: "
if "!GIT_NAME!"=="" (
    echo  [ERRO] Nome nao pode ser vazio!
    pause
    exit /b 1
)

echo.
echo  [>] Configurando git com seus dados...
git config --global user.email "!GIT_EMAIL!"
git config --global user.name "!GIT_NAME!"
echo  [OK] Git configurado: !GIT_NAME! ^<!GIT_EMAIL!^>
echo.

:: ----------------------------------------------------------------
:: 6. GitHub - Token, init, add, commit, push
:: ----------------------------------------------------------------
echo ================================================================
echo  [6] DEPLOY PARA GITHUB
echo ================================================================
echo.
echo  [!] Voce precisa de um Personal Access Token do GitHub.
echo  [!] Para criar:
    echo      1. Acesse: https://github.com/settings/tokens
    echo      2. Generate new token (classic)
    echo      3. Marque a opcao "repo" (acesso completo)
    echo      4. Copie o token gerado
echo.

set "GH_TOKEN="
set /p GH_TOKEN="  [>] Cole seu token de acesso do GitHub: "
if "!GH_TOKEN!"=="" (
    echo  [ERRO] Token nao pode ser vazio!
    pause
    exit /b 1
)

echo.
echo  [>] Inicializando repositorio Git...
if exist ".git" (
    echo  [!] Repositorio Git ja existe. Continuando...
) else (
    git init
)
echo  [OK] Repositorio inicializado!

echo.
echo  [>] Adicionando arquivos...
git add -A
if %errorlevel% neq 0 (
    echo  [ERRO] Falha ao adicionar arquivos!
    pause
    exit /b 1
)
echo  [OK] Arquivos adicionados!

echo.
echo  [>] Criando commit...
git commit -m "Deploy automatico - Cristo Advogados"
if %errorlevel% neq 0 (
    echo  [!] Commit falhou - pode ja existir. Continuando...
)
echo  [OK] Commit criado!

echo.
echo  [>] Configurando branch principal como 'main'...
git branch -M main >nul 2>&1
echo  [OK] Branch principal: main

echo.
echo  [>] Adicionando repositorio remoto...
git remote remove origin >nul 2>&1
git remote add origin https://!GH_TOKEN!@github.com/cristo-adv/cristo-adv.git
echo  [OK] Repositorio remoto configurado!

echo.
echo  [>] Enviando codigo para o GitHub...
echo  [>] Repositorio: https://github.com/cristo-adv/cristo-adv.git
echo.
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Falha ao fazer push para o GitHub!
    echo.
    echo  [!] Possiveis solucoes:
    echo      1. Verifique se o token esta correto e nao expirou
    echo      2. Verifique se o repositorio existe no GitHub:
    echo         https://github.com/cristo-adv/cristo-adv
    echo      3. Se o repositorio nao existir, crie-o primeiro
    echo      4. Tente push manual:
    echo         git push -u origin main
    echo      5. Se ja existe conteudo remoto, tente forcar:
    echo         git push -u origin main --force
    echo.
    echo  [!] Deseja tentar push com --force?
    set "FORCE_CHOICE="
    set /p FORCE_CHOICE="      Digite S para sim ou N para nao: "
    if /i "!FORCE_CHOICE!"=="S" (
        echo.
        echo  [>] Tentando push com --force...
        git push -u origin main --force
        if !errorlevel! neq 0 (
            echo.
            echo  [ERRO] Push com --force tambem falhou!
            echo  [!] Verifique manualmente o repositorio e permissoes.
            echo.
            pause
            exit /b 1
        ) else (
            echo  [OK] Push com --force concluido!
        )
    ) else (
        echo.
        echo  [!] Push cancelado. Resolva manualmente e rode novamente.
        echo.
        pause
        exit /b 1
    )
)
echo.
echo  [OK] Codigo enviado para o GitHub com sucesso!
echo  [>] Repositorio: https://github.com/cristo-adv/cristo-adv
echo.

:: ----------------------------------------------------------------
:: 7. Render - Instrucoes
:: ----------------------------------------------------------------
echo ================================================================
echo  [7] INSTRUCOES PARA O RENDER
echo ================================================================
echo.
echo  [>] Agora voce precisa configurar o Render. Siga os passos:
echo.
echo  1. Acesse: https://dashboard.render.com/
echo  2. Clique em "New +" e selecione "Web Service"
echo  3. Conecte seu repositorio do GitHub:
     https://github.com/cristo-adv/cristo-adv
echo  4. Configure o servico:
     - Name: cristo-advogados
     - Runtime: Python 3
     - Build Command: pip install -r requirements.txt
     - Start Command: gunicorn app:app --workers 4 --threads 2 --timeout 120
echo  5. Selecione o plano FREE (ou pago, se preferir)
echo  6. Em "Environment Variables", adicione:
     - FLASK_ENV=production
     - Outras variaveis que seu app precisar (chaves, etc.)
echo  7. Clique em "Create Web Service"
echo  8. Aguarde o build e deploy concluir
     (pode levar alguns minutos na primeira vez)
echo  9. Apos concluido, acesse a URL gerada pelo Render
     (algo como: https://cristo-advogados.onrender.com)
echo.
echo  [!] IMPORTANTE:
     - O Render faz deploy automatico a cada push no GitHub
     - Para atualizar, basta rodar este script novamente
     - O plano FREE "hiberna" apos inatividade (primeiro acesso demora +)
echo.
echo  [OK] Instrucoes do Render exibidas!
echo.

:: ----------------------------------------------------------------
:: 8. Teste local
:: ----------------------------------------------------------------
echo ================================================================
echo  [8] TESTE LOCAL
echo ================================================================
echo.
echo  [>] Deseja rodar o sistema localmente agora?
echo  [>] Isso abrira o servidor Flask no seu computador.
echo.
set "RUN_LOCAL="
set /p RUN_LOCAL="  Digite S para rodar agora ou N para finalizar: "

if /i "!RUN_LOCAL!"=="S" (
    echo.
    echo  [>] Iniciando servidor local...
    echo  [>] Acesse: http://localhost:5000
    echo  [>] Pressione CTRL+C para parar o servidor.
    echo.
    python app.py
) else (
    echo.
    echo  [!] Teste local pulado.
    echo  [>] Para rodar depois, execute: python app.py
)
echo.

:: ----------------------------------------------------------------
:: Finalizacao
:: ----------------------------------------------------------------
echo ================================================================
echo  DEPLOY CONCLUIDO!
echo ================================================================
echo.
echo  [OK] Processo finalizado!
echo.
echo  Resumo do que foi feito:
  - [OK] Python verificado
  - [OK] Arquivos de deploy criados (requirements.txt, Procfile, .gitignore)
  - [OK] Dependencias instaladas
  - [OK] Git configurado
  - [OK] Codigo enviado para GitHub
  - [OK] Instrucoes do Render exibidas
echo.
echo  [>] Proximo passo: configure o Render conforme as instrucoes acima.
echo.
echo  [!] Obrigado por usar o deploy automatico - Cristo Advogados!
echo.
pause
exit /b 0