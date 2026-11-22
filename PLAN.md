# 3Dworld — Ürün ve Teknik Plan

> **License notice:** This project is for testing and evaluation purposes only and is strictly not licensed for commercial use. See [`LICENSE`](LICENSE). Third-party components remain under their own licenses (see [`LICENSES.md`](LICENSES.md)).
>
> **Lisans notu (TR):** Bu proje yalnızca test ve değerlendirme amaçlıdır, ticari kullanım yasaktır ([`LICENSE`](LICENSE)). Aşağıdaki "ticari kullanıma uygun lisans" kuralı ise **dışarıdan aldığımız** bileşenler içindir; böylece ileride ticari sürüme geçmek istersek lisans engeli çıkmaz.

**Hedef:** Tek bir 2D görseli **anlayan**, parçalara ayıran, her objeyi ve arka planı **3D'ye çeviren**, kullanıcının tarayıcıda mouse ile düzenleyebildiği bir sahne kuran ve bu sahneden **üretken video modellerini kontrol eden** (kamera, düzen) bir "planlama + kontrol katmanı". Podcast'te anlatılan Evren (Evron) ürününe benzer.

**Kesin kurallar:**
1. Dışarıdan alınan her model, kütüphane ve servis ticari kullanıma uygun lisanslı olacak. Doğrulanmış liste, yasaklılar ve gerekçeleri [`LICENSES.md`](LICENSES.md) dosyasında. Orada ✅ olmayan hiçbir şey koda veya sunucuya girmez.
2. Rust, işi gerçekten hızlandırdığı yerde kullanılacak (§5).
3. Aşama aşama ilerlenecek (§6). Her faz kendi başına denenebilir bir şey üretecek.

Bu belge hukuki görüş değildir. Sürüm: 2 (4 bağımsız incelemeden sonra güncellendi, 2026-11-21).

---

## Terimler

| Terim | Anlamı |
|---|---|
| **Obje** | Görseldeki ayrı bir şey: at, saman, bot… |
| **Maske** | Objenin görseldeki piksel alanı (segmentasyon sonucu) |
| **Tamamlama** | Kadrajda kesilmiş ya da başka objenin arkasında kalmış kısmı tahmin edip çizme (amodal completion) |
| **Arka plan doldurma** | Objeler çıkarılınca açılan boşluğu doldurma (inpainting) |
| **Asset** | Bir objenin 3D dosyası (GLB mesh, opsiyonel splat) |
| **Sahne grafiği** | Tüm objeler, konumları, kamera, ışıklar ve onay durumlarını tutan tek kayıt (`scene.json`) |
| **Hizalama** | 3D asset'i fotoğraftaki yerine doğru konum, açı ve ölçekle oturtma |
| **Render pass** | Sahneden üretilen yardımcı videolar: renkli önizleme, derinlik, kenar, obje kimliği |

---

## 0. Sahiplik stratejisi: ne kadarı bizim yazılımımız?

%100 sıfırdan (kendi eğittiğimiz modellerle) başlamak gerçekçi değil. Segmentasyon, derinlik, görselden 3D ve video modelleri milyonlarca görsel ve milyon dolarlık GPU bütçesiyle eğitiliyor. Podcast'teki Evren ekibi de bunu yapmıyor; kullandıkları 12 adımdan biri Meta'nın Segment Anything'i (olası araç listesi: Ek A). Değeri yaratan şey modeller değil, onları birleştiren katman.

| Katman | Ne | Sahiplik |
|---|---|---|
| **A: %100 bizim kodumuz** | Sahne grafiği, iş akışı ve ajan, **hizalama** (en zor kısım), 2.5D katmanlar ve derinlik mesh'i, editör, kamera yolu, render pass'leri, kredi sistemi, dışa aktarma (GLB/OBJ/PLY/USD), TRELLIS'in son işleme adımı (lisans nedeniyle yeniden yazılıyor, §4) | Tamamen bizim |
| **B: Açık ağırlıklı modeller, kendi makinemizde** | SAM 2.1 (Meta), MoGe-2, TRELLIS, LaMa, Qwen-Image-Edit, Wan… | Ağırlık kopyaları bizde. Dış API, kullanım ücreti veya lisans ücreti yok. Değiştirip ince ayar yapabiliriz |
| **C: Kendi eğittiğimiz modeller (ileride)** | Kullanıcı düzeltmelerinden biriken veriyle B'deki modellerin ince ayarlı veya damıtılmış sürümleri | Tamamen bizim |

Her model bir **adaptör** arkasında durur (`segment()`, `estimate_geometry()`, `image_to_3d()`…). Daha iyi bir model ya da ileride kendi modelimiz geldiğinde yalnızca adaptör değişir.

**Meta modelleri:** SAM 2.1 ve DINOv2 Apache-2.0, güvenle kullanılır. SAM 3, SAM 3D Objects ve DINOv3 Meta'nın özel lisanslarıyla geliyor; okunup `LICENSES.md`'ye işlenmeden kullanılmaz. SAM 3D Objects, objeyi doğrudan kameranın koordinatlarında üretip konumunu da tahmin ettiği için hizalama sorununu büyük ölçüde çözebilir. Lisansı uygunsa en değerli aday bu (§8).

---

## 0.1 Podcast'teki özelliklerin bizim planımızdaki karşılığı

