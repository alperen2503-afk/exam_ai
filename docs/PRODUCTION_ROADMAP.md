# Exam AI üretim yol haritası

Bu belge mevcut yeteneklerle üretim için gerekli fakat henüz tamamlanmamış
katmanları birbirinden ayırır. OCR çıktısı hiçbir aşamada tek başına doğru kabul
edilmez; puanlama güven eşiği ve insan inceleme kuyruğuyla korunur.

## Tamamlanan ilk dikey dilim

- Görsel yükleme, tür/boyut kontrolü ve güvenli dosya adı
- Pix2Text ana motoru için entegrasyon noktası
- Satır tabanlı Tesseract fallback ve küçük görsel büyütme
- `÷` işaretini nokta–çizgi–nokta geometrisiyle geri kazanma
- Güvenli dört işlem ayrıştırma; Python `eval` kullanılmaz
- Tam kesir hesabıyla doğru, yanlış, boş ve inceleme-gerekli durumları
- Toplama, çıkarma, çarpma, bölme ve karışık işlem sınıflandırması
- Konu bazlı rapor ve yanlış/boş ağırlıklı çalışma planı
- Ham OCR, normalize ifade, güven ve uyarıların denetlenebilir kaydı

## Girdi ve belge senaryoları

1. PDF sayfaları görüntüye dönüştürülmeli; sayfa numarası her soruda korunmalı.
2. EXIF yönü, 90 derece dönüş, perspektif, gölge, bulanıklık, düşük kontrast,
   renkli kâğıt ve çift sayfa fotoğrafları ayrı kalite kontrollerinden geçmeli.
3. Çok sütun, tablo, soru numarası, şıklar, grafik, şekil ve matrisler bir layout
   modeliyle bölgelere ayrılmalı; yalnız yatay satır segmentasyonu yetmez.
4. Basılı soru ile el yazısı cevap farklı OCR modellerine yönlendirilmeli.
5. Dosya gerçekten görüntü mü sihirli baytlarla doğrulanmalı; zararlı veya aşırı
   büyük/decompression-bomb dosyaları reddedilmeli.
6. Öğrenci adı ve okul numarası kişisel veri olarak şifreleme, saklama süresi ve
   silme politikalarına tabi olmalı.

## Matematiksel doğrulama senaryoları

- Sayısal cevaplarda tam kesir, ondalık toleransı, yuvarlama basamağı ve birim
  politikası soru bazında tanımlanmalı.
- `1/2`, `0.5`, `%50` gibi eşdeğer biçimler aynı semantik değere çevrilmeli.
- Cebirde ifadelerin sembolik eşdeğerliği SymPy ile varsayımlar altında kontrol
  edilmeli; yalnız metin eşitliği kullanılmamalı.
- Denklemlerde çözüm kümesi, extraneous root, tanım kümesi ve çoklu kökler
  doğrulanmalı.
- Türev, integral, limit, matris, istatistik, olasılık, diferansiyel denklem ve
  optimizasyon her biri kendi doğrulayıcısına sahip olmalı.
- Geometri ve grafik soruları yalnız OCR ile puanlanmamalı; şekil anlayışı ve
  verilenlerin bağlanması gerekir.
- Çoktan seçmeli, çok cevaplı, doğru/yanlış, eşleştirme ve açık uçlu cevaplar
  ayrı cevap şemaları kullanmalı.
- Soru hatalı, birden fazla doğru cevaplı veya bilgi açısından eksik olabilir;
  sistem bunu öğrencinin yanlışı olarak yazmamalı.

## Güven ve insan incelemesi

- OCR karakter güveni, layout güveni, parser güveni ve solver güveni ayrı
  saklanmalı; tek bir ortalama önemli hataları gizlememeli.
- Düşük güvenli cevaplar otomatik puanlanmamalı.
- Öğretmen düzelttiğinde ham görüntü, eski tahmin, yeni değer ve kullanıcı
  kimliği audit loguna yazılmalı.
- Model güncellemeleri aynı anonimleştirilmiş golden set üzerinde ölçülmeden
  üretime çıkmamalı.

## Rapor ve çalışma programı

- Konu etiketi yanında sınıf düzeyi, müfredat kazanımı ve önkoşul beceriler
  tutulmalı.
- Program yalnız bir sınava değil zaman içindeki hata tekrarına, unutma eğrisine,
  öğrencinin günlük süresine ve yaklaşan sınava göre ayarlanmalı.
- Yanlış nedenleri `kavram`, `işlem`, `dikkat`, `okuma`, `zaman` ve `boş` olarak
  ayrılmalı; çalışma görevi nedene göre seçilmeli.
- Öğretmen ve öğrenci raporları farklı ayrıntı seviyelerinde olmalı.

## Üretim altyapısı

- OCR/model işleri API sürecinden iş kuyruğuna taşınmalı; timeout, retry ve
  idempotency anahtarı bulunmalı.
- Model ağırlıkları başlangıçta hazırlanmalı; ilk kullanıcı isteğinde indirme
  yapılmamalı.
- PostgreSQL, nesne depolama, şifre yönetimi, rate limit, kimlik doğrulama,
  yetkilendirme ve zararlı dosya taraması eklenmeli.
- Her motor için gecikme, hata, fallback, inceleme ve doğruluk metrikleri
  izlenmeli. Loglarda öğrenci görseli veya kişisel veri bulunmamalı.

## Kabul ölçütleri

- Her soru türü ve görüntü bozulması için sürümlenmiş bir test veri kümesi
- Karakter doğruluğu yanında soru ayrıştırma, cevap durumu, konu etiketi ve
  çözüm doğruluğu metrikleri
- Yanlış otomatik puanlama oranı için sıkı eşik; düşük güven durumunda abstain
- Yaş/sınıf, el yazısı biçimi ve cihaz türlerine göre hata dağılımı kontrolleri
- Geriye dönük uyumluluk ve yük testleri tamamlanmadan üretim yayını yapılmaması
