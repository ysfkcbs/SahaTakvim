# Yeni Mac mini'ye Taşıma Rehberi

Bu dosya, `merkezsaha.com`'u yayınlayan Mac mini'nin değişmesi durumunda uygulamaların (SahaTakvim
+ merkezsaha/turnuva) yeni makinede eksiksiz ayağa kaldırılması için hazırlandı. İki proje aynı
domaini paylaşıyor ama tamamen ayrı, birbirinden bağımsız Docker Compose stack'i olarak çalışıyor.

## 1. Genel Mimari (şu anki canlı durum)

```
İnternet → Router (80/443 port yönlendirme) → Mac mini
                                                  │
                                        SahaTakvim/nginx (Docker, 80+443)
                                        ├── /            → SahaTakvim web (Docker, internal)
                                        └── /turnuva/    → host.docker.internal:5001
                                                              → merkezsaha web (Docker, 127.0.0.1:5001)
```

- **SahaTakvim** (`~/Desktop/Projeler/SahaTakvim`, repo: `ysfkcbs/SahaTakvim`)
  - Domain kökünü (`merkezsaha.com/`) sahipleniyor, nginx+certbot da bu repo'nun altında.
  - PostgreSQL: **native kurulum** (Homebrew, `postgres:18`), veritabanı adı `SahaTakvim`. Docker'a alınmadı.
  - CI/CD: self-hosted GitHub Actions runner bu makinede kurulu, `push` → otomatik deploy.
- **merkezsaha / turnuva** (`~/Desktop/Projeler/merkezsaha`, repo: `ysfkcbs/merkezsaha` — eski adı `turnuva`)
  - `merkezsaha.com/turnuva/` alt yolunda yayında, SahaTakvim'in nginx'i üzerinden proxy ediliyor.
  - PostgreSQL: **kendi Docker container'ı** (`postgres:16`, container adı `turnuva-db`, volume adı `turnuva_pgdata`), veritabanı adı `turnuva_db`, sadece `127.0.0.1:5433`'e bağlı.
  - CI/CD yok — deploy elle `docker compose up -d --build` ile yapılıyor.

## 2. Eski Makineden Alınacaklar (elle taşınmalı — hiçbiri git'te değil)

| Dosya/Klasör | Neden git'te değil |
|---|---|
| `SahaTakvim/.env` | Secret'lar (SECRET_KEY, DB şifresi, admin şifresi) |
| `merkezsaha/.env` | Aynı sebep (SECRET_KEY, DB_PASSWORD, ADMIN_PASSWORD) |
| `SahaTakvim/backups/*.dump` | Native Postgres yedeği (pg_dump) |
| `merkezsaha/backups/*.dump` | Docker Postgres yedeği (pg_dump) |

Taşımadan hemen önce **taze bir yedek al**:
```bash
cd ~/Desktop/Projeler/SahaTakvim && ./scripts/backup_postgres.sh
cd ~/Desktop/Projeler/merkezsaha && \
  PGPASSWORD="$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" \
  pg_dump -h 127.0.0.1 -p 5433 -U postgres -d turnuva_db -F c \
  -f "backups/merkezsaha_$(date +%Y-%m-%d_%H%M%S).dump"
```
Yukarıdaki 4 satırı (`.env` × 2, `backups/` × 2) AirDrop/USB ile yeni makineye kopyala.

## 3. Yeni Makinede Kurulum Sırası

### 3.1 Temel araçlar
```bash
# Homebrew zaten yoksa: https://brew.sh
brew install gh
gh auth login
gh auth refresh -h github.com -s workflow   # deploy.yml push'u için gerekli
```
Docker Desktop'ı App Store/resmi siteden kur, aç, en az bir kez GUI'den giriş yap.

### 3.2 PostgreSQL (native, sadece SahaTakvim için)
PostgreSQL 18'i (EDB installer ya da `brew install postgresql@18`) kur. Kurulum sırasında
belirlediğin superuser şifresini not al — `SahaTakvim/.env`'deki `DATABASE_URL`'e bu şifre girecek.

```bash
createdb -U postgres SahaTakvim   # boş veritabanını oluştur
pg_restore -U postgres -h localhost -d SahaTakvim /path/to/sahatakvim_YYYY-MM-DD.dump
```

### 3.3 Repoları klonla
```bash
mkdir -p ~/Desktop/Projeler && cd ~/Desktop/Projeler
git clone https://github.com/ysfkcbs/SahaTakvim.git
git clone https://github.com/ysfkcbs/merkezsaha.git
```
Eski makineden getirdiğin `.env` dosyalarını ilgili klasörlere kopyala. `SahaTakvim/.env`'deki
`DATABASE_URL`'in yeni Postgres şifresiyle eşleştiğinden emin ol.

### 3.4 SahaTakvim'i ayağa kaldır
```bash
cd ~/Desktop/Projeler/SahaTakvim
docker compose up -d web   # nginx'i henüz başlatma — sertifika yok, bootstrap gerek
```
`app.py`'nin migration+seed adımları otomatik çalışır (`docker-compose.yml` command'ı içinde).

