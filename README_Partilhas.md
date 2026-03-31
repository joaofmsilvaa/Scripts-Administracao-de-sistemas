# README - Script Partilhas (SAMBA e NFS)

## 📋 Informação Geral

- **Script**: `script_partilhas.py`
- **Pontos do Projeto**: 2 e 7
- **Serviços**: SAMBA (Windows) e NFS (Linux/Unix)
- **Sistema**: Alma Linux 9

---

## 🎯 Funcionalidades

### SAMBA (Ponto 2) - Partilhas Windows

| Menu | Funcionalidade |
|------|----------------|
| 1 | Criar partilha SAMBA |
| 2 | Eliminar partilha SAMBA |
| 3 | Desativar/Ativar partilha |
| 4 | Mapear partilha Windows (CIFS) |
| 5 | Listar partilhas SAMBA |

### NFS (Ponto 7) - Partilhas Linux/Unix

| Menu | Funcionalidade |
|------|----------------|
| 6 | Criar partilha NFS |
| 7 | Eliminar partilha NFS |
| 8 | Desativar/Ativar partilha |
| 9 | Testar partilha NFS (mount -t nfs) |
| 10 | Listar partilhas NFS |

---

## 🚀 Como Executar

```bash
# Como root ou com sudo
sudo python3 script_partilhas.py
```

---

## 🧪 Testes SAMBA (Ponto 2)

### Teste 1: Criar Partilha SAMBA

1. Execute o script e escolha opção **1**
2. Nome da partilha: `documentos`
3. Diretório: `/srv/samba/documentos`
4. Comentário: `Partilha de documentos`
5. Permissões: Leitura e escrita
6. Pública: Não

**Verificação no servidor:**
```bash
# Verificar configuração
testparm -s

# Listar partilhas
smbclient -L //localhost -U%

# Verificar serviço
systemctl status smb
systemctl status nmb
```

**Verificação no Windows 10:**
```
1. Abrir Explorador de ficheiros
2. Digitar na barra de endereços: \\IP_DO_SERVIDOR\documentos
3. Ou: Mapear unidade de rede → \\IP_DO_SERVIDOR\documentos
```

---

### Teste 2: Mapear Partilha Windows no Linux (smbmount/CIFS)

1. Escolha opção **4**
2. IP do servidor Windows: `192.168.1.50`
3. Nome da partilha: `partilha_windows`
4. Ponto de montagem: `/mnt/windows_share`
5. Usar credenciais: Sim (se necessário)

**Verificação:**
```bash
# Verificar montagem
df -h | grep cifs
mount | grep cifs

# Listar conteúdo
ls -la /mnt/windows_share
```

---

### Teste 3: Eliminar Partilha SAMBA

1. Escolha opção **2**
2. Introduza o nome da partilha
3. Confirme a eliminação

---

## 🧪 Testes NFS (Ponto 7)

### Teste 1: Criar Partilha NFS

1. Escolha opção **6**
2. Diretório: `/srv/nfs/dados`
3. Clientes: `*` (todos) ou `192.168.1.0/24` (rede específica)
4. Permissões: Leitura e escrita
5. Síncrono: sync
6. Permitir root: Não

**Verificação no servidor:**
```bash
# Verificar exports
exportfs -v

# Verificar serviço
systemctl status nfs-server
systemctl status rpcbind

# Verificar portas
ss -tlnp | grep -E 'nfs|rpc'
```

---

### Teste 2: Testar Montagem NFS (mount -t nfs)

1. Escolha opção **9**
2. Selecione a partilha a testar
3. Ponto de montagem: `/mnt/nfs_test`

**Verificação:**
```bash
# Verificar montagem
df -h | grep nfs
mount | grep nfs

# Testar escrita
touch /mnt/nfs_test/teste.txt
echo "Teste NFS" > /mnt/nfs_test/teste.txt
cat /mnt/nfs_test/teste.txt
rm /mnt/nfs_test/teste.txt
```

---

### Teste 3: Aceder a Partilha NFS num Cliente Linux

No cliente Linux (máquina separada):

```bash
# Instalar cliente NFS
sudo dnf install -y nfs-utils

# Verificar partilhas disponíveis
showmount -e IP_DO_SERVIDOR

# Criar ponto de montagem
sudo mkdir -p /mnt/nfs_cliente

# Montar partilha
sudo mount -t nfs IP_DO_SERVIDOR:/srv/nfs/dados /mnt/nfs_cliente

# Verificar
ls -la /mnt/nfs_cliente
df -h

# Desmontar
sudo umount /mnt/nfs_cliente
```

---

### Teste 4: Montagem Automática (fstab)

Para montar automaticamente no arranque:

```bash
# Editar fstab
sudo nano /etc/fstab

# Adicionar linha:
IP_DO_SERVIDOR:/srv/nfs/dados  /mnt/nfs_cliente  nfs  defaults,_netdev  0  0

# Testar
sudo mount -a
```

---

## 📁 Estrutura de Ficheiros

### SAMBA
```
/etc/samba/smb.conf          # Configuração SAMBA
/srv/samba/documentos/       # Diretório partilhado
```

### NFS
```
/etc/exports                 # Configuração NFS
/srv/nfs/dados/              # Diretório partilhado
```

---

## 🔧 Comandos Úteis

### SAMBA
```bash
# Estado dos serviços
systemctl status smb
systemctl status nmb

# Reiniciar
systemctl restart smb nmb

# Testar configuração
testparm

# Listar partilhas
smbclient -L //localhost -U%

# Aceder a partilha
smbclient //localhost/documentos -U usuario

# Logs
tail -f /var/log/samba/log.smbd
```

### NFS
```bash
# Estado dos serviços
systemctl status nfs-server
systemctl status rpcbind

# Reiniciar
systemctl restart nfs-server rpcbind

# Exportar partilhas
exportfs -ra

# Listar exports
exportfs -v
showmount -e localhost

# Estatísticas
nfsstat

# Logs
tail -f /var/log/messages | grep nfs
```

---

## ⚠️ Notas Importantes

### SAMBA
1. **Firewall**: Portas 139/tcp, 445/tcp, 137/udp, 138/udp
2. **SELinux**: Contexto `samba_share_t` configurado automaticamente
3. **Backups**: `/etc/samba/smb.conf.backup.*`

### NFS
1. **Firewall**: Serviços `nfs`, `rpc-bind`, `mountd`
2. **Versões**: NFSv3 e NFSv4 suportados
3. **Permissões**: Verificar permissões no diretório partilhado
4. **Backups**: `/etc/exports.backup.*`

---

## 🔥 Firewall

O script configura automaticamente o firewalld:

```bash
# Verificar regras
firewall-cmd --list-services
firewall-cmd --list-ports

# SAMBA
firewall-cmd --permanent --add-service=samba
firewall-cmd --permanent --add-service=samba-client

# NFS
firewall-cmd --permanent --add-service=nfs
firewall-cmd --permanent --add-service=rpc-bind
firewall-cmd --permanent --add-service=mountd
```
