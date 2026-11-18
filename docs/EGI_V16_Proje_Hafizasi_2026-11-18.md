# EGI — YouTube Shorts Üretim ve Yayın Sistemi · Güncel Proje Hafızası

**Tarih:** 18 Kasım 2026 · Europe/Istanbul  
**Ana kaynak:** `hammersnow/youtube-auto-render`  
**Kanal:** **EGI** · *Curiosity in Motion* · üretici: **Ekrem Gökberk İşcan**  
**İçerik dili:** İngilizce · **Üretim maliyeti hedefi:** ücretsiz (Python/Pillow/NumPy/FFmpeg/GitHub Actions)  
**Belge statüsü:** V6.1 / V7 / V8 planlarının yerini alan **güncel karar ve devir belgesi**. Operasyonel gerçek durum için `main`, GitHub Actions ve yayımlanmış manifest esas alınır; bu belge bunların yerine geçmez.

## 1. Kesinleşen marka ve strateji

- Kanal yeni baştan açılmadı, var olan ve aboneleri bulunan kanalın adı **EGI** olarak değiştirildi.
- EGI, sadece mekanik değil; **yazılım, teknoloji, mühendislik ve bilim** anlatımları yayınlayacak. İçerik kategoriye göre farklı renk/ikon dili kullanabilir, marka bütünlüğü korunur.
- Kanal açıklaması: **EGI — Curiosity in Motion.** / Technology · Engineering · Science. Kişisel imza videolarda **Ekrem Gökberk İşcan**.
- Eski puzzle / optical / visual teaser / V7 içerikleri üretim yönü olarak **emekli**. Daha önce YouTube'a yüklenmiş videolar **silinmeyecek**.
- Yeni üretim: **kalite > adet**; günlük en fazla **2 farklı ve özgün Shorts**. Yeni onaylı bölüm yoksa video **üretilmez/yüklenmez**. Bölüm ve SHA/idempotency doğrulaması zorunlu.
- Kullanıcı 18 Kasım 2026'da mevcut YouTube üretim/yayın zincirine geçiş ve eski sistemi kapatma **açık onayını verdi**. Onay, yeni videoların teknik ve görsel QA'sının atlanması anlamına gelmez.

## 2. Onaylı EGI V16 animasyon standardı — geri dönülmez kreatif kararlar

**Kullanıcının özellikle istediği:** Daha hızlı ve düşük kaliteli üretim değil; üretim/render daha uzun sürebilir, ancak **çok daha fazla açıklayıcı animasyon**, hareketli öğe ve mikro-işlem olmalıdır. Video süresini gereksiz uzatmak ya da sayfa sayfa slaytlar göstermek **yanlış**. Akış birbiriyle bağlantılı ve izleyici açısından izlenebilir olmalıdır.

1. Tek olay zinciri: girdi → ara işlemler → çıktı. Kamera geçişi veya yakın plan önceki işlemi koparmaz; süreklilik önemlidir.
2. Görsel detayları azaltma: yazılım videosunda örneğin `HTML`, `CSS`, `JavaScript` ayrı renkli dosyalar halinde sunucudan tarayıcıya taşınmalı; yapı/stil/etkileşim oluşturmaları görselleştirilmeli. Yalnızca `RESOURCES` yazısına indirgenmemeli.
3. Nedensellik: tuş sesi URL yazma zamanına; DNS/TCP/TLS paketleri ağ akışına; kilit açılma hareketi ve `SECURE` ifadesi güvenlik anlaşmasına; batarya animasyonu akım dönüşümüne eşleşir.
4. Ekranda beliren küçük açıklama + ikonlar kullanılabilir. **Aynı olay için tek geçici açıklama (`callout`)** bulunabilir. Yazı kısa süre belirir, parçacıklara dağılıp yok olabilir; ancak kilit/işlenmiş kaynak/batarya durumu gibi **kalıcı sonuç** görünür kalabilir.
5. Önceki V12/V13/V14 katmanlarını aynı görüntü üstüne yığmak yasak: bu çift balon, çakışma ve amatör görünüm oluşturdu. Tekleştirilmiş olay zamanlayıcısı ve orijinal render kaynağı esas alınmalı.
6. Önceki onaylı mekanik tasarımlar: **Motor V8.8** (silindir içine büyük mavi balon/dolgu yok), **Turbo V8.9**, **Intercooler V9.1** (kart taşması giderildi). Bunlar silinmeyecek; gerektiğinde yeni standartta tekrar kullanılabilir.
7. Tema: yazılım koyu mavi/neon mavi-yeşil; teknoloji cyan/amber, enerji akışları; mekanik metalik gümüş/bakır, kesit ve gerçek mekanik bağlantılar. Aşırı overlay, kesik parçacık ve fiziksel olarak yanlış hareketten kaçın.
8. Metin ölçümü zorunlu: hiçbir karttan taşma, yığılma veya bir bilgi nesnesinin üstünü kapatma olmayacak. Mobil güvenli alan ve önemli olaylar birlikte denetlenmeli.
9. Teknik kalite: 9:16 **1080×1920**, H.264/AAC. V16 prototiplerinde **30 FPS**; eski onaylı motor/turbo/intercooler pilotları **24 FPS**. İngilizce anlatım, küçük gerçekçi ses efektleri, kişisel filigran, 2.5D/schematics dürüstçe belirtilmeli.
10. Üçüncü taraf referans videoları (*How URLs work.mp4* ve *What Happens When You Request a URL – DNS, TCP, TLS & HTTP Explained.mp4*) yalnızca tema/hareket analizi içindir. Görselleri veya sesleri kopyalamadan **özgün prosedürel tasarım** yapılmalıdır.