### 3.5 merkezsaha'yı ayağa kaldır
```bash
cd ~/Desktop/Projeler/merkezsaha
docker compose up -d db
# db healthy olunca (docker compose ps ile kontrol et):
PGPASSWORD="$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" \
  pg_restore -h 127.0.0.1 -p 5433 -U postgres -d turnuva_db --clean --if-exists \
  /path/to/merkezsaha_YYYY-MM-DD.dump
docker compose up -d --build web
```

### 3.6 SSL sertifikası
Eski makinedeki sertifika Docker volume içinde (`certbot-etc`), taşınmadı — router/DNS yeni
makineye yönlendiği anda **yeniden** alınacak (Let's Encrypt haftada 5 tekrar denemeye izin veriyor,
sorun olmaz):
```bash
cd ~/Desktop/Projeler/SahaTakvim
./scripts/init_letsencrypt.sh
```
Bu script'in nasıl çalıştığı ve neden iki aşamalı (bootstrap → sertifika → tam config) olduğu
`scripts/init_letsencrypt.sh` içinde yorumlanmış durumda.

### 3.7 Self-hosted GitHub Actions runner (sadece SahaTakvim için)
**Önce eski makinedeki runner'ı kaldır:** GitHub → `ysfkcbs/SahaTakvim` → Settings → Actions →
Runners → eski runner'ın yanındaki "Remove" (yoksa offline bir runner GitHub'da asılı kalır).

Sonra yeni makinede:
```bash
cd ~/Desktop/Projeler/SahaTakvim
./scripts/setup_github_runner.sh ysfkcbs/SahaTakvim
```
Bu script hem runner'ı kaydedip servis olarak kurar, hem de Docker Desktop'ın keychain sorununu
(`DOCKER_CONFIG` + no-op credential helper) otomatik çözer — bkz. script içindeki yorum.

### 3.8 Tailscale (kişisel uzaktan erişim)
```bash
brew install tailscale
brew services start tailscale
sudo tailscale up
```
Açılan URL'de kendi hesabınla onayla. Sonra System Settings → General → Sharing → Remote Login'i aç.

### 3.9 Yedekleme görevini kur
```bash
cd ~/Desktop/Projeler/SahaTakvim
./scripts/install_backup_schedule.sh
```
(merkezsaha'nın kendi otomatik yedekleme görevi henüz yok — istenirse `backup_postgres.sh`'ın
merkezsaha versiyonu ayrıca yazılabilir.)

### 3.10 Router
- Yeni Mac mini'nin MAC adresini bul (`ifconfig en0` / aktif arayüz), router panelinde **DHCP Address
  Reservation** ile sabit bir LAN IP ata.
- **Virtual Server / Port Forwarding**: dış 80 → yeni LAN IP:80 (TCP), dış 443 → yeni LAN IP:443 (TCP).
- Router'ın **kendi yönetim arayüzü** 80/443 kullanıyorsa (TP-Link'te "Yerel Yönetim") başka bir
  porta taşı — yoksa çakışır.
- **Güvenlik Duvarı Seviyesi** "Yüksek" ise "Düşük"e çek — eski kurulumda bu, port yönlendirmeyi
  sessizce engelliyordu.

### 3.11 DNS (sadece public IP değiştiyse)
Yeni makine farklı bir ağdan/ISP'den bağlanıyorsa public IP değişir. `curl -4 ifconfig.me` ile yeni
IP'yi öğren, domain sağlayıcısında `merkezsaha.com` için `@` A kaydını güncelle.

## 4. Doğrulama

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/health          # SahaTakvim, beklenen: 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5001/           # merkezsaha, beklenen: 200
```
Dışarıdan bağımsız doğrulama için (bu makineden değil — NAT hairpin nedeniyle güvenilmez):
```bash
curl -s "https://check-host.net/check-http?host=https://merkezsaha.com/health&max_nodes=3" \
  -H "Accept: application/json"
# birkaç saniye sonra dönen request_id ile:
curl -s "https://check-host.net/check-result/<request_id>" -H "Accept: application/json"
```

## 5. Bilinen Sorun Kayıtları (tekrar ederse hızlı tanı için)

Bu üç sorun ilk kurulumda sırayla çıkmıştı, hepsi çözüldü ama yeni makinede router değişmeden
kalıyorsa muhtemelen tekrar etmeyecekler — değişirse (yeni router vb.) aynı sırayla kontrol et:
1. **CGNAT**: router'ın WAN IP'si özel bir aralıktaysa (10.x, 100.64-127.x) ISP'den gerçek public IP iste.
2. **Router'ın kendi admin paneli 80/443 kullanıyor**: Yerel Yönetim portunu değiştir.
3. **Router güvenlik duvarı "Yüksek" seviye**: sessizce inbound trafiği engelliyor, düşür.

Detaylı geçmiş: bu repodaki commit geçmişi (`Add NGINX+Certbot+CI/CD infrastructure...` sonrası) ve
proje hafızasında (`~/.claude/projects/.../memory/project_deployment_status.md`).
