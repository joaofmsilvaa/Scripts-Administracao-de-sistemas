#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT PARTILHAS - Pontos 2 e 7
================================================================================
Administração de Sistemas 2025/2026
Consolidação: SAMBA (Windows) e NFS (Linux/Unix)

Funcionalidades:
- SAMBA: Criar, eliminar, alterar, desativar partilhas SMB
- SAMBA: Mapear partilhas Windows no Linux (CIFS)
- NFS: Criar, eliminar, alterar, desativar partilhas em /etc/exports
- NFS: Testar montagem com mount -t nfs
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
    print(f"{Cores.AMARELO}           PARTILHAS - SAMBA e NFS (Pontos 2, 7){Cores.FIM}")
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

def obter_ip_local():
    """Obtém o IP local do servidor"""
    resultado = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True)
    if resultado.returncode == 0:
        return resultado.stdout.strip()
    return "127.0.0.1"

# ==================== SAMBA (PONTO 2) ====================

def verificar_instalacao_samba():
    """Verifica se o SAMBA está instalado"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📦 VERIFICAÇÃO SAMBA{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("which smbd", shell=True, capture_output=True)
    if resultado.returncode != 0:
        print(f"{Cores.AMARELO}⚠ SAMBA não está instalado. A instalar...{Cores.FIM}")
       
        sucesso, _ = executar_comando("dnf install -y samba samba-client cifs-utils", "A instalar SAMBA")
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Falha ao instalar SAMBA!{Cores.FIM}")
            return False
        print(f"{Cores.VERDE}✓ SAMBA instalado!{Cores.FIM}")
    else:
        print(f"{Cores.VERDE}✓ SAMBA já está instalado{Cores.FIM}")
    return True

def configurar_firewall_samba():
    """Configura firewall para SAMBA"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔥 FIREWALL SAMBA{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("systemctl is-active firewalld", shell=True, capture_output=True)
    if resultado.returncode != 0:
        executar_comando("systemctl start firewalld", "A iniciar firewalld")
        executar_comando("systemctl enable firewalld", "A ativar firewalld")
    
    for servico in ['samba', 'samba-client', 'samba-dc']:
        executar_comando(f"firewall-cmd --permanent --add-service={servico}", f"A adicionar {servico}", ignorar_erro=True)
    executar_comando("firewall-cmd --reload", "A recarregar firewall")
    print(f"{Cores.VERDE}✓ Firewall SAMBA configurado{Cores.FIM}")
    return True

def backup_smb_conf():
    """Cria backup do smb.conf"""
    smb_conf = "/etc/samba/smb.conf"
    if os.path.exists(smb_conf):
        backup_path = f"{smb_conf}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(smb_conf, backup_path)
        print(f"{Cores.VERDE}✓ Backup: {backup_path}{Cores.FIM}")
        return backup_path
    return None

def ler_smb_conf():
    """Lê o ficheiro smb.conf"""
    try:
        with open("/etc/samba/smb.conf", 'r') as f:
            return f.read()
    except:
        return ""

def escrever_smb_conf(conteudo):
    """Escreve no smb.conf"""
    try:
        with open("/etc/samba/smb.conf", 'w') as f:
            f.write(conteudo)
        return True
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao escrever smb.conf: {e}{Cores.FIM}")
        return False

