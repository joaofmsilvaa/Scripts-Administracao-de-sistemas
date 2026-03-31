# README - Script DNS Completo

## 📋 Informação Geral

- **Script**: `script_dns_completo.py`
- **Pontos do Projeto**: 1, 4, 5 e 6
- **Serviço**: BIND DNS Server
- **Sistema**: Alma Linux 9

---

## 🎯 Funcionalidades

Este script consolida as funcionalidades DNS do projeto:

| Menu | Ponto | Funcionalidade |
|------|-------|----------------|
| 1 | **Ponto 1** | Criar zona master DNS (forward) |
| 2 | **Ponto 4** | Adicionar registo A |
| 3 | **Ponto 4** | Adicionar registo MX |
| 4 | **Ponto 5** | Criar zona reverse DNS |
| 5 | **Ponto 6** | Eliminar zona forward |
| 6 | **Ponto 6** | Eliminar zona reverse |
| 7 | - | Listar zonas forward |
| 8 | - | Listar zonas reverse |
| 9 | - | Estado do serviço DNS |

---

## 🚀 Como Executar

```bash
# Como root ou com sudo
sudo python3 script_dns_completo.py
```

---

## 🧪 Testes Passo a Passo

### Teste 1: Criar Zona Master (Ponto 1)

1. Execute o script e escolha opção **1**
2. Introduza o domínio: `empresa.local`
3. Confirme o IP (ou introduza manualmente)
4. Aguarde a instalação automática do BIND

**Verificação:**
```bash
# Verificar se o BIND está ativo
systemctl status named

# Testar resolução DNS
dig @127.0.0.1 empresa.local A

# Deve retornar o IP do servidor
```

**Ficheiros criados:**
- `/etc/named.conf` (configuração atualizada)
- `/var/named/empresa.local.zone` (ficheiro de zona)

---

### Teste 2: Adicionar Registo A (Ponto 4)

1. Escolha opção **2**
2. Selecione a zona: `empresa.local`
3. Nome do host: `www`
4. IP: `192.168.1.10`

**Verificação:**
```bash
# Testar o novo registo
dig @127.0.0.1 www.empresa.local A

# Deve retornar: 192.168.1.10
```

---

### Teste 3: Adicionar Registo MX (Ponto 4)

1. Escolha opção **3**
2. Selecione a zona: `empresa.local`
3. Prioridade: `10`
4. Servidor: `mail.empresa.local.`

**Verificação:**
```bash
# Testar registo MX
dig @127.0.0.1 empresa.local MX

# Deve retornar: 10 mail.empresa.local.
```

---

### Teste 4: Criar Zona Reverse (Ponto 5)

1. Escolha opção **4**
2. Introduza o IP: `192.168.1.10`
3. FQDN: `ns1.empresa.local.`

**Verificação:**
```bash
# Testar reverse DNS
dig @127.0.0.1 -x 192.168.1.10

# Deve retornar: ns1.empresa.local.
```

**Nota:** A zona reverse terá o formato `1.168.192.in-addr.arpa`

---

### Teste 5: Eliminar Zona (Ponto 6)

1. Escolha opção **5** (forward) ou **6** (reverse)
2. Introduza o nome da zona
3. Confirme a eliminação

**Verificação:**
```bash
# Verificar que a zona foi removida
cat /etc/named.conf | grep zona

# O ficheiro de zona também é removido de /var/named/
```

---

## 📁 Estrutura de Ficheiros

```
/etc/named.conf              # Configuração principal do BIND
/var/named/                  # Diretório das zonas
├── empresa.local.zone       # Zona forward
└── 1.168.192.in-addr.arpa.zone  # Zona reverse
```

---

## 🔧 Comandos Úteis

```bash
# Estado do serviço
systemctl status named

# Reiniciar BIND
systemctl restart named

# Verificar sintaxe
named-checkconf

# Verificar zona
named-checkzone empresa.local /var/named/empresa.local.zone

# Ver zonas carregadas
rndc status

# Logs
tail -f /var/log/messages | grep named
```

---

## ⚠️ Notas Importantes

1. **Backups automáticos**: Criados em `/var/named/*.backup.*` e `/etc/named.conf.backup`
2. **Firewall**: Configurado automaticamente (porta 53/tcp e 53/udp)
3. **SELinux**: Contextos configurados automaticamente
4. **Serial**: Atualizado automaticamente (formato: AAAAMMDD01)

---

## 🖥️ Teste no Cliente Windows

Configure o DNS no Windows:
1. Painel de Controlo → Rede → Propriedades do IPv4
2. DNS preferido: `IP_DO_SERVIDOR`
3. Teste: `nslookup empresa.local`

---

## 🐧 Teste no Cliente Linux

```bash
# Configurar resolv.conf
echo "nameserver IP_DO_SERVIDOR" | sudo tee /etc/resolv.conf

# Testar
dig empresa.local
nslookup empresa.local
```
