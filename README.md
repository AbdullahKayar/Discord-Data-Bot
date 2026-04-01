# Discord Data Warehouse & OSINT Bot

## English

### Overview
A powerful, open-source Discord bot built with Python for real-time data analysis, message archival, and server intelligence. Features role-based access control and secure data export capabilities.

### Features
- **Real-Time Data Scraping**: Automatically collect and index Discord messages, user metadata, and server events
- **Shadow Logging**: Capture deleted and edited messages with timestamps for compliance and auditing
- **Role-Based Access Control (RBAC)**: Admin-only command execution with granular permission levels
- **Data Export**: Export analyzed data to CSV/Pandas DataFrames for external analysis

### Tech Stack
- Python 3.9+
- discord.py
- aiosqlite
- Pandas

### Setup

1. **Clone Repository**
    ```bash
    git clone https://github.com/yourusername/discord-warehouse-bot.git
    cd discord-warehouse-bot
    ```

2. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Configuration**
    ```bash
    cp .env.example .env
    # Edit .env with your Discord token and database path
    ```

4. **Run Bot**
    ```bash
    python bot.py
    ```

### ⚠️ SECURITY WARNING
**NEVER commit or share `.env` or `.db` files publicly.** These contain:
- Discord bot tokens (allows account compromise)
- Database with sensitive user data
- API credentials

Add to `.gitignore`:
```
.env
*.db
config.local
```

---

## Türkçe

### Genel Bakış
Python ile geliştirilmiş, gerçek zamanlı Discord veri analizi, mesaj arşivleme ve sunucu istihbaratı için güçlü, açık kaynak bot.

### Özellikler
- **Gerçek Zamanlı Veri Kazıması**: Discord mesajları, kullanıcı metaverisi ve sunucu olaylarını otomatik olarak toplayın
- **Gölge Günlükleme**: Silinen ve düzenlenen mesajları zaman damgası ile kaydedin
- **Rol Tabanlı Erişim Kontrolü (RBAC)**: Admin komutları için ayrıntılı izin seviyeleri
- **Veri Dışa Aktarma**: Analiz edilen verileri CSV/Pandas formatında dışa aktarın

### Teknoloji Yığını
- Python 3.9+
- discord.py
- aiosqlite
- Pandas

### Kurulum

1. **Depoyu Klonlayın**
    ```bash
    git clone https://github.com/yourusername/discord-warehouse-bot.git
    ```

2. **Bağımlılıkları Yükleyin**
    ```bash
    pip install -r requirements.txt
    ```

3. **Ortam Yapılandırması**
    ```bash
    cp .env.example .env
    # .env dosyasını Discord token ile düzenleyin
    ```

4. **Botu Çalıştırın**
    ```bash
    python bot.py
    ```

### ⚠️ GÜVENLİK UYARISI
**`.env` veya `.db` dosyalarını asla genel olarak paylaşmayın.** İçerirler:
- Discord bot tokenları (hesap güvenliğini tehlikeye atar)
- Hassas kullanıcı verilerini içeren veritabanı
- API kimlik bilgileri

`.gitignore` dosyasına ekleyin:
```
.env
*.db
config.local
```

---

**License**: MIT | **Contributions**: Welcome