def listar_partilhas_samba():
    """Lista partilhas SAMBA"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📋 PARTILHAS SAMBA{Cores.FIM}")
    print("-" * 50)
    
    conteudo = ler_smb_conf()
    partilhas = re.findall(r'^\[([^\]]+)\]\s*$', conteudo, re.MULTILINE)
    partilhas_validas = [p for p in partilhas if p not in ['global', 'printers', 'print$', 'homes']]
    
    if partilhas_validas:
        print(f"{Cores.VERDE}Partilhas:{Cores.FIM}\n")
        for i, partilha in enumerate(partilhas_validas, 1):
            match_path = re.search(rf'^\[{re.escape(partilha)}\].*?^\s*path\s*=\s*(.+)$', conteudo, re.MULTILINE | re.DOTALL)
            path = match_path.group(1).strip() if match_path else "N/A"
            match_disabled = re.search(rf'^\[{re.escape(partilha)}\].*?^\s*available\s*=\s*no', conteudo, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            estado = f"{Cores.VERMELHO}[DESATIVADA]{Cores.FIM}" if match_disabled else f"{Cores.VERDE}[ATIVA]{Cores.FIM}"
            print(f"  {Cores.CIANO}[{i}]{Cores.FIM} {partilha} {estado}")
            print(f"      Path: {path}")
    else:
        print(f"{Cores.AMARELO}Nenhuma partilha configurada.{Cores.FIM}")
    return partilhas_validas

def criar_utilizador_samba(username, password):
    """Cria utilizador no sistema (se não existir) e regista-o no Samba"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}👤 CONFIGURAÇÃO DO UTILIZADOR SAMBA{Cores.FIM}")
    print("-" * 50)

    # Verifica se o utilizador já existe no sistema Linux
    resultado = subprocess.run(f"id {username}", shell=True, capture_output=True)
    if resultado.returncode != 0:
        print(f"{Cores.AMARELO}⚠ Utilizador '{username}' não existe no sistema. A criar...{Cores.FIM}")
        sucesso, _ = executar_comando(
            f"useradd -M -s /sbin/nologin {username}",
            f"A criar utilizador de sistema '{username}'"
        )
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Não foi possível criar o utilizador no sistema!{Cores.FIM}")
            return False
    else:
        print(f"{Cores.VERDE}✓ Utilizador '{username}' já existe no sistema{Cores.FIM}")

    # Regista/atualiza o utilizador na base de dados do Samba
    # O smbpasswd lê a password de stdin com o flag -s
    print(f"{Cores.CIANO}➜ A registar '{username}' na base de dados Samba...{Cores.FIM}")
    comando_smb = f"(echo '{password}'; echo '{password}') | smbpasswd -a -s {username}"
    resultado = subprocess.run(comando_smb, shell=True, capture_output=True, text=True)

    if resultado.returncode == 0:
        print(f"{Cores.VERDE}  ✓ Utilizador Samba criado/atualizado{Cores.FIM}")
    else:
        print(f"{Cores.VERMELHO}  ✗ Erro ao registar no Samba: {resultado.stderr}{Cores.FIM}")
        return False

    # Garante que o utilizador está ativo no Samba
    executar_comando(f"smbpasswd -e {username}", f"A ativar '{username}' no Samba")
    print(f"{Cores.VERDE}✓ Utilizador '{username}' configurado no Samba{Cores.FIM}")
    return True


