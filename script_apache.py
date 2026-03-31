#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT APACHE VIRTUALHOST - Ponto 3
================================================================================
Administração de Sistemas 2025/2026
Apache HTTPD - VirtualHosts com páginas de boas-vindas

Funcionalidades:
- Instala e configura o Apache HTTPD automaticamente
- Cria VirtualHost para o domínio especificado
- Gera página de boas-vindas HTML personalizada
- Configura firewall e SELinux
================================================================================
"""

import os
import sys
import subprocess
import re
import shutil
from datetime import datetime

# Cores para output no terminal
class Cores:
    VERDE = '\033[92m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    CIANO = '\033[96m'
    BRANCO = '\033[97m'
    MAGENTA = '\033[95m'
    NEGRITO = '\033[1m'
    FIM = '\033[0m'

def limpar_ecra():
    """Limpa o ecrã do terminal"""
    os.system('clear' if os.name != 'nt' else 'cls')

def imprimir_cabecalho():
    """Imprime o cabeçalho do script"""
    limpar_ecra()
    print(f"{Cores.AZUL}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"{Cores.CIANO}{Cores.NEGRITO}         ADMINISTRAÇÃO DE SISTEMAS - PROJETO 2025/2026{Cores.FIM}")
    print(f"{Cores.AZUL}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"{Cores.AMARELO}           APACHE VIRTUALHOST (Ponto 3){Cores.FIM}")
    print(f"{Cores.AZUL}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print()

def executar_comando(comando, descricao="", ignorar_erro=False):
    """Executa um comando shell e retorna o resultado"""
    if descricao:
        print(f"{Cores.CIANO}➜ {descricao}...{Cores.FIM}")
    
    try:
        resultado = subprocess.run(
            comando, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=not ignorar_erro
        )
        if resultado.returncode == 0:
            if descricao:
                print(f"{Cores.VERDE}  ✓ Concluído{Cores.FIM}")
            return True, resultado.stdout
        else:
            if not ignorar_erro and descricao:
                print(f"{Cores.VERMELHO}  ✗ Erro: {resultado.stderr}{Cores.FIM}")
            return False, resultado.stderr
    except subprocess.CalledProcessError as e:
        if not ignorar_erro and descricao:
            print(f"{Cores.VERMELHO}  ✗ Erro: {e}{Cores.FIM}")
        return False, str(e)

def verificar_root():
    """Verifica se o script está a correr como root"""
    if os.geteuid() != 0:
        print(f"{Cores.VERMELHO}{Cores.NEGRITO}✗ Este script precisa de privilégios de root!{Cores.FIM}")
        print(f"{Cores.AMARELO}  Por favor, execute: sudo python3 {sys.argv[0]}{Cores.FIM}")
        sys.exit(1)

def validar_dominio(dominio):
    """Valida o formato do nome de domínio"""
    padrao = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(padrao, dominio) is not None

def obter_ip_local():
    """Obtém o IP local do servidor"""
    resultado = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True)
    if resultado.returncode == 0:
        return resultado.stdout.strip()
    return "127.0.0.1"

def verificar_instalacao_apache():
    """Verifica se o Apache está instalado"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📦 VERIFICAÇÃO APACHE{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("which httpd", shell=True, capture_output=True)
    if resultado.returncode != 0:
        print(f"{Cores.AMARELO}⚠ Apache não está instalado. A instalar...{Cores.FIM}")
        executar_comando("dnf update -y", "A atualizar repositórios")
        sucesso, _ = executar_comando("dnf install -y httpd", "A instalar Apache")
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Falha ao instalar Apache!{Cores.FIM}")
            return False
        print(f"{Cores.VERDE}✓ Apache instalado!{Cores.FIM}")
    else:
        print(f"{Cores.VERDE}✓ Apache já está instalado{Cores.FIM}")
    return True