## 3. Kaynaklar ve GitHub durumu

| Kaynak | Amaç | Gerçek durum |
|---|---|---|
| GitHub repo: `hammersnow/youtube-auto-render` | Tek üretim/yayın deposu | Etkin |
| [PR #25](https://github.com/hammersnow/youtube-auto-render/pull/25) | V8 ilk geçiş araştırması / Blender CPU denemesi | Tarihsel taslak, yeni sistem için ana referans değil |
| [PR #26](https://github.com/hammersnow/youtube-auto-render/pull/26) | EGI V16 prosedürel render kaynakları, yerel QA, GitHub preview | **18 Kasım'da main'e merge edildi** (commit `ba488bf83159f444a5e4a6b5db1b95f862df40f3`); önizleme CI yeşil |
| [PR #27](https://github.com/hammersnow/youtube-auto-render/pull/27) | V7'yi durdurup EGI üretim/yayın sistemi kurma | **18 Kasım’da main’e merge edildi** (commit `2fac1cdb4610285a3df79a02a11e1adaff87181b`). EGI günlük cron ve EGI-only publisher kodu artık main’de; ilk gerçek YouTube çalışması ayrıca doğrulanmalıdır. |
| [EGI preview Actions](https://github.com/hammersnow/youtube-auto-render/actions/runs/44371799779) | V16 önceki bağımsız medya/QA testi | **Başarılı** |
| [EGI cutover QA](https://github.com/hammersnow/youtube-auto-render/actions/runs/44381098855) | EGI iki gün/4 bölüm yayın yapmayan uçtan uca render testi | **Başarılı (yeşil)**. İki katalog günü ve dört kaynak MP4, ses/codec/ölçü kontrollerinden geçti; bu gerçek upload değil, izole QA. |

**Yeni dosyalar** (PR #27'de önerilenler):

- `config/egi_episode_catalog.json` — EGI benzersiz bölüm takvimi; günlük maks. 2.
- `scripts/render_egi_daily.py` — bölüm seçimi + render + ffprobe ve SHA-256 kalite/manifest üretimi.
- `scripts/publish_egi_from_manifest.py` — EGI manifest ve SHA doğrulaması, UTC yayın planı, bölüm işaretleri.
- `scripts/youtube_upload.py` — `EXPECTED_YOUTUBE_CHANNEL_ID=UCNNyhE1DlhTXIip_p96kczA` ayarlıysa yükleme öncesi hedef kanalı doğrular; uyuşmazlıkta upload durur. EGI videoları YouTube **Science & Technology (kategori 28)** olarak etiketlenir.
- `.github/workflows/egi-daily.yml` — günlük EGI üretim; ayrı `egi-daily-latest` release; kontrol sonrası publisher dispatch.
- `.github/workflows/publish-youtube.yml` — sadece EGI içeriğine izin veren yayın workflow'u (PR #27 değişikliği).
- `.github/workflows/render-daily.yml` — V7 cron'unu kaldıran **retired** stub (PR #27 değişikliği).
- `.github/workflows/egi-production-cutover-qa.yml` — publish yetkisi/secreti olmayan kesit/medya QA.
- `egi_preview/egi_v16_rich_resources.py`, V12 çekirdekleri, V13 ikon yardımcıları ve V16 QA.
- `egi_preview/egi_turbo.py`, `egi_preview/egi_intercooler.py` — önceki onaylı mekanik renderer'ların GitHub'a taşınan kaynakları.

**Önemli:** `main`deki gerçek workflow'lar ve yayınlar bir PR oluşturulmasıyla değişmiş olmaz. PR merge + GitHub Actions sonuçlarını doğrulamadan geçiş başarıyla tamamlandı denmez.

## 4. İlk, tekrar etmeyen EGI yayın kataloğu

**Main’deki onaylı takvime eklenen içerikler** (18 Kasım’da PR #27 merge edildi; ilk gerçek yayın henüz ayrıca doğrulanmadı):

| Gün (İstanbul) | Bölüm | Kategori | Kaynak |
|---|---|---|---|
| 19 Kasım 2026 | URL'den tarayıcıya (DNS→TCP→TLS→HTTP→HTML/CSS/JavaScript) | Yazılım | EGI V16 |
| 19 Kasım 2026 | Kablosuz şarj / AC→indüksiyon→DC | Teknoloji | V16 teknoloji / V15 aile temeli |
| 20 Kasım 2026 | Turbo nasıl çalışır | Mekanik | V8.9 |
| 20 Kasım 2026 | Intercooler nasıl çalışır | Mekanik | V9.1 kaynaklı pilot |

- Günlük slotlar katalogdaki bölüm sayısına göre **12:00 / 17:00**, tek video günlerinde **15:00**, Europe/Istanbul. Zaman geçmişse yayıncı güvenli ileri saate planlar.
- 21 Kasım 2026 ve sonrası için henüz **onaylı yeni bölüm yoksa sistem sessiz kalmalı**. Creative R&D ajanı yeni özgün video + katalog PR’ları hazırlar; Reviewer yalnız görsel/teknik QA’yı karşılayanları merge edebilir. Bu otomatik süreç iyi niyetli hedef olup **gelecekte her gün video üretileceğinin garantisi değildir**. Asla aynı dosyayı yeni bölüm gibi tekrar yayımlama.
- Motor V8.8, diferansiyel V12, diğer test klipleri korunur; ancak **bu ilk katalogda yoktur**. Yeni katalog girdisi, orijinal renderer + görsel inceleme + QA ile eklenmelidir.
- Önceki V7 `daily-latest` release etiketi ile EGI `egi-daily-latest` **ayrıdır**. Yanlış etiketten içerik çekmek yasak.

## 5. Ajanların yeni rolü

Eski V7 puzzle odaklı beş aktif otomasyonun adları/promptları **EGI'ye çevrilmiştir** (18 Kasım). Güncellenmiş ajanlar:

- `EGI · Analytics & Strateji` — yaş-eşlemeli 24/48/72 saat ve 7 gün raporu, gerçek kanıt ve format kıyaslaması.
- `EGI · Trend Scout` — yazılım/teknoloji/mekanik alanında güncel özgün İngilizce fikirler ve mikro animasyon planı.
- `EGI · Creative R&D` — açık kaynak prosedürel hareket, ses/ikon/kalite geliştirme; **haftada iki planlı çalışmada** farklı özgün bölüm renderer + yeni episode catalog girdisi içeren izolasyonlu PR açabilir. Kalite uygun değilse sayıyı zorlamaz.
- `EGI · Sistem Denetimi` — günlük EGI release, manifest, YouTube doğrulama, SHA, eksik bölüm/no-filler, legacy cron kapalı mı.
- `EGI · Reviewer & Integrator` — tek olay/callout, mobil taşma, semantik kaynak, tam MP4 önizlemesi ve QA kontrolü; EGI V16 standardında tamamen yeni bölüm PR’larını **görsel + teknik test kanıtıyla** ve önceden onaylanmış format içinde kaldığında güvenle main’e merge edebilir. Yayın/OAuth/cron/kanal gibi çekirdek sistem değişikliklerinde ayrıca kullanıcı onayı gerekir; kendisi upload başlatmaz.

**Geçiş sırasında bu beş ajan geçici olarak durduruldu; PR #27 merge ve QA sonrası 18 Kasım’da beşi de yeniden etkinleştirildi.** Eski puzzle görevlerini açma. Ajanların etkinlik durumunu gerektiğinde canlı sistemden tekrar doğrula.

## 6. Yayın öncesi ve yayın sonrası zorunlu kontroller

1. `EGI Production Cutover Test` yeşil olmalı: iki günlük render, dört farklı MP4, SHA, H.264/AAC, doğru çözünürlük, audio, süre, duplicate-check.
2. İlk pilotların görsel ve teknik anlamı onaylı olmalı: web kaynak aktarımı ayrı nesne, kablosuz şarjın bobinleri, mekanik akışlar doğru, açıklama balonları tekil.
3. **Tamamlandı:** PR #27 QA yeşilken `main`e merge edildi. V7 `render-daily.yml` artık scheduled render değil, güvenli `retired` stub; `publish-youtube.yml` yalnız EGI manifestini kabul eder.
4. Cron `egi-daily.yml` günün tek üreticisi olsun. Yayımlama tarafı **YouTube OAuth** ile var olan **EGI** kanalına yapar; kanal/handle yanlışsa otomatik yükleme durmalı.
5. Manifest release `egi-daily-latest` üzerinde EGI-only; ilk gün en fazla 2 benzersiz `episode_id`.
6. Günlük bölüm bitince **NO_NEW_EPISODE** normaldir. Veri yokken zorla upload, yeniden gönderim, eski puzzle fallback yasak.
7. Geçiş sonrası ajansal denetim, Metrics ve yayın sonucu kontrol edilir. İlk 14 gün performans eşlemeli izlenir, ham toplam view ile yanlış çıkarım yapılmaz.

## 7. Riskler, rollback ve silme politikası

- **Geri dönüş:** EGI workflow başarısızsa önce EGI cron/publisher dispatch'i durdur; YouTube'da zaten planlanmış videoların durumunu kontrol et. Gerekirse repo önceki V7 commit'ine döndürülebilir, fakat bu otomatik olarak V7 puzzle yayınlarını açmamalıdır. Hatalı duplicate upload/planlama yaratma.
- **Eski YouTube videolarını silme.** İzlenmeler, aboneler ve geriye dönük raporlar korunur.
- **Eski V6.1 / V7 / V8 Markdown'larını silmek zorunda değilsin.** Bunlar tarihi bilgi, eski mimari ve rollback için faydalı. Fakat yeni oturumların aktif talimatı olmasın; `ARCHIVE/LEGACY` klasörüne taşı veya başlarına **SUPERSEDED BY EGI V16** ekle. EGI güncel belgeyi proje hafızasının **birincil kaynağı** yap.
- Projeyi temizlemek istiyorsan **önce** bu MD'yi projeye ekle ve dosyanın erişimini kontrol et; sonra eski MD'leri aktif proje eklerinden ayırabilirsin. Eski dosyaların yedeğini repo/yerel arşivde tut. Silme kalıcıysa ancak yedek/rollback ihtiyacının olmadığından emin olduktan sonra.
- ChatGPT'nin kişisel Memory özelliği ile proje .md dosyaları ayrı mekanizmalardır; bu MD eklemek geçmiş belleği otomatik silmez. Tarihi bilgiye dayanıp V7 otomasyonunu tekrar etkinleştirmemek için yeni belgede açık öncelik belirtilmiştir.

## 8. Sonraki oturum için ilk komut

> **EGI V16 production geçişi 18 Kasım’da merge edildi, QA yeşil, beş EGI ajanı aktif. İlk iş: 19 Kasım 2026 `egi-daily.yml` workflow run, `egi-daily-latest` manifest ve `publish-youtube.yml` upload sonuçlarını kontrol et. V7 `render-daily.yml` retired olmalı. YouTube kanal kimliği doğrulaması `UCNNyhE1DlhTXIip_p96kczA`. Katalogda yalnız 19–20 Kasım için dört bölüm var; 21 Kasım’dan sonrası için özgün bölümler oluşturulup QA’dan geçirilmeden yayın yapılamaz. Her gün en fazla iki, tekrarsız. Bu dosya eski V6/V7/V8 MD'lerine göre öncelikli.**

---

**Kaynak güven düzeyi:** Kullanıcının marka/animasyon tercihleri kesin; PR #26 ve #27 main'e merge edildi, preview ve dört pilotlu cutover QA yeşil, beş EGI ajanı aktif. **Gerçek YouTube upload/publish başarısı henüz test edilmedi; 19 Kasım 2026 ilk production çalışmasında doğrulanacak.**