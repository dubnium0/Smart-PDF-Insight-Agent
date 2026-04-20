# RotAI: Akıllı Doküman Analisti (PDF & Raporlama)

Bu projeyi **RotAI: Otonom Agent Yarışması** kapsamında geliştirdim. Yarışmada bizden istenilenler. 
Agent'ın bir dokümanı okuyup, bir danışman gibi yorumlaması isenecektir. 

* Görev: Verilen bir PDF dosyasını okumak ve o dosya ile ilgili sorulan anlık soruları 
yanıtlamak.
* Beklenti: Agent, cevabı bir mail olarak atmalıdır. Ancak mail şu yapısal 
başlıklardan oluşmalıdır: 
   * Soru: (Sorulan soru) 
   * Cevap: (PDF'teki net bilgi) 
   * Agent Yorumu: (Agent'ın konuya dair içgörüsü) 
   * Öneri Aksiyonları: (Agent'ın bu bilgi ışığında önerdiği adımlar)

## Özellikler

- **PDF Analizi:** E-posta ile gelen PDF dokümanlarını parçalar ve vektör veritabanına kaydeder.
- **RAG Mimarisi:** Google Gemini modellerini kullanarak bağlam odaklı cevaplar üretir.
- **Otomatik Raporlama:** Analiz sonuçlarını ve işlem loglarını e-posta olarak ilgili birimlere iletir.
- **Kullanıcı Dostu Arayüz:** Streamlit tabanlı modern bir web arayüzü sunar.

**.env Dosyasını Oluşturun:**
   Proje ana dizininde `.env` adında bir dosya oluşturun ve aşağıdaki değişkenleri kendi bilgilerinizle doldurun.

   **Örnek `.env` içeriği:**
   ```ini
   # Google Gemini API Anahtarı
   GOOGLE_API_KEY=your_api_key
   # E-posta Gönderim Ayarları (SMTP)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=465
   SENDER_EMAIL=your_mail@gmail.com
   SENDER_PASSWORD=your_app_password
   ```