def configurar_firewall():
    """Configura firewall para Apache"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔥 FIREWALL{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("systemctl is-active firewalld", shell=True, capture_output=True)
    if resultado.returncode != 0:
        executar_comando("systemctl start firewalld", "A iniciar firewalld")
        executar_comando("systemctl enable firewalld", "A ativar firewalld")
    
    executar_comando("firewall-cmd --permanent --add-service=http", "A adicionar HTTP")
    executar_comando("firewall-cmd --permanent --add-service=https", "A adicionar HTTPS")
    executar_comando("firewall-cmd --reload", "A recarregar firewall")
    print(f"{Cores.VERDE}✓ Firewall configurado{Cores.FIM}")
    return True

def obter_rede(ip):
    """Obtém a rede /24 a partir de um IP (ex: 10.39.195.107 → 10.39.195.0/24)"""
    octetos = ip.split('.')
    return '.'.join(octetos[:3]) + '.0/24'

def configurar_dns_rede(ip_servidor, dominio):
    """Configura o BIND para aceitar queries da rede local"""
    named_conf = "/etc/named.conf"

    if not os.path.exists(named_conf):
        print(f"{Cores.AMARELO}⚠ named.conf não encontrado — a saltar configuração DNS{Cores.FIM}")
        return False

    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🌐 CONFIGURAÇÃO DNS PARA A REDE{Cores.FIM}")
    print("-" * 50)

    try:
        with open(named_conf, 'r') as f:
            conteudo = f.read()
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao ler named.conf: {e}{Cores.FIM}")
        return False

    rede = obter_rede(ip_servidor)
    alterado = False

    # --- listen-on ---
    # Verifica se o IP do servidor já está na diretiva listen-on
    listen_match = re.search(r'listen-on\s+port\s+53\s*\{([^}]*)\}', conteudo)
    if listen_match:
        listen_atual = listen_match.group(1)
        if ip_servidor not in listen_atual:
            novo_listen = listen_atual.rstrip().rstrip(';').rstrip() + f'; {ip_servidor}; '
            conteudo = conteudo[:listen_match.start(1)] + novo_listen + conteudo[listen_match.end(1):]
            print(f"{Cores.VERDE}✓ listen-on atualizado: adicionado {ip_servidor}{Cores.FIM}")
            alterado = True
        else:
            print(f"{Cores.AMARELO}⚠ listen-on já contém {ip_servidor}{Cores.FIM}")

    # --- allow-query ---
    # Verifica se a rede já está na diretiva allow-query
    query_match = re.search(r'allow-query\s*\{([^}]*)\}', conteudo)
    if query_match:
        query_atual = query_match.group(1)
        if rede not in query_atual:
            novo_query = query_atual.rstrip().rstrip(';').rstrip() + f'; {rede}; '
            conteudo = conteudo[:query_match.start(1)] + novo_query + conteudo[query_match.end(1):]
            print(f"{Cores.VERDE}✓ allow-query atualizado: adicionada rede {rede}{Cores.FIM}")
            alterado = True
        else:
            print(f"{Cores.AMARELO}⚠ allow-query já contém {rede}{Cores.FIM}")

    if alterado:
        # Backup antes de escrever
        backup = f"{named_conf}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(named_conf, backup)
        print(f"{Cores.VERDE}✓ Backup: {backup}{Cores.FIM}")

        try:
            with open(named_conf, 'w') as f:
                f.write(conteudo)
        except Exception as e:
            print(f"{Cores.VERMELHO}✗ Erro ao escrever named.conf: {e}{Cores.FIM}")
            return False

        # Valida e reinicia o BIND
        sucesso, erro = executar_comando("named-checkconf", "A validar named.conf", ignorar_erro=True)
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Erro na configuração do BIND: {erro}{Cores.FIM}")
            return False

        executar_comando("systemctl restart named", "A reiniciar BIND")
        print(f"{Cores.VERDE}✓ BIND reconfigurado — rede {rede} pode agora usar este servidor DNS{Cores.FIM}")
    else:
        print(f"{Cores.VERDE}✓ BIND já estava configurado para a rede{Cores.FIM}")

    # Mostra instruções para os PCs da rede
    print(f"""
{Cores.AZUL}{Cores.NEGRITO}📋 PARA ACEDER AO SITE NOS PCs DA REDE:{Cores.FIM}

  {Cores.BRANCO}Opção A — Configurar DNS no PC (recomendado){Cores.FIM}
    Windows: Definições → Rede → IPv4 → DNS preferido: {Cores.CIANO}{ip_servidor}{Cores.FIM}
    Linux:   echo "nameserver {ip_servidor}" | sudo tee /etc/resolv.conf

  {Cores.BRANCO}Opção B — Ficheiro hosts (rápido, só para esse PC){Cores.FIM}
    Windows: C:\\Windows\\System32\\drivers\\etc\\hosts  (como administrador)
    Linux:   /etc/hosts
    {Cores.CIANO}  {ip_servidor}   {dominio}
      {ip_servidor}   www.{dominio}{Cores.FIM}