| # | Özellik (Evren) | Bizde nasıl | Katman | Faz |
|---|---|---|---|---|
| 1 | Tek görselden başlama | Yükleme + kalite kontrolü (düşük çözünürlük uyarısı) | A | 1 |
| 2 | Görseli anlama ("seni anladım") | Görsel-dil modeli ile obje listesi + güven skoru | B | 1 |
| 3 | Segmentasyon | Grounding DINO + **SAM 2.1 (Meta)** | B | 1 |
| 4 | Onay / düzeltme ("oyuncak → saman") | Etiket düzenleme. Düzeltilen etiket sonraki adımlara prompt olarak gider | A | 1 |
| 5 | Kesik objeyi tamamlama | Qwen-Image-Edit (2.5D katmanlar için de gerekli) | B | 1 |
| 6 | Arka planı tamamlama | LaMa / Qwen-Image-Edit | B | 1 |
| 7 | Yeniden üretme | Farklı seed ile 2–4 aday, sürüm geçmişi | A | 1 |
| 8 | Kredi (token) onayı | Faz 1'de basit kota, Faz 2'de adım başı GPU süresi tahmini + onay | A | 1–2 |
| 9 | Her objeyi ayrı 3D'ye çevirme | TRELLIS (v1, kendi son işlememizle) | B + A | 2 |
| 10 | Arka planı 3D'ye çevirme | Faz 1: katmanlı derinlik mesh'i. Faz 2: zemin ve duvarlarla tam sahne | A | 1 → 2 |
| 11 | Sahneyi bire bir birleştirme, splat gösterimi | Hizalama motoru. Mesh ana format, splat yalnızca önizleme (Spark) | A | 2 |
| 12 | Üretim süresi (~15 dk) | Yalnızca GPU süresi (kullanıcı inceleme süresi hariç). Tek RTX 4000 ile tutmaz (§5.4) | A | 2 |
| 13 | 12 modelli altyapı | Adaptör arayüzü + iş kuyruğu + tek GPU zamanlayıcı | A | 0 |
| 14 | Ajan mimarisi | Sahne grafiği üzerinde tipli araçlar | A + LLM | 4 |
| 15 | Video modelleri için yerleşim referansı | Kamera yolu → render pass'leri → video modeli | A | 3 |
| 16 | Çoklu girdi (görsel, video, kılavuz) | Çoklu görsel/video ile geometri; PDF kılavuzdan parça listesi | A + B | 5 |
| 17 | Konuşarak düzenleme | Ajan + bas-konuş + yazılı alternatif + yıkıcı işlemlerde onay | A + B | 4 |
| 18 | Uçtan uca prodüksiyon | Wan + VACE ile kendi makinemizde video | B | 3 |
| 19 | 2D platformlara entegrasyon | Dışa açık API + SDK (hedef platform Faz 5'te seçilir) | A | 5 |
| 20 | Robot eğitimi | Parça etiketleme, MJCF/USD export, sentetik veri | A | 5 |
| 21 | Robotların insanları eğitmesi | Tanımsız (Evren'de de öyle), kapsam dışı | — | — |
| Cuebric | 2.5D katmanlar + mesh export | Faz 1'in 2.5D katmanları + GLB export. USD/OBJ Faz 2'de. FBX ileride ikili (binary) formatta | A | 1–2 |
| Cuebric | LED ekran için gerçek zamanlı kamera takibi | **Şimdilik kapsam dışı.** Talep olursa Faz 5'te (Unreal/LED ekran bağlantısı) | — | 5+ |

---

## 1. Ürün akışı (podcast'teki demodan)

1. **Anla:** Görsel yüklenir, sistem "ahır, at, saman, kovboy botu…" diye obje listesi çıkarır.
2. **Ayır:** Her obje maskelenir.
3. **Kullanıcı doğrular:** etiketleri ve maskeleri onaylar ya da düzeltir.
4. **Tamamla:** Kesik/örtülü objeler tamamlanır, arka plandaki boşluklar doldurulur. Her biri onaylanır ya da yeniden üretilir.
5. **3D'ye çevir:** Her obje ayrı asset olur, arka plan 3D zemine dönüşür, hepsi orijinal kameraya göre yerleşir.
6. **Düzenle:** Tarayıcıda objeleri mouse ile taşı, döndür, kamera yolu çiz.
7. **Kontrollü video:** Kamera yolundan render pass'leri üret, video modeline koşul olarak ver.
8. **Ajan** (Faz 4) ve **B2B / robotik** (Faz 5).

### 1.1 İnsan onaylı akış (human-in-the-loop)

Makine önerir, insan kontrol eder: veri etiketlemedeki "insan doğrulaması" mantığı. Her ekranda aynı üç düğme var: **Onayla / Düzelt / Yeniden üret**. Yüksek güvenli öneriler için **"Hepsini onayla"** düğmesi var. Her ekrandan bir önceki ekrana iş kaybetmeden dönülür.

**İki akış modu:**
- **Hızlı mod (varsayılan, Evren'deki gibi):** Kullanıcı objelere tıklar. Sistem onaylanan obje listesi için tamamlamayı ve 3D'yi **hemen** üretir ve sonucu gösterir. Kullanıcı 3D sonuç üzerinde onaylar, düzeltir ya da yeniden ürettirir. Kredi onayı tek seferde, 3D'ye geçmeden önce alınır.
- **Adım adım mod:** Pahalı ya da kritik objeler için her ara adım (maske → tamamlama → 3D) ayrı onaylanır, böylece hata 3D'ye taşınmaz.

**İlk kullanım:** Yeni kullanıcı kredi harcamadan önce hazır bir örnek sahneyle (önceden işlenmiş) ürünü dener.

**Ekran 1: Yükleme (Faz 1).** Görsel yüklenir. Kalite kontrolü yapılır (çok küçük, aşırı kırpılmış veya bulanıksa uyarı). Arka planda MoGe-2 derinliği hesaplanır ve SAM 2.1'in görsel kodlaması bir kez yapılır (CPU'da ~2 sn), böylece tıklamalar anında yanıt verir.

**Ekran 2: Objeleri seç ve doğrula, "bu bot mu, at mı?" (Faz 1).**
- **Ana etkileşim tıklamak:** Kullanıcı objenin üstüne tıklar, maske anında gelir (ölçüm: CPU'da tıklama başına ~30–60 ms). Ekranın tamamı otomatik taranmaz.
- **Parça / bütün:** Tek tıklama belirsizdir (minder mi, koltuk mu?). SAM üç aday verir; varsayılan "bütün obje", kullanıcı tekerlek veya kısayolla parça ↔ bütün arasında geçer.
- **Düzeltme tıklamaları:** artı tıklama eksik kalan parçayı ekler, eksi tıklama yanlış dahil edileni çıkarır.
- Maskeler görselin üstünde renk + dış çizgi + etiketle gösterilir (renk körlüğüne uygun palet), yanda obje listesi.
- **Etiket:** Görsel-dil modeli tıklanan objeye etiket önerir ("at", "kovboy botu"). Kullanıcı düzeltir; düzeltilen etiket sonraki adımlara prompt olarak gider.
- **Maske düzelt:** fırça ile ekle/sil, birleştir, böl.
- **Otomatik öneri (isteğe bağlı):** "Objeleri öner" düğmesi tüm görseli tarar (CPU'da ~40 sn) ve derinlikte öne çıkan objeleri önerir; duvar, zemin ve halı elenir.

**Ekran 3: Tamamlamaları kontrol et, "yarım atı düzgün tamamladı mı?" (Faz 1).**
- Her obje için bir kart: solda orijinal kesik hali, sağda tamamlanmış hali. Onayla, yeniden üret (2–4 aday yan yana) veya prompt ekle.
- **Arka plan kartı:** objeler çıkarılmış, boşlukları doldurulmuş arka plan. Bu adım şart: obje oynatıldığında arkasında delik değil, doldurulmuş zemin görünmeli.
- Her "yeniden üret" düğmesinin yanında tahmini kredi yazar.

**Ekran 4: Kredi onayı (Faz 2).** Obje sayısı ve kaliteye göre tahmini GPU süresi ve kredi. GPU hatasında kredi otomatik iade edilir.

**Ekran 5: 3D'ye çevirme (Faz 2).**
- Her obje sırayla 3D'ye çevrilir. TRELLIS, tamamlanmış görselden objenin görünmeyen arka tarafını tahmin eder.
- Hazır oldukça sahnede belirir; ilerleme ve kalan süre gösterilir. Sekme kapatılabilir, iş sunucuda devam eder, bitince bildirim gelir.
- Sonuç, orijinal kameradan fotoğrafın üstüne bindirilerek gösterilir.
- **Kısmi başarısızlık:** 9 objeden 7'si başarılıysa kullanıcı devam eder. Başarısız olanlar için sırayla şu seçenekler sunulur: yeniden dene, 2.5D kart olarak kullan, düz görsel olarak kullan.

**Ekran 6: 3D sahne editörü, mouse ile hareket (Faz 2).**
- **Kamera:** sürükle → sahne etrafında dön, tekerlek → yakınlaş, "orijinal kameraya dön". Kamera, arkası doldurulmamış alanların görüneceği açılara gidemez ("geçerli kamera alanı"). Sınırda uyarı verilir.
- **Seç:** objeye tıkla (çoklu seçim için Shift).
- **Taşı:** sürükleyince obje **zemin üzerinde** sağa, sola, ileri, geri kayar; havaya kalkmaz, gömülmez. Shift + sürükle ile yükseklik. Klavye ok tuşlarıyla hassas kaydırma.
- **Döndür / ölçekle:** dikey eksen etrafında döndürme halkası, köşe tutamakları.
- **Çarpışma:** objeler birbirinin içine girmez (Faz 2'de basit sınır kutusu kontrolü).
- **Işık uyumsuzluğu:** Objenin ışığı fotoğraftan geliyor. Çok uzağa taşınırsa "ışık uyumsuz olabilir" uyarısı gösterilir. Basit temas gölgesi var, yeniden ışıklandırma ileride.
- **Zemin bulunamazsa** (ör. yakın çekim): kullanıcı zemini üç noktaya tıklayarak tanımlar.

**Tüm ekranlarda geri al / yinele.** Her değişiklik (etiket, maske, onay, taşıma) sahne grafiğinde tek bir değişiklik kaydına (diff) yazılır. Faz 4'teki ajan da aynı kaydı kullanır. Oturum otomatik kaydedilir, kaldığı yerden devam edilir.

### 1.2 Bir şey değişirse sonrası ne olur? (bağımlılık kuralları)

| Değişen | Etkilenen | Ne olur |
|---|---|---|
| Etiket | O objenin tamamlaması ve 3D'si | "Güncel değil" rozeti alır, yenileme kredisi gösterilir. **Kredi asla kendiliğinden harcanmaz.** |
| Maske | Tamamlama, arka plan doldurma, 3D | Aynı |
| Tamamlama seçimi | O objenin 3D'si | Aynı |
| Arka plan doldurma | Arka plan 3D'si, render'lar | Aynı. Objelerin elle verilmiş konumları korunur |
| 3D yeniden üretildi | O objenin konumu | Kullanıcının elle verdiği konum, açı ve ölçek korunur, yeni asset aynı yere oturtulur |

Obje başına durum makinesi:

```
önerildi → onaylandı/düzeltildi → tamamlandı → tamamlama onaylandı → 3D üretiliyor → 3D hazır → yerleştirildi → elle düzenlendi
     ↑                                                                    │
     └──── yukarıdaki bir adım değişince: "güncel değil" ◄────────────────┘
                                         başarısızlık: "hata" → yeniden dene / 2.5D kart / düz görsel
```

### 1.3 Her insan kararı veridir (açık izinle)

Etiket düzeltmeleri, eklenen maskeler, seçilen/reddedilen adaylar ve yeniden üretme sayıları kaydedilir. İki amacı var: kalite ölçümü (hangi adım en çok düzeltiliyor?) ve Katman C'de kendi modellerimizi eğitmek. **Bu veri yalnızca kullanıcı açıkça izin verirse (opt-in) eğitim için kullanılır.** Saklama süresi ve silme hakkı baştan tanımlanır. Bu, Faz 1'den itibaren geçerli.

---

## 2. Pipeline mimarisi

```
 Görsel
   │
   ▼
[1] Sahne anlama (VLM) ──► obje listesi + etiket + güven skoru  ◄── kullanıcı düzeltmesi
   ▼
[2] Lokalizasyon (Grounding DINO) + segmentasyon (SAM 2.1) + kenar iyileştirme (BiRefNet)
   ▼
[3] Geometri: MoGe-2 → metrik nokta haritası + kamera (FOV). Kamera koordinat sistemi sabitlenir (§2.1)
   ▼
[3b] Örtme sırası: hangi obje hangisinin önünde (maskeler + derinlik)
   │
   ├──────────────────────────────────────┐
   ▼                                      ▼
[4] Tamamlama (obje başına)            [5] Arka plan doldurma
    - kadraj dışına taşan obje için        - doldurulan arka plan için derinlik yeniden
      tuvali genişlet (outpaint)             hesaplanır ve maske dışında orijinal
    - görünen orijinal pikseller             derinliğe eşitlenir
      sonuca geri yapıştırılır
    - arka planı silinip RGBA yapılır
   │                                      │
   ▼                                      ▼
[6] Obje → 3D (TRELLIS v1) +           [7] Arka plan → katmanlı derinlik mesh'i
    kendi son işleme ve doku basma         (derinlik sıçramalarında kesilir,
    (§4: lisans nedeniyle)                  uzamış üçgen olmaz)
   │                                      │
   └──────────────┬───────────────────────┘
                  ▼
[8] Hizalama (§2.2): çoklu başlangıç + ölçek + silüet/derinlik puanı + zemine oturtma
                  ▼
        scene.json + GLB asset'ler (tek doğruluk kaynağı: sahne grafiği)
                  ▼
[9] Web editör (three.js) ── kamera yolu, ışık, gizmo'lar, geçerli kamera alanı
                  ▼
[10] Render pass'leri (tarayıcıda WebGL ile üretilip sunucuya yüklenir): RGB, derinlik, kenar, obje kimliği
                  ▼
[11] Video adaptörleri: Wan2.1-VACE-1.3B (kendi makinemizde) | kapalı API'ler (RGB render ile)
```

### 2.1 Koordinat sistemi (Faz 0'da sabitlenir)

MoGe OpenCV eksenleri kullanır (y aşağı, z ileri). glTF ve three.js ise y yukarı, −z ileri. `scene.json` **glTF/three.js eksenlerini ve metre birimini** kullanır. Dönüşüm tek bir yerde, `scene-schema` içinde yapılır. Bu Faz 0'da yazılır ve testle kilitlenir. Aksi halde her şey ters ya da aynalı çıkar.

### 2.2 Hizalama: projenin en zor ve en farklılaştırıcı kısmı

TRELLIS objeyi kendi küpünde ve kendi yönünde üretir, kameranın koordinatlarında değil. Bu yüzden konum, açı ve ölçeğin hepsi çözülmeli. Tek başlangıç tahminiyle yapılan silüet + ICP eşleştirmesi yerel minimumlara takılır, simetrik objelerde yön karışır. Tarif:

1. **Ölçek ve konum:** Maskeyi birkaç piksel küçült (kenar derinliği gürültülü), içindeki MoGe-2 noktalarıyla Umeyama hizalaması.
2. **Açı:** Birden fazla başlangıç dene: dikey eksen etrafında 8–24 açı × 2–3 eğim.
3. **İyileştirme:** Her aday için PyTorch'ta diferansiyellenebilir render ile silüet IoU + derinlik hatası en aza indirilir. En iyi aday seçilir.
4. **Zemine oturtma:** Zemin düzlemi (RANSAC) bulunur, objenin tabanı zemine değdirilir.
5. **Bire bir görünüm:** TRELLIS görünmeyen tarafı tahmin ettiği için orijinal kameradan bakınca fotoğrafla tam örtüşmez. Orijinal kamera açısında objenin görünen yüzüne fotoğrafın kendi pikselleri yansıtılır (ya da 2.5D katmanı gösterilir). Kamera uzaklaştıkça 3D asset'e geçilir.

Hizalama tamamen **Python + PyTorch**'ta yapılır (GPU'da çalışır, diferansiyellenebilir render gerekir). Rust'ta ayrıca ICP/RANSAC yazılmaz.

---

## 3. Bileşen seçimi (ticari kullanıma uygun, `LICENSES.md` ile aynı)

| Adım | Birincil seçim | Lisans | Yedek / not |
|---|---|---|---|
| 1. Sahne anlama | Claude API (tool use, JSON çıktı) | API ToS | Kendi makinemizde: Qwen2.5-VL-7B, 8/4-bit (Apache-2.0) |
| 2a. Etiketten kutu | Grounding DINO | Apache-2.0 | OWLv2 (Apache-2.0), Florence-2 (MIT) |
| 2b. Maske | SAM 2.1 | Apache-2.0 | Kenar: BiRefNet (MIT) |
| 3. Derinlik + kamera | **MoGe-2** (metrik ölçek + FOV) | MIT | Yedekler birebir yerine geçmez: Depth Anything V2 Small yalnızca göreli derinlik verir, FOV vermez |
| 4. Tamamlama | Qwen-Image-Edit-2509, 4-bit GGUF + Qwen-Image-Lightning (4–8 adım) | Apache-2.0 | Model maske girdisi almaz: sonucun görünen kısmına orijinal pikseller geri yapıştırılır |
| 5. Arka plan doldurma | LaMa (hızlı) | Apache-2.0 | Kalite için Qwen-Image-Edit |
| 6. Obje → 3D | **TRELLIS v1** (`TRELLIS-image-large`) + kendi son işleme | MIT (model + kod) | TRELLIS.2: DINOv3 lisansı okunana kadar ⏳. TripoSR (MIT): hızlı, düşük kalite |
| 7. Arka plan → 3D | Kendi kodumuz (Rust `geom-core`): katmanlı derinlik mesh'i | — | Faz 2+: gsplat (Apache-2.0) ile splat |
| 8. Hizalama | PyTorch + PyTorch3D (diferansiyellenebilir render) | BSD | — |
| 9. Editör | three.js + React Three Fiber + drei | MIT | Splat önizleme: Spark (MIT) |
| 10. Render pass | Tarayıcıda three.js shader'ları | MIT | Sunucu tarafı gerekirse ileride Rust wgpu |
| 11. Video (açık) | **Wan2.1-VACE-1.3B** (480p, ~5 sn parçalar) | Apache-2.0 | Wan2.1-Fun-1.3B-Control, CogVideoX-2B (Apache-2.0). Not: Wan2.2-TI2V-5B VACE kontrolü almaz |
| 11. Video (kapalı) | Veo, Seedance, Kling, Runway adaptörleri | ToS | Çoğu derinlik videosu kabul etmez: RGB render, video-to-video veya ilk kare olarak gönderilir |
| Export | GLB, OBJ, PLY, USD(A) | Kendi yazıcılarımız | FBX: ileride ikili format (Blender ASCII FBX okuyamaz) |
| Robotik (Faz 5) | MuJoCo (MJCF export) | Apache-2.0 | USD export |

---

## 4. Lisans tuzakları (özet, ayrıntı `LICENSES.md`'de)

En önemlisi: **TRELLIS'in kendisi MIT ama resmi kurulumu yasaklı paketler getiriyor.**

- **TRELLIS v1:** nvdiffrast (NVIDIA, ticari yasak), diffoctreerast ve mip-splatting (Inria, ticari yasak), pymeshfix ve plyfile (GPL-3.0), igraph (GPL-2).
  - **Çözüm:** Bunları hiç kurmuyoruz.
  - Mesh çıkarma kendi kodumuzla yapılıyor. FlexiCubes, kaolin (Apache-2.0) içinde.
  - Doku basma PyTorch3D ile, mesh temizleme kendi kodumuzla yapılıyor. PLY yazıcısı Rust'ta.
  - Görseli TRELLIS'e **arka planı silinmiş (RGBA)** veriyoruz. Böylece içindeki rembg hiç çalışmıyor.
  - Bu iş **Faz 2'de ayrıca zaman bütçelenmiş bir görev.**
- **TRELLIS.2:** Üstüne briaai/RMBG-2.0 (CC BY-NC, ticari yasak) ve DINOv3 (Meta özel lisansı) kullanıyor. DINOv3 lisansı okunana kadar ⏳.
- **Depth Anything V2 Base/Large/Giant:** CC BY-NC. Yalnızca Small.
- **Hunyuan3D, Stable Fast 3D, FLUX dev, YOLO (AGPL), MinIO (AGPL):** kullanılmaz.
- **Görünmeyen kaçaklar:** Çalışma anında indirilen ağırlıklar (`from_pretrained`, `torch.hub`) paket lisans kontrolüne görünmez. Bu yüzden ağırlıklar tek bir yoldan (`weights.fetch`), izin listesi ve sabit sürümle indirilir; testler kodu, izin listesini ve LICENSES.md'yi karşılaştırır. Kendi ağırlık aynamız ve `HF_HUB_OFFLINE=1` planlı, henüz yok.

---

## 5. Teknoloji yığını

### 5.1 Rust nerede, Python nerede? (hız kuralı)

İlke: **Rust, CPU'da çalışan yoğun ve uzun ömürlü kodda. Python, GPU'daki model çıkarımında ve hizalamada.** Model çıkarımında süre zaten CUDA çekirdeklerinde geçiyor. TRELLIS veya Wan'ı Rust'a taşımak aylar sürer ve hız kazandırmaz. Rust'ın kazandırdığı hız modellerin *arasındaki* işlerde.

İncelemeden sonra Rust kapsamı **daraltıldı ve sıraya kondu.** Küçük ekip iki dili Faz 0'dan itibaren taşıyacağı için yalnızca kazancı net yerlerde başlıyoruz:

| Alan | Dil | Ne zaman | Neden |
|---|---|---|---|
| **API + iş akışı** (kuyruk, kredi, canlı ilerleme) | **Rust** (axum + tokio + sqlx) | Faz 0 | Tek binary, düşük gecikme, tip güvenliği |
| **İş kuyruğu** | **PostgreSQL** (`FOR UPDATE SKIP LOCKED`) | Faz 0 | Rust ve Python ikisi de aynı tabloyu okur; ayrı kuyruk sunucusu gerekmez |
| **`geom-core`**: derinlik → nokta bulutu → mesh (sıçramalarda kesme), 2.5D katmanlar, mesh sadeleştirme (meshopt), PLY/GLB/OBJ/USDA yazıcıları, splat format dönüşümü | **Rust** | Faz 1 | En büyük CPU kazancı: Python döngülerine göre 10–100×, rayon ile çok çekirdek |
| `geom-core`'un Python'dan kullanımı | Rust → **PyO3 + maturin + numpy crate** | Faz 1 | Diziler sınırda bir kez kopyalanır (bellek düzeninden bağımsız okuma), hesap sırasında GIL bırakılır |
| `geom-core`'un tarayıcıdan kullanımı | Rust → **WASM**, önce **tek çekirdekli** | Faz 2 | Tarayıcıda çok çekirdek için nightly Rust ve COOP/COEP başlıkları gerekiyor, bu yüzden önce tek çekirdek. meshopt/xatlas (C/C++) yalnızca sunucuda kalır |
| Hafif modeller (SAM 2 maske çözücü) | İleride Rust/tarayıcıda ONNX | Gerekirse | Önce Python worker; tıklama gecikmesi sorun olursa taşınır |
| Video kodlama | Rust (rav1e AV1, openh264) | Faz 3 | Wan zaten kare tensörü alır; kodlama yalnızca dışa aktarma ve kapalı API'ler için |
| Ağır modeller, hizalama | **Python + PyTorch** | Her zaman | Modellerin kendi kodu bu |
| Editör arayüzü | **TypeScript** (React + three.js) | Faz 1 | UI ekosistemi burada |

Ertelenenler: kendi WebGL splat görüntüleyicimiz (yerine Spark), FBX yazıcısı, sunucu tarafı render (önce tarayıcıda render edilip yüklenir; gerekirse Rust + wgpu).

Rust ile Python arasındaki veri formatı anlaşması `scene-schema` içinde tek kaynaktan üretilir: Rust `serde` yapıları → JSON Schema → TypeScript ve Pydantic tipleri.

### 5.2 Diğer bileşenler

- **Frontend:** Next.js + React + React Three Fiber + drei, Zustand, `TransformControls`.
- **Veritabanı ve depolama:** PostgreSQL. Dosyalar başta yerel diskte, sonra S3 uyumlu depolama (Cloudflare R2 veya SeaweedFS, Apache-2.0). Asset'ler içerik özetiyle (hash) adreslenir, aynı şey iki kez üretilmez.
- **GPU worker'ları:** Python, her model ailesi için ayrı Docker imajı. Kuyruktan iş alır, `geom_core` modülünü kullanır.
- **LLM / ajan:** Claude API tool use.

### 5.3 Repo yapısı

✅ = var, (planlı) = henüz yok.

```
3Dworld/
  Cargo.toml  rust-toolchain.toml  deny.toml  Makefile  pyproject.toml   ✅
  crates/
    scene-schema/        # ✅ Rust serde tipleri → JSON Schema; koordinat dönüşümleri; durum makinesi
    geom-core/           # ✅ Rust: geometri çekirdeği (saf Rust, test edilebilir)
    geom-py/             # ✅ Rust → Python (PyO3/maturin) + geom_core.pyi tip dosyası
    api/                 # (planlı) Rust: axum API + iş akışı + kredi + Postgres kuyruğu
    geom-wasm/           # (planlı, Faz 2) Rust → tarayıcı (wasm-bindgen)
    encode/              # (planlı, Faz 3) Rust: render → AV1/H.264
  apps/web/              # (planlı) Next.js + R3F editör
  workers/               # ✅ Python worker'ları
    common/              # ✅ modelsiz yardımcılar: scene_json, clicks, images, depth_ops, weights
    geometry/ segment/ complete/ pipeline/   # ✅ MoGe-2, SAM 2.1, LaMa, katmanlı sahne
    tests/               # ✅ modelsiz testler (CI'da çalışır)
    gpu_scheduler/       # (planlı) tek GPU paylaşımı, model yükle/boşalt
  schema/                # ✅ scene.schema.json + Python'un ürettiği örnek (sözleşme)
  requirements/          # ✅ sabit Python sürümleri
  scripts/               # ✅ setup_env.sh, check_blacklist.py
  weights/               # ✅ izin listesi + sabit sürümler (ağırlıklar git'e girmez)
  eval/                  # (planlı) test görselleri + metrik betikleri
  LICENSE  LICENSES.md  THIRD_PARTY_NOTICES.md  PLAN.md  README.md  CLAUDE.md
```

### 5.4 Donanım: tek RTX 4000 (varsayım: RTX 4000 Ada, 20 GB)

> ⚠️ Kartın tam modeli doğrulanmalı: `nvidia-smi --query-gpu=name,memory.total --format=csv`. Quadro RTX 4000 (8 GB, Turing) çıkarsa büyük modellerin çoğu sığmaz. O durumda ağır adımlar için bulut GPU gerekir.

| Model | 20 GB'da durum |
|---|---|
| SAM 2.1 + Grounding DINO + MoGe-2 + BiRefNet + LaMa | ✅ Toplam ~8 GB, **sürekli bellekte** kalır |
| Qwen-Image-Edit-2509 (20B + 7B metin kodlayıcı, bf16'da ~57 GB) | ⚠️ 4-bit GGUF + kısmen CPU'ya taşıma + Lightning ile görsel başına ~30–90 sn (ölçülecek) |
| TRELLIS v1 | ✅ ~16 GB, sınırda. Yüklenirken diğer büyük modeller boşaltılır |
| TRELLIS.2-4B | ⚠️ Muhtemelen 24 GB+, ayrıca lisans ⏳ |
| Wan2.1-VACE-1.3B | ✅ 480p, ~81 kare (~5 sn) parçalar. Uzun kamera yolları parçalara bölünür, parçalar arası tutarlılık için son kare sonraki parçaya verilir |
| Qwen2.5-VL-7B | ⚠️ Yalnızca 8/4-bit. Varsayılan Claude API (GPU harcamaz) |
| Wan 14B modelleri | ❌ Sığmaz (~80 GB) |

**GPU zamanlayıcı:** Küçük modeller hep yüklü. Büyük modeller (Qwen-Edit, TRELLIS, Wan) tek tek yüklenir. Aynı modeli kullanan işler arka arkaya gruplanır ki yükle/boşalt maliyeti azalsın (NVMe'den yükleme GB başına birkaç saniye).

**Süre beklentisi:** Tek kartla 10 objeli bir sahne muhtemelen 30–60 dakika GPU süresi alır. 15 dakika hedefi ancak birden fazla GPU ile tutar. Proje test amaçlı olduğu için geliştirmede sorun değil.

---

## 6. Yol haritası

> Süreler **1–2 geliştirici** varsayımıyla kaba tahmindir. Ekip büyüklüğü netleşince güncellenir.

### Faz 0: Temel (2–3 hafta)
- Lisans kapıları:
  - Paket lisansları: `cargo-deny` (✅ yapıldı); `pip-licenses`, `license-checker` (planlı).
  - Kara liste: nvdiffrast, nvdiffrec, diffoctreerast, diff-gaussian-rasterization, pymeshfix, plyfile, igraph, ultralytics, RMBG (✅ yapıldı).
  - Ağırlıklar için izin listesi ve sabit sürümler (✅ yapıldı); kendi aynamız ve `HF_HUB_OFFLINE=1` (planlı).
  - Otomatik üretilen `THIRD_PARTY_NOTICES.md` (planlı).
- Rust workspace: `scene-schema` (koordinat sistemi dahil, §2.1) ✅; `api`, Postgres kuyruğu, GPU zamanlayıcı iskeleti (planlı).
- Tek komutla tekrarlanabilir ortam (`make setup`), `make ci` = CI, `CLAUDE.md` oturum kuralları ✅.
- Her model, yasaklı paketler **kurulmadan**, ayrı bir ortamda tek tek çalıştırılır: SAM 2.1, MoGe-2, LaMa ✅; TRELLIS v1 (kendi son işleme prototipiyle) GPU'yu bekliyor.
- **M0 (iç kullanım):** Komut satırından `görsel → maskeler + nokta haritası + GLB` ✅.

### Faz 1: **M1 "Paralaks Sahne"**, ilk denenebilir ürün (5–7 hafta)
- Ekran 1–3: yükle → objelere tıklayarak seç (parça/bütün, artı/eksi tıklama) → etiketleri düzelt → tamamlamaları ve arka planı onayla/yeniden üret.
- `geom-core` (Rust + PyO3): her obje ve arka plan için derinlik mesh katmanları.
- Tarayıcıda: kamerayı geçerli alan içinde gezdir, gerçek paralaks, boşluklar dolu. Katmanlar düzlemde kaydırılabilir.
- Dışa aktarma: kısa MP4 + GLB.
- Basit kredi/kota koruması, geri al/yinele, otomatik kayıt, örnek sahne, eğitim verisi için opt-in.
- **Başarı ölçütü:** 10 test görselinde kullanıcı tüm akışı tamamlayabiliyor. Orijinal kameradan render, giriş görseline yakın (PSNR/LPIPS hedefi Faz 0'da ölçülerek belirlenir).

### Faz 2: Tam 3D (8–12 hafta)
- TRELLIS v1 + **lisans-temiz son işleme ve doku basma** (ayrı bütçelenmiş görev).
- Hizalama motoru (§2.2), zemin bulma, temas gölgesi.
- Ekran 4–6: kredi onayı, 3D'ye çevirme (kısmi başarısızlık ve geri dönüşler), mouse ile taşıma/döndürme/ölçekleme, çarpışma.
- `geom-wasm` (tek çekirdek), Spark ile splat önizleme.
- GLB / OBJ / PLY / USD dışa aktarma.
- **Başarı ölçütü:** Orijinal kameradan silüet IoU ve derinlik hatası hedefleri; GPU süresi ölçülüp raporlanır.

### Faz 3: Kontrollü video (4–6 hafta)
- Kamera yolu (anahtar kareler, lens, hız eğrisi) → tarayıcıda RGB, derinlik, kenar ve obje kimliği pass'leri.
- Wan2.1-VACE-1.3B ile 5 sn'lik parçalar halinde video, parçalar arası tutarlılık.
- Kapalı API adaptörleri: RGB render'ı video-to-video veya ilk kare olarak gönderme.
- `encode` crate'i (AV1 / H.264).

### Faz 4: Ajan katmanı (3–4 hafta)
- Claude tool use: `move_object`, `rotate_object`, `add_light`, `set_camera_path`, `regenerate_asset`, `relabel_object`…
- Her komut değişiklik kaydında geri alınabilir bir diff, önizleme → onay. Yıkıcı işlemlerde ayrıca onay.
- Bas-konuş sesli komut + yazılı alternatif.

### Faz 5: B2B / robotik / genişleme (pilot müşteriyle)
- Çoklu görsel/video girişi, PDF kılavuzdan parça listesi.
- Robot eğitimi için aynı tıkla-etiketle akışı: insan parçaya tıklar ve adlandırır ("pil", "ekran"), sistem 3D'ye çevirir. Etiketli 3D parçalar doğrudan simülasyon ve eğitim verisi olur.
- Parça etiketleme, MJCF/USD export, sentetik veri (ışık, kamera ve doku varyasyonları + otomatik etiketler).
- Dışa açık API/SDK (hedef platform seçilerek).
- İsteğe bağlı: LED ekran / Unreal bağlantısı (Cuebric tarzı).

---

## 7. Değerlendirme

- `eval/` altında lisansı temiz ~50 test görseli (iç mekan, dış mekan, ürün, karakter).
- **Metrikler:**
  - Maske IoU.
  - **Yeniden projeksiyon tutarlılığı:** orijinal kameradan render ile giriş görseli karşılaştırılır (PSNR/LPIPS).
  - Hizalamada silüet IoU ve derinlik hatası.
  - İlk seferde onay oranı.
  - Adım başı GPU süresi, uçtan uca GPU süresi.
- Her model veya adaptör değişikliğinde aynı set otomatik koşar ve bir regresyon raporu üretilir.

---

## 8. Riskler ve açık sorular

**Riskler**
- **Tek görselden 3D sınırlıdır.** Görünmeyen yüzler tahmindir. Çözüm: onay/yeniden üret akışı, ileride çoklu görsel.
- **Hizalama** en zor kısım. Faz 2'nin en büyük kalemi.
- **TRELLIS son işlemesinin yeniden yazılması** (nvdiffrast olmadan doku basma) kaliteyi düşürebilir ve zaman alır. Faz 0'da prototiplenip ölçülür.
- **Mesh ve splat'ı aynı sahnede doğru sıralamak zor.** Ana format mesh; splat yalnızca önizleme.
- **Tek GPU:** süre uzun, eşzamanlı kullanıcı neredeyse yok. Geliştirme için yeterli.
- **SAM 2 tıklamaları tarayıcıya taşınırsa** her görsel için 10–16 MB öznitelik verisi indirilir. Önce sunucuda kalır.
- **Kapalı video API'leri** girdi formatlarını değiştirebilir. Ürünün değeri açık modelle kanıtlanabilir olmalı.

**Açık sorular**
1. RTX 4000'in tam modeli (20 GB Ada mı, 8 GB Turing mi)?
2. İlk hedef kullanıcı kim: bireysel AI video üreticileri mi, stüdyo ön görselleştirme ekipleri mi? Faz 1–3 önceliklerini bu belirler.
3. Ekip büyüklüğü?
4. SAM 3D Objects ve DINOv3 lisansları okunup kabul edilebilir bulunursa hizalama ve TRELLIS.2 planı değişir.
5. `LICENSE` için tüzel kişi adı, iletişim adresi ve geçerli hukuk (hangi ülke)?

---

## Ek A: Evren'in olası 12 adımı (tahmin)

Podcast'te yalnızca Meta'nın Segment Anything'i adıyla geçiyor. "12 inference", aynı modelin birden çok kez çağrıldığı 12 adım da olabilir. Evren bir girişim olarak kapalı API'leri rahatça kullanabilir; biz yalnızca ticari lisanslı açık modelleri kullanıyoruz.

| # | Adım | Evren'in muhtemelen kullandığı | Bizim karşılığımız |
|---|---|---|---|
| 1 | Sahne anlama | Gemini / GPT / Claude | Claude API / Qwen2.5-VL-7B |
| 2 | Etiketten yer bulma | Grounding DINO / Florence-2 | Grounding DINO |
| 3 | Segmentasyon (Meta) | SAM 2, büyük ihtimalle SAM 3 (yazıyla maske verir) | SAM 2.1 |
| 4 | Maske kenarı | BiRefNet / RMBG | BiRefNet (RMBG-2.0 ticari yasak) |
| 5 | Derinlik + kamera | Depth Pro / MoGe / Depth Anything / VGGT | MoGe-2 |
| 6 | Kesik obje tamamlama | Gemini Image / FLUX Kontext / GPT-Image / Qwen-Image-Edit | Qwen-Image-Edit-2509 |
| 7 | Arka plan doldurma | FLUX Fill / aynı düzenleme modeli | LaMa / Qwen-Image-Edit |
| 8 | Obje görüntüsünü büyütme | Real-ESRGAN / Magnific / Topaz | Real-ESRGAN (lisans ⏳) |
| 9 | Obje → 3D | Hunyuan3D / TRELLIS / Tripo / Meshy / Rodin / SAM 3D Objects | TRELLIS v1 |
| 10 | Arka plan → 3D (splat) | World Labs Marble / katmanlı splat | Kendi derinlik mesh'imiz + gsplat |
| 11 | Sahneye yerleştirme | SAM 3D Objects / kendi optimizasyonları | Kendi hizalama motorumuz |
| 12 | Ajan / orkestrasyon | Kapalı LLM | Claude tool use |

Tahmin: Meta'nın Kasım 2025'te çıkardığı **SAM 3D Objects**, Evren'in demosuna çok benziyor: objeyi seç, örtülü kısmı tamamla, 3D'ye çevir, sahnedeki konumunu tahmin et. Bu doğruysa 3, 9 ve 11 numaralı adımların büyük kısmını o model yapıyor olabilir.
