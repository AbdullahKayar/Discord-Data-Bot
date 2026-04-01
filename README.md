📊 Discord Data Warehouse & Analytics Bot

🇹🇷 Türkçe Özet

Bu proje, Discord sunucuları için geliştirilmiş gelişmiş bir Veri Ambarı ve OSINT botudur. Sunucudaki tüm mesaj trafiğini SQLite veritabanına işler, silinen/düzenlenen mesajları "Gölge Kayıt" olarak saklar ve yöneticilere CSV dökümü alma imkanı sunar.

🌟 Öne Çıkanlar

Veri Madenciliği: Tüm geçmiş mesajları ve medyaları otomatik olarak arşive çeker.

Gölge Kayıt: Silinen mesajlar asla kaybolmaz, veritabanında saklanır.

Otonom Raporlama: Her hafta sunucu aktiflik özetini otomatik olarak raporlar.

RBAC Güvenliği: Rol bazlı yetkilendirme ile güvenli veri erişimi sağlar.

🇬🇧 English Overview

An advanced Data Warehouse and OSINT bot designed for Discord servers. It logs all message traffic into a local SQLite database, maintains shadow records of deleted/edited messages, and allows administrators to export data as CSV files for analysis.

🌟 Key Features

Data Scraping: Automatically archives message history and media attachments.

Shadow Logging: Deleted messages are never lost; they are stored securely in the DB.

Autonomous Reporting: Sends weekly server activity summaries automatically.

RBAC Security: Ensures secure data access with role-based permissions.

🛠️ Installation / Kurulum

Clone the repo: git clone https://github.com/AbdullahKayar/Discord-Data-Bot.git

Install deps: pip install -r requirements.txt

Setup environment: Create a .env file using the .env.example template.

Configure IDs: Open main.py and enter your Discord Channel IDs.

Run: python main.py

📫 Connect with me / Bana Ulaşın

Proje hakkında sorularınız varsa veya iş birliği yapmak isterseniz bana aşağıdaki kanallardan ulaşabilirsiniz:

LinkedIn: linkedin.com/in/AbdullahKayar

GitHub: github.com/AbdullahKayar

Email: abdullahkayar5231@gmail.com

🛡️ Security & Privacy

This bot keeps all data locally in server_archive.db. Never share your database file or .env token publicly on GitHub.