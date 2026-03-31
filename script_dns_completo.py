#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SCRIPT DNS COMPLETO - Pontos 1, 4, 5 e 6
================================================================================
Administração de Sistemas 2025/2026
Consolidação: Zonas Master, Registos A/MX, Zonas Reverse, Eliminar

Funcionalidades:
- Criar zonas master (forward) DNS automaticamente
- Adicionar registos do tipo A e MX
- Criar zonas reverse DNS
- Eliminar zonas DNS, zonas reverse e VirtualHosts
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
    print(f"{Cores.AMARELO}              DNS COMPLETO (Pontos 1, 4, 5, 6){Cores.FIM}")
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

def verificar_instalacao_bind():
    """Verifica se o BIND está instalado e instala se necessário"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📦 VERIFICAÇÃO DE PRÉ-REQUISITOS{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("which named", shell=True, capture_output=True)
    if resultado.returncode != 0:
        print(f"{Cores.AMARELO}⚠ BIND não está instalado. A instalar...{Cores.FIM}")
        executar_comando("dnf update -y", "A atualizar repositórios")
        sucesso, _ = executar_comando("dnf install -y bind bind-utils", "A instalar BIND DNS Server")
        if not sucesso:
            print(f"{Cores.VERMELHO}✗ Falha ao instalar BIND!{Cores.FIM}")
            return False
        print(f"{Cores.VERDE}✓ BIND instalado com sucesso!{Cores.FIM}")
    else:
        print(f"{Cores.VERDE}✓ BIND já está instalado{Cores.FIM}")
    return True

def configurar_firewall():
    """Configura o firewall para permitir tráfego DNS"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔥 CONFIGURAÇÃO DO FIREWALL{Cores.FIM}")
    print("-" * 50)
    
    resultado = subprocess.run("systemctl is-active firewalld", shell=True, capture_output=True)
    if resultado.returncode != 0:
        executar_comando("systemctl start firewalld", "A iniciar firewalld")
        executar_comando("systemctl enable firewalld", "A ativar firewalld no arranque")
    
    executar_comando("firewall-cmd --permanent --add-service=dns", "A adicionar serviço DNS ao firewall", ignorar_erro=True)
    executar_comando("firewall-cmd --reload", "A recarregar firewall")
    print(f"{Cores.VERDE}✓ Firewall configurado{Cores.FIM}")
    return True

def validar_dominio(dominio):
    """Valida o formato do nome de domínio"""
    padrao = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(padrao, dominio) is not None

def validar_ip(ip):
    """Valida o formato do endereço IP"""
    padrao = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(padrao, ip):
        return False
    octetos = ip.split('.')
    for octeto in octetos:
        if int(octeto) > 255:
            return False
    return True

def obter_ip_local():
    """Obtém o IP local do servidor"""
    resultado = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True)
    if resultado.returncode == 0:
        return resultado.stdout.strip()
    return "127.0.0.1"

def backup_ficheiro(ficheiro):
    """Cria backup de um ficheiro"""
    if os.path.exists(ficheiro):
        backup_path = f"{ficheiro}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(ficheiro, backup_path)
        print(f"{Cores.VERDE}✓ Backup criado: {backup_path}{Cores.FIM}")
        return backup_path
    return None

def obter_ficheiro_zona(dominio):
    """Obtém o caminho do ficheiro de zona a partir do named.conf"""
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        padrao = rf'zone\s+"{re.escape(dominio)}"\s+IN\s*\{{[^}}]*file\s+"([^"]+)"'
        match = re.search(padrao, conteudo, re.DOTALL)
        if match:
            return match.group(1)
        return f"/var/named/{dominio}.zone"
    except:
        return f"/var/named/{dominio}.zone"

def atualizar_serial(ficheiro_zona):
    """Atualiza o serial no ficheiro de zona"""
    try:
        with open(ficheiro_zona, 'r') as f:
            linhas = f.readlines()
        novo_serial = datetime.now().strftime("%Y%m%d01")
        for i, linha in enumerate(linhas):
            if re.search(r'\d{8,}', linha) and not re.match(r'^[\s]*[;#]', linha):
                linhas[i] = re.sub(r'(\s)\d{8,}(\s*;)', rf'\g<1>{novo_serial}\g<2>', linha)
                break
        with open(ficheiro_zona, 'w') as f:
            f.writelines(linhas)
        return True
    except Exception as e:
        print(f"{Cores.AMARELO}⚠ Não foi possível atualizar serial: {e}{Cores.FIM}")
        return False