def criar_partilha_samba():
    """Cria partilha SAMBA"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ CRIAR PARTILHA SAMBA (Ponto 2){Cores.FIM}\n")
    
    while True:
        nome = input(f"{Cores.BRANCO}Nome da partilha: {Cores.FIM}").strip()
        if not nome or ' ' in nome:
            print(f"{Cores.VERMELHO}✗ Nome inválido!{Cores.FIM}")
            continue
        if nome.lower() in ['global', 'printers', 'print$', 'homes']:
            print(f"{Cores.VERMELHO}✗ Nome reservado!{Cores.FIM}")
            continue
        break
    
    while True:
        diretorio = input(f"{Cores.BRANCO}Diretório (caminho completo): {Cores.FIM}").strip()
        if diretorio and diretorio.startswith('/'):
            break
        print(f"{Cores.VERMELHO}✗ Caminho inválido!{Cores.FIM}")
    
    if not os.path.exists(diretorio):
        criar = input(f"{Cores.AMARELO}Criar diretório? (s/n): {Cores.FIM}").strip().lower()
        if criar == 's':
            os.makedirs(diretorio, exist_ok=True)
            print(f"{Cores.VERDE}✓ Diretório criado{Cores.FIM}")
        else:
            return
    
    comentario = input(f"{Cores.BRANCO}Comentário: {Cores.FIM}").strip()
    
    print(f"\n{Cores.BRANCO}Permissões:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Leitura apenas")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Leitura e escrita")
    read_only = "yes" if (input(f"{Cores.BRANCO}Escolha (1-2) [2]: {Cores.FIM}").strip() or "2") == "1" else "no"
    
    publico = input(f"{Cores.BRANCO}Partilha pública? (s/n) [n]: {Cores.FIM}").strip().lower() or "n"
    public = "yes" if publico == "s" else "no"

    # Se a partilha não for pública, pede utilizador e password
    username = ""
    password = ""
    if public == "no":
        print(f"\n{Cores.BRANCO}Credenciais de acesso à partilha:{Cores.FIM}")
        while True:
            username = input(f"{Cores.BRANCO}Nome de utilizador: {Cores.FIM}").strip()
            if username:
                break
            print(f"{Cores.VERMELHO}✗ Nome de utilizador obrigatório!{Cores.FIM}")
        import getpass
        while True:
            password = getpass.getpass(f"{Cores.BRANCO}Password: {Cores.FIM}")
            confirm  = getpass.getpass(f"{Cores.BRANCO}Confirmar password: {Cores.FIM}")
            if password == confirm and password:
                break
            print(f"{Cores.VERMELHO}✗ Passwords não coincidem ou estão vazias!{Cores.FIM}")
    
    print(f"\n{Cores.AMARELO}⚠ Confirma?{Cores.FIM}")
    print(f"  Nome: {Cores.CIANO}{nome}{Cores.FIM}")
    print(f"  Diretório: {Cores.CIANO}{diretorio}{Cores.FIM}")
    if input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower() != 's':
        print(f"{Cores.AMARELO}⚠ Cancelado{Cores.FIM}")
        return
    
    if not verificar_instalacao_samba():
        return
    configurar_firewall_samba()
    backup_smb_conf()

    # Cria utilizador Samba antes de adicionar a partilha
    if public == "no" and username:
        if not criar_utilizador_samba(username, password):
            print(f"{Cores.VERMELHO}✗ Falha ao configurar utilizador. Partilha não criada.{Cores.FIM}")
            input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
            return

    executar_comando(f"chmod 770 {diretorio}", "A configurar permissões")
    executar_comando(f"chcon -t samba_share_t {diretorio}", "SELinux", ignorar_erro=True)

    conteudo = ler_smb_conf()

    # Linha valid users só é adicionada se a partilha não for pública
    valid_users_linha = f"\n    valid users = {username}" if public == "no" and username else ""

    nova_partilha = f"""
[{nome}]
    path = {diretorio}
    comment = {comentario or nome}
    read only = {read_only}
    public = {public}
    browseable = yes
    available = yes{valid_users_linha}