""")
    return True

def criar_pagina_boas_vindas(diretorio, dominio, ip_servidor):
    """Cria página de boas-vindas HTML"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem-vindo a {dominio}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #333;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
            max-width: 600px;
            text-align: center;
            animation: slideIn 0.8s ease-out;
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(-30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .server-icon {{
            display: inline-block;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            line-height: 60px;
            color: white;
            font-size: 30px;
            margin-bottom: 20px;
        }}
        h1 {{ color: #667eea; font-size: 2.5em; margin-bottom: 15px; }}
        .domain {{ color: #764ba2; font-weight: bold; font-size: 1.3em; margin-bottom: 25px; }}
        .info {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: left;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-item:last-child {{ border-bottom: none; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ color: #333; font-family: monospace; }}
        .success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            display: inline-block;
            margin-top: 20px;
            font-weight: bold;
        }}
        .footer {{ margin-top: 30px; color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="server-icon">🌐</div>
        <h1>Bem-vindo!</h1>
        <p class="domain">{dominio}</p>
        <p>O seu VirtualHost foi configurado com sucesso.</p>
        <div class="info">
            <div class="info-item">
                <span class="label">Domínio:</span>
                <span class="value">{dominio}</span>
            </div>
            <div class="info-item">
                <span class="label">IP do Servidor:</span>
                <span class="value">{ip_servidor}</span>
            </div>
            <div class="info-item">
                <span class="label">Protocolo:</span>
                <span class="value">HTTP/1.1</span>
            </div>
            <div class="info-item">
                <span class="label">Servidor Web:</span>
                <span class="value">Apache HTTPD</span>
            </div>
            <div class="info-item">
                <span class="label">Data de Criação:</span>
                <span class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </div>
        <div class="success">✓ VirtualHost Ativo</div>
        <div class="footer">
            <p>Administração de Sistemas 2025/2026</p>
            <p>Configuração automática via script Python</p>
        </div>
    </div>
</body>
</html>
"""
    
    index_path = os.path.join(diretorio, "index.html")
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"{Cores.VERDE}✓ Página criada: {index_path}{Cores.FIM}")
        return True
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return False

def criar_virtualhost():
    """Cria VirtualHost Apache"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ CRIAR VIRTUALHOST (Ponto 3){Cores.FIM}\n")
    
    while True:
        dominio = input(f"{Cores.BRANCO}Nome do domínio (ex: empresa.local): {Cores.FIM}").strip().lower()
        if not dominio:
            print(f"{Cores.VERMELHO}✗ Domínio não pode estar vazio!{Cores.FIM}")
            continue
        if not validar_dominio(dominio):
            print(f"{Cores.VERMELHO}✗ Formato inválido!{Cores.FIM}")
            continue
        break
    
    vhost_file = f"/etc/httpd/conf.d/{dominio}.conf"
    if os.path.exists(vhost_file):
        print(f"{Cores.AMARELO}⚠ VirtualHost '{dominio}' já existe!{Cores.FIM}")
        if input(f"{Cores.BRANCO}Sobrescrever? (s/n) [n]: {Cores.FIM}").strip().lower() != 's':
            print(f"{Cores.AMARELO}⚠ Cancelado{Cores.FIM}")
            input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
            return
    
    ip_default = obter_ip_local()
    ip_input = input(f"{Cores.BRANCO}IP do servidor [{ip_default}]: {Cores.FIM}").strip()
    ip_servidor = ip_input if ip_input else ip_default
    
    email = input(f"{Cores.BRANCO}Email admin [admin]: {Cores.FIM}").strip() or "admin"
    
    print(f"\n{Cores.AMARELO}⚠ Confirma?{Cores.FIM}")
    print(f"  Domínio: {Cores.CIANO}{dominio}{Cores.FIM}")
    print(f"  IP: {Cores.CIANO}{ip_servidor}{Cores.FIM}")
    if input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower() != 's':
        print(f"{Cores.AMARELO}⚠ Cancelado{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A CRIAR VIRTUALHOST{Cores.FIM}")
    print("=" * 50)
    
    if not verificar_instalacao_apache():
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    configurar_firewall()
    executar_comando("setsebool -P httpd_enable_homedirs on", "SELinux", ignorar_erro=True)
    
    document_root = f"/var/www/{dominio}"
    os.makedirs(document_root, exist_ok=True)
    print(f"{Cores.VERDE}✓ Diretório: {document_root}{Cores.FIM}")
    
    criar_pagina_boas_vindas(document_root, dominio, ip_servidor)
    
    executar_comando(f"chown -R apache:apache {document_root}", "A definir proprietário")
    executar_comando(f"chmod -R 755 {document_root}", "A definir permissões")
    executar_comando(f"semanage fcontext -a -t httpd_sys_content_t '{document_root}(/.*)?'", "SELinux", ignorar_erro=True)
    executar_comando(f"restorecon -Rv {document_root}", "Restaurar SELinux", ignorar_erro=True)
    
    vhost_config = f"""#
# VirtualHost para {dominio}
# Criado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#

<VirtualHost *:80>
    ServerName {dominio}
    ServerAlias www.{dominio}
    ServerAdmin {email}@{dominio}
    DocumentRoot {document_root}
    
    <Directory {document_root}>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog /var/log/httpd/{dominio}-error.log
    CustomLog /var/log/httpd/{dominio}-access.log combined
</VirtualHost>
"""
    
    try:
        with open(vhost_file, 'w') as f:
            f.write(vhost_config)
        print(f"{Cores.VERDE}✓ Configuração: {vhost_file}{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return
    
    sucesso, _ = executar_comando("httpd -t", "A verificar configuração")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro na configuração!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    executar_comando("systemctl restart httpd", "A reiniciar Apache")
    executar_comando("systemctl enable httpd", "A ativar Apache")

    configurar_dns_rede(ip_servidor, dominio)
    
    sucesso, _ = executar_comando("systemctl is-active httpd", "A verificar estado")
    if sucesso:
        print(f"{Cores.VERDE}✓ Apache ativo{Cores.FIM}")
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🧪 TESTE{Cores.FIM}")
    print("-" * 50)
    sucesso, saida = executar_comando(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost/ -H 'Host: {dominio}'", "", ignorar_erro=True)
    if sucesso and saida.strip() == "200":
        print(f"{Cores.VERDE}✓ VirtualHost responde HTTP 200{Cores.FIM}")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}      ✓ VIRTUALHOST CRIADO!{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Resumo:{Cores.FIM}")
    print(f"  • Domínio: {Cores.CIANO}{dominio}{Cores.FIM}")
    print(f"  • IP: {Cores.CIANO}{ip_servidor}{Cores.FIM}")
    print(f"  • DocumentRoot: {Cores.CIANO}{document_root}{Cores.FIM}")
    print(f"  • URL: {Cores.CIANO}http://{dominio}/{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def listar_virtualhosts():
    """Lista VirtualHosts"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📋 VIRTUALHOSTS{Cores.FIM}")
    print("-" * 50)
    
    conf_d_dir = "/etc/httpd/conf.d"
    if not os.path.exists(conf_d_dir):
        print(f"{Cores.AMARELO}Diretório não encontrado.{Cores.FIM}")
        return []
    
    vhosts = []
    for ficheiro in os.listdir(conf_d_dir):
        if ficheiro.endswith('.conf') and ficheiro not in ['README', 'autoindex.conf', 'userdir.conf', 'welcome.conf']:
            vhosts.append(ficheiro.replace('.conf', ''))
    
    if vhosts:
        print(f"{Cores.VERDE}VirtualHosts:{Cores.FIM}\n")
        for i, vhost in enumerate(vhosts, 1):
            doc_root = f"/var/www/{vhost}"
            estado = f"{Cores.VERDE}[ATIVO]{Cores.FIM}" if os.path.exists(doc_root) else f"{Cores.AMARELO}[CONFIG]{Cores.FIM}"
            print(f"  {Cores.CIANO}[{i}]{Cores.FIM} {vhost} {estado}")
    else:
        print(f"{Cores.AMARELO}Nenhum VirtualHost.{Cores.FIM}")
    
    return vhosts

def eliminar_virtualhost():
    """Elimina VirtualHost"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🗑️ ELIMINAR VIRTUALHOST{Cores.FIM}\n")
    
    vhosts = listar_virtualhosts()
    if not vhosts:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    dominio = input(f"{Cores.BRANCO}Nome do VirtualHost: {Cores.FIM}").strip().lower()
    
    encontrado = False
    for v in vhosts:
        if v.lower() == dominio:
            dominio = v
            encontrado = True
            break
    
    if not encontrado:
        print(f"{Cores.VERMELHO}✗ Não encontrado!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}⚠ Vai eliminar '{dominio}'!{Cores.FIM}")
    eliminar_conteudo = input(f"{Cores.BRANCO}Eliminar diretório /var/www/{dominio}? (s/n) [n]: {Cores.FIM}").strip().lower() or "n"
    
    if input(f"{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A ELIMINAR{Cores.FIM}")
    print("=" * 50)
    
    vhost_file = f"/etc/httpd/conf.d/{dominio}.conf"
    if os.path.exists(vhost_file):
        backup_path = f"{vhost_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(vhost_file, backup_path)
        os.remove(vhost_file)
        print(f"{Cores.VERDE}✓ Configuração eliminada{Cores.FIM}")
    
    if eliminar_conteudo == 's':
        doc_root = f"/var/www/{dominio}"
        if os.path.exists(doc_root):
            shutil.rmtree(doc_root)
            print(f"{Cores.VERDE}✓ Diretório eliminado{Cores.FIM}")
    
    for log_file in [f"/var/log/httpd/{dominio}-error.log", f"/var/log/httpd/{dominio}-access.log"]:
        if os.path.exists(log_file):
            os.remove(log_file)
            print(f"{Cores.VERDE}✓ Log eliminado: {os.path.basename(log_file)}{Cores.FIM}")
    
    executar_comando("httpd -t", "A verificar configuração")
    executar_comando("systemctl restart httpd", "A reiniciar Apache")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ VIRTUALHOST ELIMINADO!{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def menu_principal():
    """Menu principal"""
    while True:
        imprimir_cabecalho()
        
        print(f"{Cores.BRANCO}=== PONTO 3: APACHE VIRTUALHOST ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[1]{Cores.FIM} Criar VirtualHost")
        print(f"  {Cores.VERMELHO}[2]{Cores.FIM} Eliminar VirtualHost")
        print(f"  {Cores.AMARELO}[3]{Cores.FIM} Listar VirtualHosts")
        print()
        print(f"  {Cores.VERMELHO}[0]{Cores.FIM} Sair")
        print()
        
        opcao = input(f"{Cores.CIANO}Opção: {Cores.FIM}").strip()
        
        if opcao == "1":
            criar_virtualhost()
        elif opcao == "2":
            eliminar_virtualhost()
        elif opcao == "3":
            imprimir_cabecalho()
            listar_virtualhosts()
            input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        elif opcao == "0":
            print(f"\n{Cores.VERDE}✓ A sair...{Cores.FIM}")
            sys.exit(0)
        else:
            print(f"{Cores.VERMELHO}✗ Opção inválida!{Cores.FIM}")
            input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def main():
    verificar_root()
    menu_principal()

if __name__ == "__main__":
    main()