def listar_zonas_forward():
    """Lista as zonas forward DNS configuradas"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📋 ZONAS FORWARD DNS{Cores.FIM}")
    print("-" * 50)
    
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        zonas = re.findall(r'zone\s+"([^"]+)"\s+IN', conteudo)
        zonas_forward = [z for z in zonas if not z.endswith('.in-addr.arpa')]
        
        if zonas_forward:
            print(f"{Cores.VERDE}Zonas forward:{Cores.FIM}\n")
            for i, zona in enumerate(zonas_forward, 1):
                print(f"  {Cores.CIANO}[{i}]{Cores.FIM} {zona}")
        else:
            print(f"{Cores.AMARELO}Nenhuma zona forward configurada.{Cores.FIM}")
        return zonas_forward
    except Exception as e:
        print(f"{Cores.VERMELHO}Erro ao ler configuração: {e}{Cores.FIM}")
        return []

def listar_zonas_reverse():
    """Lista as zonas reverse DNS configuradas"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}📋 ZONAS REVERSE DNS{Cores.FIM}")
    print("-" * 50)
    
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        zonas = re.findall(r'zone\s+"([^"]+\.in-addr\.arpa)"\s+IN', conteudo)
        
        if zonas:
            print(f"{Cores.VERDE}Zonas reverse:{Cores.FIM}\n")
            for i, zona in enumerate(zonas, 1):
                print(f"  {Cores.CIANO}[{i}]{Cores.FIM} {zona}")
        else:
            print(f"{Cores.AMARELO}Nenhuma zona reverse configurada.{Cores.FIM}")
        return zonas
    except Exception as e:
        print(f"{Cores.VERMELHO}Erro ao ler configuração: {e}{Cores.FIM}")
        return []

def configurar_named_conf(dominio, arquivo_zona, reverse=False):
    """Adiciona a zona ao named.conf com sintaxe correta"""
    named_conf = "/etc/named.conf"
    
    if not os.path.exists(f"{named_conf}.backup"):
        shutil.copy(named_conf, f"{named_conf}.backup")
        print(f"{Cores.VERDE}✓ Backup criado: {named_conf}.backup{Cores.FIM}")
    
    try:
        with open(named_conf, 'r') as f:
            conteudo = f.read()
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao ler named.conf: {e}{Cores.FIM}")
        return False
    
    if f'zone "{dominio}"' in conteudo:
        print(f"{Cores.AMARELO}⚠ Zona '{dominio}' já existe no named.conf{Cores.FIM}")
        return True
    
    # Configuração da zona com sintaxe correta
    config_zona = f'''zone "{dominio}" IN {{
    type master;
    file "{arquivo_zona}";
    allow-update {{ none; }};
}};
'''
    
    # Encontrar a posição correta para inserir (antes das includes ou no final)
    linhas = conteudo.split('\n')
    posicao_insercao = len(linhas)
    
    # Procurar por linhas include ou o fim do ficheiro
    for i, linha in enumerate(linhas):
        if 'include' in linha.lower() and linha.strip().startswith('include'):
            posicao_insercao = i
            break
    
    # Inserir a configuração da zona
    linhas.insert(posicao_insercao, config_zona)
    novo_conteudo = '\n'.join(linhas)
    
    try:
        with open(named_conf, 'w') as f:
            f.write(novo_conteudo)
        print(f"{Cores.VERDE}✓ Zona adicionada ao named.conf{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao atualizar named.conf: {e}{Cores.FIM}")
        return False
    return True