"""
    novo_conteudo = conteudo.rstrip() + "\n" + nova_partilha
    
    if escrever_smb_conf(novo_conteudo):
        print(f"{Cores.VERDE}✓ Partilha adicionada{Cores.FIM}")
    
    executar_comando("testparm -s", "A verificar configuração")
    executar_comando("systemctl restart smb", "A reiniciar SMB")
    executar_comando("systemctl restart nmb", "A reiniciar NMB")
    executar_comando("systemctl enable smb", "A ativar SMB")
    executar_comando("systemctl enable nmb", "A ativar NMB")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA SAMBA CRIADA!{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Aceda a: {Cores.CIANO}\\\\{obter_ip_local()}\\{nome}{Cores.FIM}")
    if public == "no" and username:
        print(f"{Cores.BRANCO}Utilizador: {Cores.CIANO}{username}{Cores.FIM}")
        print(f"{Cores.AMARELO}(Use estas credenciais quando o Windows pedir autenticação){Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def eliminar_partilha_samba():
    """Elimina partilha SAMBA"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🗑️ ELIMINAR PARTILHA SAMBA (Ponto 2){Cores.FIM}\n")
    
    partilhas = listar_partilhas_samba()
    if not partilhas:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    nome = input(f"{Cores.BRANCO}Nome da partilha a eliminar: {Cores.FIM}").strip()
    if nome not in partilhas:
        print(f"{Cores.VERMELHO}✗ Partilha não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    if input(f"{Cores.VERMELHO}⚠ Eliminar '{nome}'? (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    backup_smb_conf()
    conteudo = ler_smb_conf()
    padrao = rf'^\[{re.escape(nome)}\].*?(?=^\[|\Z)'
    novo_conteudo = re.sub(padrao, '', conteudo, flags=re.MULTILINE | re.DOTALL)
    novo_conteudo = re.sub(r'\n{3,}', '\n\n', novo_conteudo)
    
    if escrever_smb_conf(novo_conteudo):
        print(f"{Cores.VERDE}✓ Partilha removida{Cores.FIM}")
    
    executar_comando("systemctl restart smb", "A reiniciar SMB")
    executar_comando("systemctl restart nmb", "A reiniciar NMB")
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA ELIMINADA!{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def desativar_ativar_samba():
    """Desativa ou ativa partilha SAMBA"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🔘 DESATIVAR/ATIVAR SAMBA (Ponto 2){Cores.FIM}\n")
    
    partilhas = listar_partilhas_samba()
    if not partilhas:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    nome = input(f"{Cores.BRANCO}Nome da partilha: {Cores.FIM}").strip()
    if nome not in partilhas:
        print(f"{Cores.VERMELHO}✗ Partilha não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print(f"\n{Cores.BRANCO}Opção:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Desativar")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Ativar")
    opcao = input(f"{Cores.BRANCO}Escolha: {Cores.FIM}").strip()
    
    if opcao not in ["1", "2"]:
        return
    
    available = "no" if opcao == "1" else "yes"
    acao = "desativar" if opcao == "1" else "ativar"
    
    if input(f"{Cores.AMARELO}⚠ {acao} '{nome}'? (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    backup_smb_conf()
    conteudo = ler_smb_conf()
    
    padrao = rf'^(\[{re.escape(nome)}\].*?^\s*available\s*=\s*)(.+)$'
    if re.search(padrao, conteudo, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE):
        conteudo = re.sub(padrao, rf'\1{available}', conteudo, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    else:
        padrao_secao = rf'^(\[{re.escape(nome)}\].*?)$'
        conteudo = re.sub(padrao_secao, rf'\1\n    available = {available}', conteudo, flags=re.MULTILINE | re.DOTALL, count=1)
    
    if escrever_smb_conf(conteudo):
        print(f"{Cores.VERDE}✓ Partilha {acao}da{Cores.FIM}")
    
    executar_comando("systemctl restart smb", "A reiniciar SMB")
    executar_comando("systemctl restart nmb", "A reiniciar NMB")
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA {acao.upper()}DA!{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def mapear_partilha_windows():
    """Mapeia partilha Windows no Linux (smbmount/CIFS)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🔗 MAPEAR PARTILHA WINDOWS (Ponto 2){Cores.FIM}\n")
    
    ip_windows = input(f"{Cores.BRANCO}IP do servidor Windows: {Cores.FIM}").strip()
    nome_partilha = input(f"{Cores.BRANCO}Nome da partilha: {Cores.FIM}").strip()
    
    if not ip_windows or not nome_partilha:
        print(f"{Cores.VERMELHO}✗ Dados obrigatórios!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    ponto_montagem = input(f"{Cores.BRANCO}Ponto de montagem [/mnt/windows]: {Cores.FIM}").strip() or "/mnt/windows"
    usar_cred = input(f"{Cores.BRANCO}Usar credenciais? (s/n) [n]: {Cores.FIM}").strip().lower() or "n"
    
    username = ""
    password = ""
    if usar_cred == "s":
        username = input(f"{Cores.BRANCO}Username: {Cores.FIM}").strip()
        password = input(f"{Cores.BRANCO}Password: {Cores.FIM}").strip()
    
    if not os.path.exists(ponto_montagem):
        os.makedirs(ponto_montagem, exist_ok=True)
        print(f"{Cores.VERDE}✓ Ponto de montagem criado{Cores.FIM}")
    
    share_path = f"//{ip_windows}/{nome_partilha}"
    
    if usar_cred == "s" and username and password:
        comando = f"mount -t cifs '{share_path}' '{ponto_montagem}' -o username='{username}',password='{password}',iocharset=utf8"
    else:
        comando = f"mount -t cifs '{share_path}' '{ponto_montagem}' -o guest,iocharset=utf8"
    
    print(f"\n{Cores.CIANO}➜ A montar...{Cores.FIM}")
    sucesso, saida = executar_comando(comando, "", ignorar_erro=True)
    
    if sucesso:
        print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA MAPEADA!{Cores.FIM}")
        print(f"  Origem: {Cores.CIANO}{share_path}{Cores.FIM}")
        print(f"  Montado: {Cores.CIANO}{ponto_montagem}{Cores.FIM}")
        
        print(f"\n{Cores.AZUL}Conteúdo:{Cores.FIM}")
        executar_comando(f"ls -la '{ponto_montagem}'", "")
        
        adicionar_fstab = input(f"\n{Cores.BRANCO}Adicionar ao /etc/fstab? (s/n): {Cores.FIM}").strip().lower()
        if adicionar_fstab == 's':
            if usar_cred == "s":
                cred_file = f"/root/.smbcredentials_{nome_partilha}"
                with open(cred_file, 'w') as f:
                    f.write(f"username={username}\npassword={password}\n")
                os.chmod(cred_file, 0o600)
                fstab_entry = f"{share_path}    {ponto_montagem}    cifs    credentials={cred_file},iocharset=utf8,_netdev    0    0\n"
            else:
                fstab_entry = f"{share_path}    {ponto_montagem}    cifs    guest,iocharset=utf8,_netdev    0    0\n"
            
            with open("/etc/fstab", 'a') as f:
                f.write(fstab_entry)
            print(f"{Cores.VERDE}✓ Adicionado ao /etc/fstab{Cores.FIM}")
    else:
        print(f"\n{Cores.VERMELHO}✗ ERRO: {saida}{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

# ==================== NFS (PONTO 7) ====================

def verificar_instalacao_nfs():
    """Verifica se o NFS está instalado"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📦 VERIFICAÇÃO NFS{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("rpm -q nfs-utils", shell=True, capture_output=True)
    if resultado.returncode != 0:
        print(f"{Cores.AMARELO}⚠ NFS não está instalado. A instalar...{Cores.FIM}")
        
        sucesso, _ = executar_comando("dnf install -y nfs-utils", "A instalar NFS")
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Falha ao instalar NFS!{Cores.FIM}")
            return False
        print(f"{Cores.VERDE}✓ NFS instalado!{Cores.FIM}")
    else:
        print(f"{Cores.VERDE}✓ NFS já está instalado{Cores.FIM}")
    return True

def configurar_firewall_nfs():
    """Configura firewall para NFS"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔥 FIREWALL NFS{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("systemctl is-active firewalld", shell=True, capture_output=True)
    if resultado.returncode != 0:
        executar_comando("systemctl start firewalld", "A iniciar firewalld")
        executar_comando("systemctl enable firewalld", "A ativar firewalld")
    
    for servico in ['nfs', 'rpc-bind', 'mountd']:
        executar_comando(f"firewall-cmd --permanent --add-service={servico}", f"A adicionar {servico}", ignorar_erro=True)
    executar_comando("firewall-cmd --reload", "A recarregar firewall")
    print(f"{Cores.VERDE}✓ Firewall NFS configurado{Cores.FIM}")
    return True

def backup_exports():
    """Cria backup do /etc/exports"""
    exports_file = "/etc/exports"
    if os.path.exists(exports_file):
        backup_path = f"{exports_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(exports_file, backup_path)
        print(f"{Cores.VERDE}✓ Backup: {backup_path}{Cores.FIM}")
        return backup_path
    return None

def ler_exports():
    """Lê o /etc/exports"""
    try:
        with open("/etc/exports", 'r') as f:
            return f.read()
    except:
        return ""

def escrever_exports(conteudo):
    """Escreve no /etc/exports"""
    try:
        with open("/etc/exports", 'w') as f:
            f.write(conteudo)
        return True
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return False

def listar_partilhas_nfs():
    """Lista partilhas NFS"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📋 PARTILHAS NFS{Cores.FIM}")
    print("-" * 50)
    
    conteudo = ler_exports()
    partilhas = []
    linhas = conteudo.split('\n')
    
    print(f"{Cores.VERDE}Partilhas:{Cores.FIM}\n")
    
    for i, linha in enumerate(linhas, 1):
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            continue
        
        match = re.match(r'^(/\S+)\s+(.+)$', linha)
        if match:
            diretorio = match.group(1)
            opcoes = match.group(2)
            ativa = not linha.startswith('#')
            estado = f"{Cores.VERDE}[ATIVA]{Cores.FIM}" if ativa else f"{Cores.VERMELHO}[DESATIVADA]{Cores.FIM}"
            partilhas.append({'diretorio': diretorio, 'opcoes': opcoes, 'ativa': ativa})
            print(f"  {Cores.CIANO}[{len(partilhas)}]{Cores.FIM} {diretorio} {estado}")
            print(f"      Opções: {opcoes}")
    
    if not partilhas:
        print(f"{Cores.AMARELO}Nenhuma partilha configurada.{Cores.FIM}")
    
    return partilhas

def criar_partilha_nfs():
    """Cria partilha NFS"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ CRIAR PARTILHA NFS (Ponto 7){Cores.FIM}\n")
    
    while True:
        diretorio = input(f"{Cores.BRANCO}Diretório a partilhar: {Cores.FIM}").strip()
        if diretorio and diretorio.startswith('/'):
            break
        print(f"{Cores.VERMELHO}✗ Caminho inválido!{Cores.FIM}")
    
    if not os.path.exists(diretorio):
        criar = input(f"{Cores.AMARELO}Criar diretório? (s/n): {Cores.FIM}").strip().lower()
        if criar == 's':
            os.makedirs(diretorio, exist_ok=True)
            print(f"{Cores.VERDE}✓ Diretório criado{Cores.FIM}")
        else:
            return
    
    print(f"\n{Cores.AZUL}Clientes:{Cores.FIM}")
    print(f"  {Cores.CIANO}*{Cores.FIM} - Todos")
    print(f"  {Cores.CIANO}192.168.1.0/24{Cores.FIM} - Rede específica")
    clientes = input(f"{Cores.BRANCO}Clientes [*]: {Cores.FIM}").strip() or "*"
    
    print(f"\n{Cores.BRANCO}Permissões:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Somente leitura (ro)")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Leitura e escrita (rw)")
    rw = "rw" if (input(f"{Cores.BRANCO}Escolha (1-2) [2]: {Cores.FIM}").strip() or "2") == "2" else "ro"
    
    sync_async = input(f"{Cores.BRANCO}Síncrono ou assíncrono? (sync/async) [sync]: {Cores.FIM}").strip() or "sync"
    no_root = input(f"{Cores.BRANCO}Permitir root remoto? (s/n) [n]: {Cores.FIM}").strip().lower() or "n"
    no_root_squash = "no_root_squash" if no_root == 's' else "root_squash"
    
    opcoes = f"{rw},{sync_async},{no_root_squash},no_subtree_check"
    
    print(f"\n{Cores.AMARELO}⚠ Confirma?{Cores.FIM}")
    print(f"  Diretório: {Cores.CIANO}{diretorio}{Cores.FIM}")
    print(f"  Clientes: {Cores.CIANO}{clientes}{Cores.FIM}")
    print(f"  Opções: {Cores.CIANO}{opcoes}{Cores.FIM}")
    if input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    if not verificar_instalacao_nfs():
        return
    configurar_firewall_nfs()
    backup_exports()
    
    executar_comando(f"chmod 777 {diretorio}", "A configurar permissões")
    
    conteudo = ler_exports()
    nova_linha = f"{diretorio}\t{clientes}({opcoes})\n"
    novo_conteudo = conteudo.rstrip() + "\n" + nova_linha
    
    if escrever_exports(novo_conteudo):
        print(f"{Cores.VERDE}✓ Partilha adicionada{Cores.FIM}")
    
    executar_comando("exportfs -ra", "A exportar partilhas")
    executar_comando("systemctl restart nfs-server", "A reiniciar NFS")
    executar_comando("systemctl restart rpcbind", "A reiniciar rpcbind")
    executar_comando("systemctl enable nfs-server", "A ativar NFS")
    executar_comando("systemctl enable rpcbind", "A ativar rpcbind")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA NFS CRIADA!{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Teste no cliente:{Cores.FIM}")
    print(f"  {Cores.CIANO}showmount -e {obter_ip_local()}{Cores.FIM}")
    print(f"  {Cores.CIANO}mount -t nfs {obter_ip_local()}:{diretorio} /mnt{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def eliminar_partilha_nfs():
    """Elimina partilha NFS"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🗑️ ELIMINAR PARTILHA NFS (Ponto 7){Cores.FIM}\n")
    
    partilhas = listar_partilhas_nfs()
    if not partilhas:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    diretorio = input(f"{Cores.BRANCO}Diretório a eliminar: {Cores.FIM}").strip()
    
    encontrada = False
    for p in partilhas:
        if p['diretorio'] == diretorio:
            encontrada = True
            break
    
    if not encontrada:
        print(f"{Cores.VERMELHO}✗ Partilha não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    if input(f"{Cores.VERMELHO}⚠ Eliminar '{diretorio}'? (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    backup_exports()
    conteudo = ler_exports()
    linhas = conteudo.split('\n')
    novas_linhas = [l for l in linhas if not l.strip().startswith(diretorio)]
    
    if escrever_exports('\n'.join(novas_linhas)):
        print(f"{Cores.VERDE}✓ Partilha removida{Cores.FIM}")
    
    executar_comando("exportfs -ra", "A atualizar exports")
    executar_comando("systemctl restart nfs-server", "A reiniciar NFS")
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA ELIMINADA!{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def desativar_ativar_nfs():
    """Desativa ou ativa partilha NFS"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🔘 DESATIVAR/ATIVAR NFS (Ponto 7){Cores.FIM}\n")
    
    partilhas = listar_partilhas_nfs()
    if not partilhas:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    diretorio = input(f"{Cores.BRANCO}Diretório: {Cores.FIM}").strip()
    
    partilha = None
    for p in partilhas:
        if p['diretorio'] == diretorio:
            partilha = p
            break
    
    if not partilha:
        print(f"{Cores.VERMELHO}✗ Partilha não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print(f"\n{Cores.BRANCO}Opção:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Desativar")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Ativar")
    opcao = input(f"{Cores.BRANCO}Escolha: {Cores.FIM}").strip()
    
    if opcao not in ["1", "2"]:
        return
    
    acao = "desativar" if opcao == "1" else "ativar"
    
    if input(f"{Cores.AMARELO}⚠ {acao} '{diretorio}'? (s/n): {Cores.FIM}").strip().lower() != 's':
        return
    
    backup_exports()
    conteudo = ler_exports()
    linhas = conteudo.split('\n')
    novas_linhas = []
    
    for linha in linhas:
        if linha.strip().startswith(diretorio):
            if opcao == "1" and not linha.strip().startswith('#'):
                linha = '#' + linha
            elif opcao == "2" and linha.strip().startswith('#'):
                linha = linha[1:]
        novas_linhas.append(linha)
    
    if escrever_exports('\n'.join(novas_linhas)):
        print(f"{Cores.VERDE}✓ Partilha {acao}da{Cores.FIM}")
    
    executar_comando("exportfs -ra", "A atualizar exports")
    executar_comando("systemctl restart nfs-server", "A reiniciar NFS")
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA {acao.upper()}DA!{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

def testar_partilha_nfs():
    """Testa partilha NFS com mount -t nfs"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🧪 TESTAR PARTILHA NFS (Ponto 7){Cores.FIM}\n")
    
    partilhas = listar_partilhas_nfs()
    if not partilhas:
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    print()
    diretorio = input(f"{Cores.BRANCO}Diretório a testar: {Cores.FIM}").strip()
    
    encontrada = False
    for p in partilhas:
        if p['diretorio'] == diretorio:
            encontrada = True
            break
    
    if not encontrada:
        print(f"{Cores.VERMELHO}✗ Partilha não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        return
    
    ponto_montagem = input(f"{Cores.BRANCO}Ponto de montagem [/mnt/nfs_test]: {Cores.FIM}").strip() or "/mnt/nfs_test"
    
    if not os.path.exists(ponto_montagem):
        os.makedirs(ponto_montagem, exist_ok=True)
        print(f"{Cores.VERDE}✓ Ponto de montagem criado{Cores.FIM}")
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔄 A TESTAR MONTAGEM{Cores.FIM}")
    print("-" * 50)
    
    ip_local = obter_ip_local()
    executar_comando(f"umount {ponto_montagem} 2>/dev/null", "", ignorar_erro=True)
    
    comando = f"mount -t nfs {ip_local}:{diretorio} {ponto_montagem}"
    sucesso, saida = executar_comando(comando, f"A montar {diretorio}", ignorar_erro=True)
    
    if sucesso:
        print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ PARTILHA MONTADA!{Cores.FIM}")
        
        print(f"\n{Cores.AZUL}Montagens NFS:{Cores.FIM}")
        executar_comando("mount | grep nfs", "")
        
        print(f"\n{Cores.AZUL}Teste de escrita:{Cores.FIM}")
        test_file = f"{ponto_montagem}/nfs_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(test_file, 'w') as f:
                f.write("Teste NFS - OK\n")
            print(f"{Cores.VERDE}✓ Escrita OK{Cores.FIM}")
            os.remove(test_file)
            print(f"{Cores.VERDE}✓ Ficheiro removido{Cores.FIM}")
        except Exception as e:
            print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        
        print(f"\n{Cores.AZUL}Conteúdo:{Cores.FIM}")
        executar_comando(f"ls -la {ponto_montagem}", "")
        
        if input(f"\n{Cores.BRANCO}Desmontar? (s/n) [s]: {Cores.FIM}").strip().lower() != 'n':
            executar_comando(f"umount {ponto_montagem}", "A desmontar")
            print(f"{Cores.VERDE}✓ Desmontado{Cores.FIM}")
    else:
        print(f"\n{Cores.VERMELHO}✗ ERRO: {saida}{Cores.FIM}")
        print(f"\n{Cores.AMARELO}Dicas:{Cores.FIM}")
        print(f"  • systemctl status nfs-server")
        print(f"  • firewall-cmd --list-services")
        print(f"  • ls -ld {diretorio}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")

# ==================== MENU PRINCIPAL ====================

def menu_principal():
    """Menu principal"""
    while True:
        imprimir_cabecalho()
        
        print(f"{Cores.BRANCO}=== PONTO 2: SAMBA (Windows) ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[1]{Cores.FIM} Criar partilha SAMBA")
        print(f"  {Cores.VERDE}[2]{Cores.FIM} Eliminar partilha SAMBA")
        print(f"  {Cores.VERDE}[3]{Cores.FIM} Desativar/Ativar partilha SAMBA")
        print(f"  {Cores.CIANO}[4]{Cores.FIM} Mapear partilha Windows (CIFS)")
        print(f"  {Cores.AMARELO}[5]{Cores.FIM} Listar partilhas SAMBA")
        print()
        print(f"{Cores.BRANCO}=== PONTO 7: NFS (Linux/Unix) ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[6]{Cores.FIM} Criar partilha NFS")
        print(f"  {Cores.VERDE}[7]{Cores.FIM} Eliminar partilha NFS")
        print(f"  {Cores.VERDE}[8]{Cores.FIM} Desativar/Ativar partilha NFS")
        print(f"  {Cores.CIANO}[9]{Cores.FIM} Testar partilha NFS (mount -t nfs)")
        print(f"  {Cores.AMARELO}[10]{Cores.FIM} Listar partilhas NFS")
        print()
        print(f"  {Cores.VERMELHO}[0]{Cores.FIM} Sair")
        print()
        
        opcao = input(f"{Cores.CIANO}Opção: {Cores.FIM}").strip()
        
        if opcao == "1":
            criar_partilha_samba()
        elif opcao == "2":
            eliminar_partilha_samba()
        elif opcao == "3":
            desativar_ativar_samba()
        elif opcao == "4":
            mapear_partilha_windows()
        elif opcao == "5":
            imprimir_cabecalho()
            listar_partilhas_samba()
            input(f"\n{Cores.AMARELO}Pressione ENTER...{Cores.FIM}")
        elif opcao == "6":
            criar_partilha_nfs()
        elif opcao == "7":
            eliminar_partilha_nfs()
        elif opcao == "8":
            desativar_ativar_nfs()
        elif opcao == "9":
            testar_partilha_nfs()
        elif opcao == "10":
            imprimir_cabecalho()
            listar_partilhas_nfs()
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
