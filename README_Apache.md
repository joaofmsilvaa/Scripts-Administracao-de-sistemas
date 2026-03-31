# README - Script Apache VirtualHost

## 📋 Informação Geral

- **Script**: `script_apache.py`
- **Ponto do Projeto**: 3
- **Serviço**: Apache HTTPD
- **Sistema**: Alma Linux 9

---

## 🎯 Funcionalidades

| Menu | Funcionalidade |
|------|----------------|
| 1 | Criar VirtualHost com página de boas-vindas |
| 2 | Eliminar VirtualHost |
| 3 | Listar VirtualHosts |
| 4 | Estado do serviço Apache |

---

## 🚀 Como Executar

```bash
# Como root ou com sudo
sudo python3 script_apache.py
```

---

## 🧪 Testes Passo a Passo

### Teste 1: Criar VirtualHost (Ponto 3)

1. Execute o script e escolha opção **1**
2. Introduza o domínio: `empresa.local`
3. Confirme o IP (ou introduza manualmente)
4. Email do administrador: `admin` (ou outro)
5. Aguarde a instalação automática do Apache

**O que o script faz:**
- Instala o Apache HTTPD (se não estiver instalado)
- Cria o diretório `/var/www/empresa.local/`
- Gera página de boas-vindas HTML personalizada
- Cria configuração em `/etc/httpd/conf.d/empresa.local.conf`
- Configura firewall (portas 80 e 443)
- Configura SELinux
- Reinicia o Apache

**Verificação no servidor:**
```bash
# Verificar se o Apache está ativo
systemctl status httpd

# Verificar configuração
httpd -t

# Testar localmente
curl -H "Host: empresa.local" http://localhost/

# Deve retornar o HTML da página de boas-vindas
```

---

### Teste 2: Aceder pelo Browser

**No Windows 10 (cliente):**

1. Configure o ficheiro `hosts` (como administrador):
   ```
   C:\Windows\System32\drivers\etc\hosts
   ```

2. Adicione a linha:
   ```
   IP_DO_SERVIDOR  empresa.local
   IP_DO_SERVIDOR  www.empresa.local
   ```

3. Abra o browser e aceda a:
   ```
   http://empresa.local/
   ```

4. Deve aparecer a página de boas-vindas com:
   - Título: "Bem-vindo a empresa.local"
   - Informações do domínio
   - IP do servidor
   - Data de criação
   - Indicador "VirtualHost Ativo"

**Alternativa (sem configurar hosts):**
```
http://IP_DO_SERVIDOR/
```

---

### Teste 3: Verificar Ficheiros Criados

```bash
# Configuração do VirtualHost
cat /etc/httpd/conf.d/empresa.local.conf

# Página de boas-vindas
cat /var/www/empresa.local/index.html

# Logs específicos do VirtualHost
tail -f /var/log/httpd/empresa.local-access.log
tail -f /var/log/httpd/empresa.local-error.log
```

---

### Teste 4: Eliminar VirtualHost

1. Escolha opção **2**
2. Introduza o nome do VirtualHost: `empresa.local`
3. Escolha se quer eliminar o diretório do site
4. Confirme a eliminação

**Verificação:**
```bash
# Verificar que foi eliminado
ls /etc/httpd/conf.d/ | grep empresa
ls /var/www/ | grep empresa
```

---

### Teste 5: Listar VirtualHosts

1. Escolha opção **3**
2. Veja a lista de VirtualHosts configurados

---

## 📁 Estrutura de Ficheiros

```
/etc/httpd/
├── conf/
│   └── httpd.conf           # Configuração principal
├── conf.d/
│   ├── empresa.local.conf   # VirtualHost criado
│   └── ...
└── conf.modules.d/          # Módulos

/var/www/
└── empresa.local/           # DocumentRoot
    └── index.html           # Página de boas-vindas

/var/log/httpd/
├── empresa.local-access.log # Logs de acesso
└── empresa.local-error.log  # Logs de erro
```

---

## 🔧 Comandos Úteis

```bash
# Estado do serviço
systemctl status httpd

# Iniciar/Parar/Reiniciar
systemctl start httpd
systemctl stop httpd
systemctl restart httpd

# Ativar no arranque
systemctl enable httpd

# Verificar sintaxe da configuração
httpd -t

# Versão do Apache
httpd -v

# Módulos carregados
httpd -M

# Portas em escuta
ss -tlnp | grep httpd
netstat -tlnp | grep httpd

# Logs gerais
tail -f /var/log/httpd/access_log
tail -f /var/log/httpd/error_log

# Logs de um VirtualHost específico
tail -f /var/log/httpd/empresa.local-access.log
```

---

## ⚠️ Notas Importantes

1. **Firewall**: O script configura automaticamente:
   - `http` (porta 80/tcp)
   - `https` (porta 443/tcp)

2. **SELinux**: Configurado automaticamente:
   - Contexto `httpd_sys_content_t` no DocumentRoot
   - Boolean `httpd_enable_homedirs` ativado

3. **Backups**: Criados automaticamente antes de alterações

4. **Permissões**: 
   - Proprietário: `apache:apache`
   - Permissões: `755` para diretórios

---

## 🔥 Firewall

```bash
# Verificar serviços no firewall
firewall-cmd --list-services

# Deve mostrar: http https

# Adicionar manualmente (se necessário)
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

---

## 🌐 Configuração de Exemplo

O VirtualHost criado terá esta estrutura:

```apache
<VirtualHost *:80>
    ServerName empresa.local
    ServerAlias www.empresa.local
    ServerAdmin admin@empresa.local
    DocumentRoot /var/www/empresa.local
    
    <Directory /var/www/empresa.local>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog /var/log/httpd/empresa.local-error.log
    CustomLog /var/log/httpd/empresa.local-access.log combined
</VirtualHost>
```

---

## 🎨 Personalização da Página

A página de boas-vindas é gerada automaticamente em HTML/CSS. Para editar:

```bash
# Editar a página
sudo nano /var/www/empresa.local/index.html

# Recarregar (não é necessário reiniciar o Apache)
```

---

## 🐛 Resolução de Problemas

### Apache não inicia
```bash
# Verificar erros de sintaxe
httpd -t

# Ver logs
journalctl -u httpd -xe
tail /var/log/httpd/error_log
```

### Página não aparece
```bash
# Verificar se o VirtualHost está carregado
httpd -S

# Verificar permissões
ls -la /var/www/empresa.local/
ls -Z /var/www/empresa.local/

# Restaurar contexto SELinux
restorecon -Rv /var/www/empresa.local/
```

### Acesso negado
```bash
# Verificar firewall
firewall-cmd --list-all

# Verificar SELinux
getenforce
setenforce 0  # Testar (temporário)
```

---

## 📱 Teste com curl

```bash
# Teste básico
curl http://empresa.local/

# Com header específico
curl -H "Host: empresa.local" http://localhost/

# Ver cabeçalhos
curl -I http://empresa.local/

# Seguir redirecionamentos
curl -L http://empresa.local/
```