def verificar_configuracao_dns():
    """Verifica a sintaxe da configuração do BIND"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔍 VERIFICAÇÃO DA CONFIGURAÇÃO{Cores.FIM}")
    print("-" * 50)
    
    sucesso, saida = executar_comando("named-checkconf", "A verificar sintaxe do named.conf")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro na configuração do named.conf!{Cores.FIM}")
        print(f"{Cores.VERMELHO}{saida}{Cores.FIM}")
        return False
    print(f"{Cores.VERDE}✓ Configuração do named.conf válida{Cores.FIM}")
    return True

def reiniciar_bind():
    """Reinicia o serviço BIND"""
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🔄 REINICIO DO SERVIÇO{Cores.FIM}")
    print("-" * 50)
    
    executar_comando("systemctl restart named", "A reiniciar BIND")
    executar_comando("systemctl enable named", "A ativar BIND no arranque")
    
    sucesso, saida = executar_comando("systemctl is-active named", "A verificar estado do serviço")
    if sucesso and "active" in saida:
        print(f"{Cores.VERDE}✓ Serviço BIND está ativo{Cores.FIM}")
        return True
    else:
        print(f"{Cores.VERMELHO}✗ Serviço BIND não está ativo!{Cores.FIM}")
        return False

# ==================== PONTO 1: CRIAR ZONA MASTER ====================

def criar_zona_master():
    """Cria uma zona master DNS (Ponto 1)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ CRIAR ZONA MASTER DNS (Ponto 1){Cores.FIM}\n")
    
    while True:
        dominio = input(f"{Cores.BRANCO}Nome do domínio (ex: empresa.local): {Cores.FIM}").strip().lower()
        if not dominio:
            print(f"{Cores.VERMELHO}✗ Domínio não pode estar vazio!{Cores.FIM}")
            continue
        if not validar_dominio(dominio):
            print(f"{Cores.VERMELHO}✗ Formato de domínio inválido!{Cores.FIM}")
            continue
        break
    
    ip_default = obter_ip_local()
    ip_input = input(f"{Cores.BRANCO}IP do servidor [{ip_default}]: {Cores.FIM}").strip()
    ip_servidor = ip_input if ip_input else ip_default
    
    if not validar_ip(ip_servidor):
        print(f"{Cores.VERMELHO}✗ IP inválido! A usar {ip_default}{Cores.FIM}")
        ip_servidor = ip_default
    
    print(f"\n{Cores.AMARELO}⚠ Confirma a criação da zona?{Cores.FIM}")
    print(f"  Domínio: {Cores.CIANO}{dominio}{Cores.FIM}")
    print(f"  IP: {Cores.CIANO}{ip_servidor}{Cores.FIM}")
    confirmar = input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower()
    
    if confirmar != 's':
        print(f"{Cores.AMARELO}⚠ Operação cancelada{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A INICIAR CONFIGURAÇÃO{Cores.FIM}")
    print("=" * 50)
    
    if not verificar_instalacao_bind():
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    configurar_firewall()
    
    # Criar ficheiro de zona
    os.makedirs("/var/named", exist_ok=True)
    arquivo_zona = f"/var/named/{dominio}.zone"
    serial = datetime.now().strftime("%Y%m%d01")
    
    # Conteúdo da zona DNS formatado corretamente
    conteudo_zona = f"""; Zona DNS para {dominio}
; Gerado automaticamente - Ponto 1
; Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

$TTL 86400
@       IN      SOA     ns1.{dominio}.     admin.{dominio}. (
                        {serial}    ; Serial
                        3600        ; Refresh
                        1800        ; Retry
                        604800      ; Expire
                        86400       ; Minimum TTL
)

; Servidores de Nomes
@       IN      NS      ns1.{dominio}.
@       IN      NS      ns2.{dominio}.

; Registos A
@       IN      A       {ip_servidor}
ns1     IN      A       {ip_servidor}
ns2     IN      A       {ip_servidor}
www     IN      A       {ip_servidor}
ftp     IN      A       {ip_servidor}
mail    IN      A       {ip_servidor}

; Registo CNAME
web     IN      CNAME   www
"""
    
    try:
        with open(arquivo_zona, 'w') as f:
            f.write(conteudo_zona)
        print(f"{Cores.VERDE}✓ Ficheiro de zona criado: {arquivo_zona}{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao criar ficheiro de zona: {e}{Cores.FIM}")
        return
    
    executar_comando(f"chown named:named {arquivo_zona}", "A definir permissões")
    executar_comando(f"chmod 640 {arquivo_zona}", "A definir permissões de leitura")
    
    configurar_named_conf(dominio, arquivo_zona)
    
    if not verificar_configuracao_dns():
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    sucesso, _ = executar_comando(f"named-checkzone {dominio} {arquivo_zona}", "A verificar zona")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro no ficheiro de zona!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    if not reiniciar_bind():
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    # Testar
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🧪 TESTE DE RESOLUÇÃO{Cores.FIM}")
    print("-" * 50)
    sucesso, saida = executar_comando(f"dig @127.0.0.1 {dominio} A +short", "", ignorar_erro=True)
    if sucesso and ip_servidor in saida:
        print(f"{Cores.VERDE}✓ Resolução DNS funcionando!{Cores.FIM}")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}         ✓ ZONA MASTER CRIADA COM SUCESSO!{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Resumo:{Cores.FIM}")
    print(f"  • Domínio: {Cores.CIANO}{dominio}{Cores.FIM}")
    print(f"  • IP: {Cores.CIANO}{ip_servidor}{Cores.FIM}")
    print(f"  • Ficheiro: {Cores.CIANO}{arquivo_zona}{Cores.FIM}")
    print(f"\n{Cores.AMARELO}Nota: Configure /etc/resolv.conf com 'nameserver 127.0.0.1'{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

# ==================== PONTO 4: REGISTOS A E MX ====================

def adicionar_registo_a():
    """Adiciona um registo do tipo A (Ponto 4)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ ADICIONAR REGISTO A (Ponto 4){Cores.FIM}\n")
    
    zonas = listar_zonas_forward()
    if not zonas:
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print()
    dominio = input(f"{Cores.BRANCO}Nome da zona/domínio: {Cores.FIM}").strip().lower()
    if dominio not in zonas:
        print(f"{Cores.VERMELHO}✗ Zona não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}Dados do registo A:{Cores.FIM}\n")
    nome_host = input(f"{Cores.BRANCO}Nome do host (@ para raiz): {Cores.FIM}").strip()
    ip = input(f"{Cores.BRANCO}Endereço IP: {Cores.FIM}").strip()
    
    if not ip or not validar_ip(ip):
        print(f"{Cores.VERMELHO}✗ IP inválido!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    nome_registo = "@" if not nome_host or nome_host == '@' else nome_host
    fqdn = dominio if nome_registo == "@" else f"{nome_host}.{dominio}"
    
    print(f"\n{Cores.AMARELO}⚠ Confirma a adição do registo?{Cores.FIM}")
    print(f"  Tipo: {Cores.CIANO}A{Cores.FIM}")
    print(f"  Nome: {Cores.CIANO}{fqdn}{Cores.FIM}")
    print(f"  IP: {Cores.CIANO}{ip}{Cores.FIM}")
    confirmar = input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower()
    
    if confirmar != 's':
        print(f"{Cores.AMARELO}⚠ Operação cancelada{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    ficheiro_zona = obter_ficheiro_zona(dominio)
    backup_ficheiro(ficheiro_zona)
    
    try:
        with open(ficheiro_zona, 'r') as f:
            conteudo = f.read()
        
        linha_registo = f"{nome_registo}\tIN\tA\t{ip}\n"
        linhas = conteudo.split('\n')
        posicao = len(linhas)
        
        for i, linha in enumerate(linhas):
            if re.match(r'^[\s]*[;#]\s*Registos?\s+(CNAME|MX|Final)', linha, re.IGNORECASE):
                posicao = i
                break
        
        linhas.insert(posicao, linha_registo)
        
        with open(ficheiro_zona, 'w') as f:
            f.write('\n'.join(linhas))
        
        print(f"{Cores.VERDE}✓ Registo A adicionado{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return
    
    atualizar_serial(ficheiro_zona)
    
    sucesso, _ = executar_comando(f"named-checkzone {dominio} {ficheiro_zona}", "A verificar zona")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro na zona!{Cores.FIM}")
        return
    
    reiniciar_bind()
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ REGISTO A ADICIONADO!{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Teste: dig @{obter_ip_local()} {fqdn} A{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

def adicionar_registo_mx():
    """Adiciona um registo do tipo MX (Ponto 4)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ ADICIONAR REGISTO MX (Ponto 4){Cores.FIM}\n")
    
    zonas = listar_zonas_forward()
    if not zonas:
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print()
    dominio = input(f"{Cores.BRANCO}Nome da zona/domínio: {Cores.FIM}").strip().lower()
    if dominio not in zonas:
        print(f"{Cores.VERMELHO}✗ Zona não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}Dados do registo MX:{Cores.FIM}\n")
    print(f"  {Cores.CIANO}[10]{Cores.FIM} Alta prioridade")
    print(f"  {Cores.CIANO}[20]{Cores.FIM} Média prioridade")
    print(f"  {Cores.CIANO}[30]{Cores.FIM} Baixa prioridade")
    
    prioridade = input(f"{Cores.BRANCO}Prioridade [10]: {Cores.FIM}").strip() or "10"
    servidor_mail = input(f"{Cores.BRANCO}Servidor de email (ex: mail.{dominio}): {Cores.FIM}").strip()
    
    if not servidor_mail:
        print(f"{Cores.VERMELHO}✗ Servidor de email é obrigatório!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    if not servidor_mail.endswith('.'):
        servidor_mail += '.'
    
    print(f"\n{Cores.AMARELO}⚠ Confirma a adição do registo?{Cores.FIM}")
    print(f"  Tipo: {Cores.CIANO}MX{Cores.FIM}")
    print(f"  Prioridade: {Cores.CIANO}{prioridade}{Cores.FIM}")
    print(f"  Servidor: {Cores.CIANO}{servidor_mail}{Cores.FIM}")
    confirmar = input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower()
    
    if confirmar != 's':
        print(f"{Cores.AMARELO}⚠ Operação cancelada{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    ficheiro_zona = obter_ficheiro_zona(dominio)
    backup_ficheiro(ficheiro_zona)
    
    try:
        with open(ficheiro_zona, 'r') as f:
            conteudo = f.read()
        
        linha_registo = f"@\tIN\tMX\t{prioridade}\t{servidor_mail}\n"
        linhas = conteudo.split('\n')
        posicao = len(linhas)
        
        for i, linha in enumerate(linhas):
            if re.match(r'^[\s]*[;#]\s*Registos?\s+(MX|Mail|Final)', linha, re.IGNORECASE):
                posicao = i
                break
            if 'CNAME' in linha and posicao == len(linhas):
                posicao = i
        
        linhas.insert(posicao, linha_registo)
        
        with open(ficheiro_zona, 'w') as f:
            f.write('\n'.join(linhas))
        
        print(f"{Cores.VERDE}✓ Registo MX adicionado{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return
    
    atualizar_serial(ficheiro_zona)
    
    sucesso, _ = executar_comando(f"named-checkzone {dominio} {ficheiro_zona}", "A verificar zona")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro na zona!{Cores.FIM}")
        return
    
    reiniciar_bind()
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ REGISTO MX ADICIONADO!{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Teste: dig @{obter_ip_local()} {dominio} MX{Cores.FIM}")
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

# ==================== PONTO 5: ZONA REVERSE ====================

def ip_para_reverse(ip):
    """Converte IP para formato reverse"""
    octetos = ip.split('.')
    return '.'.join(reversed(octetos[:3])) + '.in-addr.arpa'

def ip_para_ptr(ip):
    """Obtém último octeto para PTR"""
    return ip.split('.')[-1]

def zona_reverse_existe(reverse_zone):
    """Verifica se zona reverse existe"""
    try:
        with open("/etc/named.conf", 'r') as f:
            return f'zone "{reverse_zone}"' in f.read()
    except:
        return False

def criar_zona_reverse():
    """Cria uma zona reverse DNS (Ponto 5)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}➕ CRIAR ZONA REVERSE (Ponto 5){Cores.FIM}\n")
    
    ip_default = obter_ip_local()
    ip = input(f"{Cores.BRANCO}Endereço IP [{ip_default}]: {Cores.FIM}").strip() or ip_default
    
    if not validar_ip(ip):
        print(f"{Cores.VERMELHO}✗ IP inválido!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    fqdn = input(f"{Cores.BRANCO}Nome FQDN (ex: ns1.empresa.local.): {Cores.FIM}").strip()
    if not fqdn:
        print(f"{Cores.VERMELHO}✗ FQDN não pode estar vazio!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    if not fqdn.endswith('.'):
        fqdn += '.'
    
    reverse_zone = ip_para_reverse(ip)
    ptr_value = ip_para_ptr(ip)
    network = '.'.join(ip.split('.')[:3])
    
    print(f"\n{Cores.AMARELO}⚠ Confirma a criação da zona reverse?{Cores.FIM}")
    print(f"  IP: {Cores.CIANO}{ip}{Cores.FIM}")
    print(f"  FQDN: {Cores.CIANO}{fqdn}{Cores.FIM}")
    print(f"  Zona: {Cores.CIANO}{reverse_zone}{Cores.FIM}")
    confirmar = input(f"\n{Cores.BRANCO}Confirmar (s/n): {Cores.FIM}").strip().lower()
    
    if confirmar != 's':
        print(f"{Cores.AMARELO}⚠ Operação cancelada{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A CRIAR ZONA REVERSE{Cores.FIM}")
    print("=" * 50)
    
    if zona_reverse_existe(reverse_zone):
        print(f"{Cores.AMARELO}⚠ Zona reverse já existe!{Cores.FIM}")
        adicionar = input(f"{Cores.BRANCO}Adicionar registo PTR? (s/n) [s]: {Cores.FIM}").strip().lower() or "s"
        if adicionar != 's':
            return
    
    arquivo_zona = f"/var/named/{reverse_zone}.zone"
    serial = datetime.now().strftime("%Y%m%d01")
    
    conteudo_zona = f"""; Zona Reverse DNS para rede {network}.0/24
; Gerado automaticamente - Ponto 5
; Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

$TTL 86400
@       IN      SOA     {fqdn}     admin.{fqdn.replace('.', '-')} (
                        {serial}    ; Serial
                        3600        ; Refresh
                        1800        ; Retry
                        604800      ; Expire
                        86400       ; Minimum TTL
)

; Servidores de Nomes
@       IN      NS      {fqdn}

; Registos PTR
{ptr_value}     IN      PTR     {fqdn}
"""
    
    try:
        with open(arquivo_zona, 'w') as f:
            f.write(conteudo_zona)
        print(f"{Cores.VERDE}✓ Ficheiro de zona reverse criado: {arquivo_zona}{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro: {e}{Cores.FIM}")
        return
    
    executar_comando(f"chown named:named {arquivo_zona}", "A definir permissões")
    executar_comando(f"chmod 640 {arquivo_zona}", "A definir permissões")
    
    configurar_named_conf(reverse_zone, arquivo_zona, reverse=True)
    
    if not verificar_configuracao_dns():
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    sucesso, _ = executar_comando(f"named-checkzone {reverse_zone} {arquivo_zona}", "A verificar zona reverse")
    if not sucesso:
        print(f"{Cores.VERMELHO}✗ Erro na zona reverse!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    if not reiniciar_bind():
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🧪 TESTE DE RESOLUÇÃO REVERSE{Cores.FIM}")
    print("-" * 50)
    sucesso, saida = executar_comando(f"dig @127.0.0.1 -x {ip} +short", "", ignorar_erro=True)
    if sucesso and fqdn in saida:
        print(f"{Cores.VERDE}✓ Reverse DNS funcionando!{Cores.FIM}")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}       ✓ ZONA REVERSE CRIADA COM SUCESSO!{Cores.FIM}")
    print(f"{Cores.VERDE}{Cores.NEGRITO}" + "="*70 + f"{Cores.FIM}")
    print(f"\n{Cores.BRANCO}Resumo:{Cores.FIM}")
    print(f"  • IP: {Cores.CIANO}{ip}{Cores.FIM}")
    print(f"  • FQDN: {Cores.CIANO}{fqdn}{Cores.FIM}")
    print(f"  • Zona: {Cores.CIANO}{reverse_zone}{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

# ==================== PONTO 6: ELIMINAR ====================

def eliminar_zona_forward():
    """Elimina uma zona forward DNS (Ponto 6)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🗑️ ELIMINAR ZONA FORWARD (Ponto 6){Cores.FIM}\n")
    
    zonas = listar_zonas_forward()
    if not zonas:
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print()
    dominio = input(f"{Cores.BRANCO}Nome da zona a eliminar (ou 'cancelar' para sair): {Cores.FIM}").strip().lower()
    
    # Opção para cancelar
    if dominio == 'cancelar':
        print(f"{Cores.AMARELO}⚠ Operação cancelada pelo utilizador.{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    if dominio not in zonas:
        print(f"{Cores.VERMELHO}✗ Zona não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}⚠ ATENÇÃO! Vai eliminar a zona '{dominio}' e todos os seus registos DNS.{Cores.FIM}")
    print(f"{Cores.AMARELO}Esta ação não pode ser desfeita!{Cores.FIM}")
    print()
    print(f"{Cores.BRANCO}Opções:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Confirmar eliminação")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Cancelar")
    print()
    
    opcao = input(f"{Cores.BRANCO}Escolha (1-2) [2]: {Cores.FIM}").strip() or "2"
    
    if opcao != "1":
        print(f"{Cores.AMARELO}⚠ Operação cancelada.{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A ELIMINAR ZONA{Cores.FIM}")
    print("=" * 50)
    
    backup_ficheiro("/etc/named.conf")
    
    # Obter ficheiro da zona
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        
        padrao = rf'zone\s+"{re.escape(dominio)}"\s+IN\s*\{{[^}}]*file\s+"([^"]+)"'
        match = re.search(padrao, conteudo, re.DOTALL)
        
        if match:
            ficheiro_zona = match.group(1)
            # Backup e eliminar ficheiro de zona
            if os.path.exists(ficheiro_zona):
                backup_ficheiro(ficheiro_zona)
                os.remove(ficheiro_zona)
                print(f"{Cores.VERDE}✓ Ficheiro de zona eliminado: {ficheiro_zona}{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.AMARELO}⚠ Não foi possível eliminar ficheiro de zona: {e}{Cores.FIM}")
    
    # Remover do named.conf
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        
        # Padrão para encontrar e remover a zona completa
        padrao = rf'\n?zone\s+"{re.escape(dominio)}"\s+IN\s*\{{[^}}]*\}};\s*\n?'
        novo_conteudo = re.sub(padrao, '\n', conteudo, flags=re.DOTALL)
        
        # Limpar linhas em branco excessivas
        novo_conteudo = re.sub(r'\n{3,}', '\n\n', novo_conteudo)
        
        with open("/etc/named.conf", 'w') as f:
            f.write(novo_conteudo)
        
        print(f"{Cores.VERDE}✓ Zona removida do named.conf{Cores.FIM}")
        
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao atualizar named.conf: {e}{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    # Verificar configuração
    sucesso, _ = executar_comando("named-checkconf", "A verificar configuração")
    if sucesso:
        print(f"{Cores.VERDE}✓ Configuração válida{Cores.FIM}")
    
    # Reiniciar BIND
    executar_comando("systemctl restart named", "A reiniciar BIND")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ ZONA FORWARD ELIMINADA!{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

def eliminar_zona_reverse():
    """Elimina uma zona reverse DNS (Ponto 6)"""
    imprimir_cabecalho()
    print(f"{Cores.AZUL}{Cores.NEGRITO}🗑️ ELIMINAR ZONA REVERSE (Ponto 6){Cores.FIM}\n")
    
    zonas = listar_zonas_reverse()
    if not zonas:
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print()
    reverse_zone = input(f"{Cores.BRANCO}Nome da zona reverse a eliminar (ou 'cancelar' para sair): {Cores.FIM}").strip().lower()
    
    # Opção para cancelar
    if reverse_zone == 'cancelar':
        print(f"{Cores.AMARELO}⚠ Operação cancelada pelo utilizador.{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    zona_real = None
    for z in zonas:
        if z.lower() == reverse_zone:
            zona_real = z
            break
    
    if not zona_real:
        print(f"{Cores.VERMELHO}✗ Zona não encontrada!{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}⚠ ATENÇÃO! Vai eliminar a zona reverse '{zona_real}'.{Cores.FIM}")
    print(f"{Cores.AMARELO}Esta ação não pode ser desfeita!{Cores.FIM}")
    print()
    print(f"{Cores.BRANCO}Opções:{Cores.FIM}")
    print(f"  {Cores.CIANO}[1]{Cores.FIM} Confirmar eliminação")
    print(f"  {Cores.CIANO}[2]{Cores.FIM} Cancelar")
    print()
    
    opcao = input(f"{Cores.BRANCO}Escolha (1-2) [2]: {Cores.FIM}").strip() or "2"
    
    if opcao != "1":
        print(f"{Cores.AMARELO}⚠ Operação cancelada.{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    print(f"\n{Cores.AZUL}{Cores.NEGRITO}🚀 A ELIMINAR ZONA REVERSE{Cores.FIM}")
    print("=" * 50)
    
    backup_ficheiro("/etc/named.conf")
    
    # Obter ficheiro da zona
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        
        padrao = rf'zone\s+"{re.escape(zona_real)}"\s+IN\s*\{{[^}}]*file\s+"([^"]+)"'
        match = re.search(padrao, conteudo, re.DOTALL)
        
        if match:
            ficheiro_zona = match.group(1)
            if os.path.exists(ficheiro_zona):
                backup_ficheiro(ficheiro_zona)
                os.remove(ficheiro_zona)
                print(f"{Cores.VERDE}✓ Ficheiro de zona reverse eliminado: {ficheiro_zona}{Cores.FIM}")
    except Exception as e:
        print(f"{Cores.AMARELO}⚠ Não foi possível eliminar ficheiro de zona: {e}{Cores.FIM}")
    
    # Remover do named.conf
    try:
        with open("/etc/named.conf", 'r') as f:
            conteudo = f.read()
        
        padrao = rf'\n?zone\s+"{re.escape(zona_real)}"\s+IN\s*\{{[^}}]*\}};\s*\n?'
        novo_conteudo = re.sub(padrao, '\n', conteudo, flags=re.DOTALL)
        novo_conteudo = re.sub(r'\n{3,}', '\n\n', novo_conteudo)
        
        with open("/etc/named.conf", 'w') as f:
            f.write(novo_conteudo)
        
        print(f"{Cores.VERDE}✓ Zona reverse removida do named.conf{Cores.FIM}")
        
    except Exception as e:
        print(f"{Cores.VERMELHO}✗ Erro ao atualizar named.conf: {e}{Cores.FIM}")
        input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        return
    
    # Verificar configuração
    sucesso, _ = executar_comando("named-checkconf", "A verificar configuração")
    if sucesso:
        print(f"{Cores.VERDE}✓ Configuração válida{Cores.FIM}")
    
    # Reiniciar BIND
    executar_comando("systemctl restart named", "A reiniciar BIND")
    
    print(f"\n{Cores.VERDE}{Cores.NEGRITO}✓ ZONA REVERSE ELIMINADA!{Cores.FIM}")
    
    input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

# ==================== MENU PRINCIPAL ====================

def menu_principal():
    """Menu principal do script"""
    while True:
        imprimir_cabecalho()
        
        print(f"{Cores.BRANCO}=== PONTO 1: ZONAS MASTER ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[1]{Cores.FIM} Criar zona master DNS")
        print()
        print(f"{Cores.BRANCO}=== PONTO 4: REGISTOS DNS ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[2]{Cores.FIM} Adicionar registo A")
        print(f"  {Cores.VERDE}[3]{Cores.FIM} Adicionar registo MX")
        print()
        print(f"{Cores.BRANCO}=== PONTO 5: ZONAS REVERSE ==={Cores.FIM}")
        print(f"  {Cores.VERDE}[4]{Cores.FIM} Criar zona reverse")
        print()
        print(f"{Cores.BRANCO}=== PONTO 6: ELIMINAR ==={Cores.FIM}")
        print(f"  {Cores.VERMELHO}[5]{Cores.FIM} Eliminar zona forward")
        print(f"  {Cores.VERMELHO}[6]{Cores.FIM} Eliminar zona reverse")
        print()
        print(f"{Cores.BRANCO}=== LISTAR ==={Cores.FIM}")
        print(f"  {Cores.CIANO}[7]{Cores.FIM} Listar zonas forward")
        print(f"  {Cores.CIANO}[8]{Cores.FIM} Listar zonas reverse")
        print(f"  {Cores.AMARELO}[9]{Cores.FIM} Estado do serviço DNS")
        print()
        print(f"  {Cores.VERMELHO}[0]{Cores.FIM} Sair")
        print()
        
        opcao = input(f"{Cores.CIANO}Opção: {Cores.FIM}").strip()
        
        if opcao == "1":
            criar_zona_master()
        elif opcao == "2":
            adicionar_registo_a()
        elif opcao == "3":
            adicionar_registo_mx()
        elif opcao == "4":
            criar_zona_reverse()
        elif opcao == "5":
            eliminar_zona_forward()
        elif opcao == "6":
            eliminar_zona_reverse()
        elif opcao == "7":
            imprimir_cabecalho()
            listar_zonas_forward()
            input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        elif opcao == "8":
            imprimir_cabecalho()
            listar_zonas_reverse()
            input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        elif opcao == "9":
            imprimir_cabecalho()
            print(f"{Cores.AZUL}{Cores.NEGRITO}ℹ️ ESTADO DO SERVIÇO DNS{Cores.FIM}\n")
            executar_comando("systemctl status named --no-pager", "", ignorar_erro=True)
            input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")
        elif opcao == "0":
            print(f"\n{Cores.VERDE}✓ A sair...{Cores.FIM}")
            sys.exit(0)
        else:
            print(f"{Cores.VERMELHO}✗ Opção inválida!{Cores.FIM}")
            input(f"\n{Cores.AMARELO}Pressione ENTER para continuar...{Cores.FIM}")

def main():
    """Função principal"""
    verificar_root()
    menu_principal()

if __name__ == "__main__":
    main()
