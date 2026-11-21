# 3Dworld — Ürün ve Teknik Plan

> Hedef: Tek bir 2D görseli **anlayan**, parçalara ayıran, her objeyi ve arka planı **3D'ye çeviren**, kullanıcının tarayıcıda düzenleyebildiği bir sahne kuran ve bu sahneden **üretken video modellerini kontrol eden** (kamera, düzen, derinlik) bir "planlama + kontrol katmanı".
>
> Kısıt: **Lisans derdi olmasın** → yalnızca ticari kullanıma açık (MIT / Apache-2.0 / BSD) model ve kütüphaneler. Kapalı servisler (Veo, Seedance, Kling, Runway…) sadece opsiyonel API adaptörü olarak; onlarda bağlayıcı olan lisans değil, servis koşulları (ToS).
>
> **Kesin kural:** Dışarıdan kullanılan her parça ticari kullanıma uygun lisanslı olmalı. Doğrulanmış liste, yasaklılar ve gerekçeleri [`LICENSES.md`](LICENSES.md) dosyasında (2026-11-21'de model kartları ve LICENSE dosyalarından kontrol edildi). Listede ✅ olmayan hiçbir şey koda girmez. Bu hukuki danışmanlık değildir.

---

## 0. Sahiplik stratejisi — "ne kadarı bizim yazılımımız?"

%100 sıfırdan (kendi eğittiğimiz modellerle) başlamak gerçekçi değil: segmentasyon, derinlik, görselden 3D ve video modelleri milyonlarca görsel ve milyon dolarlık GPU bütçesiyle eğitiliyor. Evren de bunu yapmıyor; ellerindeki 12 modelin biri Meta'nın Segment Anything'i. Değeri yaratan şey modeller değil, onları birleştiren katman (podcast'teki "anlama / planlama / kontrol katmanı").

Bu yüzden üç katmanlı ilerliyoruz:

| Katman | Ne | Sahiplik |
|---|---|---|
| **A — %100 bizim kodumuz** | Sahne grafiği, orkestrasyon ve ajan, **hizalama** (asıl zor kısım), 2.5D katman/derinlik mesh'i, splat/mesh görüntüleyici, editör, kamera yolu, render pass'leri, kredi (token) sistemi, glTF/OBJ/USD yazıcıları | Tamamen bizim |
| **B — Açık ağırlıklı modeller, kendi sunucumuzda** | SAM 2 (Meta, Apache-2.0), MoGe, TRELLIS, LaMa, Wan… | Ağırlıkların kopyası bizde. Dış API'ye, kullanım ücretine ya da lisans ücretine bağımlılık yok. Değiştirip ince ayar yapabiliriz. |
| **C — Kendi eğittiğimiz modeller (ileride)** | Kullanıcı düzeltmelerinden biriken veriyle B'deki modellerin ince ayarlı ya da damıtılmış (distill) sürümleri | Tamamen bizim |

Kural: Katman B'deki her model bir adaptör arkasında durur. Sonradan kendi modelimizi yazdığımızda (Katman C) sadece adaptör değişir, ürünün geri kalanı etkilenmez.

**Meta modelleri:** SAM 2 / 2.1 (Apache-2.0) ve DINOv2 (Apache-2.0) güvenle kullanılabilir. SAM 3 ve SAM 3D Objects daha güçlü ama Meta'nın kendi "SAM License"ı ile geliyor. Eklemeden önce ticari kullanım maddelerini okuyun. VGGT'nin orijinal sürümü ticari kullanıma kapalı.

---

## 0.1 Podcast'teki özelliklerin bizim planımızdaki karşılığı

| # | Özellik (Evren) | Bizde nasıl | Katman | Faz |
|---|---|---|---|---|
| 1 | Tek görselden başlama | Yükleme + ön işleme | A | 1 |
| 2 | Görseli anlama ("seni anladım") | VLM etiketleme → obje listesi | B (LLM/VLM) | 1 |
| 3 | Segmentasyon | Grounding DINO + **SAM 2 (Meta)** | B | 1 |
| 4 | Onay / düzeltme ("oyuncak → saman") | Etiket düzenleme arayüzü; düzeltilen etiket sonraki adımlara prompt olarak gider | A | 1 |
| 5 | Kesik objeyi tamamlama | Amodal tamamlama (Qwen-Image-Edit) | B | 2 |
| 6 | Arka planı tamamlama | LaMa / Qwen-Image-Edit inpaint | B | 1 |
| 7 | Yeniden üretme | Her adımda seed değiştirerek yeniden çalıştırma + sürüm geçmişi | A | 1 |
| 8 | Token onayı | Adım başı GPU-saniye tahmini → kredi göster → onay al | A | 2 |
| 9 | Her objeyi ayrı 3D'ye çevirme | TRELLIS (MIT) | B | 2 |
| 10 | Arka planı 3D'ye çevirme | Derinlik + inpaint → depth mesh / gsplat | A (+B derinlik) | 1–2 |
| 11 | Sahneyi bire bir birleştirme, splat gösterimi | **Hizalama motoru + kendi WebGL splat görüntüleyicimiz** | A | 2 |
| 12 | ~15 dk | Paralel worker'lar, önbellek, önizleme/yüksek kalite ayrımı | A | 2 |
| 13 | 12 modelli altyapı | Adaptör arayüzü + iş kuyruğu | A | 0 |
| 14 | Ajan mimarisi | Sahne grafiği üzerinde tipli araçlar | A (+LLM) | 4 |
| 15 | Video modelleri için yerleşim referansı | Kamera yolu → RGB/depth/kenar render → video modeline koşul | A | 3 |
| 16 | Çoklu girdi | Çoklu görsel/video → daha tutarlı geometri | A+B | 5 |
| 17 | Konuşarak düzenleme | Ajan + (opsiyonel) konuşmayı yazıya çevirme | A+B | 4 |
| 18 | Uçtan uca prodüksiyon | Wan + VACE ile kendi sunucumuzda video üretimi | B | 3 |
| 19 | 2D platformlara entegrasyon | Dışarıya açık API + SDK | A | 5 |
| 20 | Robot eğitimi | Parça etiketleme, MJCF/USD export, sentetik veri | A | 5 |
| 21 | Robotların insanları eğitmesi | Henüz tanımsız (Evren'de de öyle), sonraya bırak | — | — |
| Cuebric | 2.5D katmanlar + mesh export | Faz 1 MVP tam olarak bu. FBX: Autodesk SDK yerine kendi ASCII-FBX yazıcımızla ileride eklenebilir | A | 1 |

---

## 1. Ürün ne yapıyor? (podcast'teki demodan çıkarılan akış)

1. **Anla** — Görseli yükle; sistem "ahır, at, saman, kovboy botu…" diye obje listesi çıkarır. Kullanıcı düzeltir ("oyuncak değil, saman").
2. **Ayır** — Her obje maskelenir (segmentasyon).
3. **Tamamla** — Kadrajda kesilmiş/örtülmüş objeler tamamlanır (amodal completion); objeler çıkınca arka plandaki boşluk doldurulur (inpainting). Her adımda "Doğru mu?" → onay / yeniden üret.
4. **3D'ye çevir** — Her obje ayrı 3D asset olur; arka plan 3D/2.5D zemin olur; hepsi orijinal kameraya göre doğru yere, doğru ölçekte yerleşir. **Orijinal kameradan bakınca sahne giriş görseliyle bire bir örtüşmeli.**
5. **Düzenle** — Tarayıcıda objeleri taşı/döndür, ışık ekle, kamera yolu çiz.
6. **Kontrollü render** — Kamera yolundan depth / normal / kenar / "clay" render pass'leri üret → üretken video modeline koşul olarak ver → model kamerayı ve düzeni halüsine etmez.
7. **Ajan** (sonraki faz) — "Işığı atın üstüne koy", "kamerayı alçalt" gibi komutlar sahne grafiği üzerinde fonksiyon çağrılarına dönüşür.
8. **B2B / robotik** (keşif fazı) — Aynı sahne grafiği → etiketli 3D parçalar, simülasyon/sentetik veri export'u.

---

## 2. Pipeline mimarisi

```
 Görsel
   │
   ▼
[1] Sahne anlama (VLM) ──► obje listesi + etiketler (JSON)  ◄── kullanıcı düzeltmesi
   │
   ▼
[2] Lokalizasyon + segmentasyon ──► obje maskeleri
   │
   ├──────────────────────────────┐
   ▼                              ▼
[3] Geometri + kamera          [4] Amodal tamamlama (obje başına)
   (point map, FOV, ölçek)        [5] Arka plan inpainting
   │                              │
   │                              ▼
   │                        [6] Obje → 3D asset (GLB / splat)
   │                        [7] Arka plan → 2.5D/3D zemin
   │                              │
   └──────────────┬───────────────┘
                  ▼
[8] Hizalama: ölçek + poz (silüet render-and-compare + ICP, zemin düzlemi)
                  │
                  ▼
        scene.json + glTF asset'ler  (tek doğruluk kaynağı: sahne grafiği)
                  │
                  ▼
[9] Web editör (three.js) ── kamera yolu, ışık, gizmo'lar
                  │
                  ▼
[10] Render pass'leri: RGB önizleme, depth, normal, kenar, obje-ID
                  │
                  ▼
[11] Üretken video adaptörleri:  açık model (Wan + VACE)  |  kapalı API'ler
```

Her model bir **adaptör** arkasında durur (`segment()`, `estimate_geometry()`, `image_to_3d()`…). Yeni/ daha iyi model çıktığında sadece adaptör değişir — podcast'teki "12 inference, plug-and-play" yapısı budur.

---

## 3. Bileşen seçimi (ticari kullanıma uygun)

| Adım | Birincil seçim | Lisans | Yedek / not |
|---|---|---|---|
| 1. Sahne anlama | Claude API (tool use, JSON çıktı) | API ToS | Self-host: Qwen2.5-VL-7B (Apache-2.0), Florence-2 (MIT) |
| 2a. Etiketten kutu | Grounding DINO | Apache-2.0 | OWLv2 (Apache-2.0), Florence-2 (MIT) |
| 2b. Maske | SAM 2 / 2.1 | Apache-2.0 | Kenar iyileştirme: BiRefNet (MIT) |
| 3. Derinlik + kamera | MoGe / MoGe-2 (point map + FOV) | MIT (doğrula) | Depth Anything V2 **Small** (Apache-2.0), Metric3D v2 (BSD-2) |
| 4. Amodal tamamlama | Qwen-Image-Edit | Apache-2.0 | Qwen-Image-Edit-2509 (Apache-2.0) |
| 5. Arka plan inpaint | LaMa (hızlı) | Apache-2.0 | Kalite için Qwen-Image-Edit |
| 6. Obje → 3D | TRELLIS / TRELLIS.2 | MIT | Hızlı/düşük kalite: TripoSR (MIT). ⚠️ alt bağımlılıklara bak (§4) |
| 7. Arka plan → 3D | Kendi kodumuz: inpaint + depth → katmanlı depth mesh | — | Splat optimizasyonu: gsplat (Apache-2.0) |
| 8. Hizalama | Open3D (ICP, RANSAC zemin) + PyTorch render-and-compare | MIT / BSD | PyTorch3D (BSD) diferansiyellenebilir render |
| 9. Editör | three.js + React Three Fiber + drei | MIT | Splat gösterimi: kendi WebGL görüntüleyicimiz (Katman A). Geçici yedek: Spark (MIT) |
| 10. Render pass | three.js shader'ları (depth/normal/ID) | MIT | Sunucu tarafı: headless Chromium + aynı kod |
| 11. Video (açık) | Wan 2.1 / 2.2 + VACE (depth/pose kontrol) | Apache-2.0 | CogVideoX-**2B** (Apache-2.0) |
| 11. Video (kapalı) | Veo, Seedance, Kling, Runway adaptörleri | Her birinin ToS'u | Opsiyonel; ürün bunlara bağımlı olmamalı |
| Export | glTF/GLB, OBJ, OpenUSD | MIT / Apache tarzı | FBX yok (Autodesk SDK kapalı) |
| Robotik (sonra) | MuJoCo (MJCF export) | Apache-2.0 | USD export |

---

## 4. Lisans tuzakları — bunlardan uzak dur

| Bileşen | Sorun | Ne yap |
|---|---|---|
| Depth Anything V2 Base/Large/Giant | CC BY-NC (ticari yasak) | Sadece **Small** veya MoGe |
| Hunyuan3D 2.x, HunyuanWorld | Tencent lisansı: AB/İngiltere/G.Kore hariç, kullanıcı sayısı eşiği | Kullanma |
| Stable Fast 3D, SPAR3D, SD3.x | Stability Community License (gelir eşiği) | Kullanma veya eşiği takip et |
| FLUX.1 dev / Fill / Kontext dev | Non-commercial ağırlıklar | Qwen-Image-Edit kullan |
| **nvdiffrast**, **nvdiffrec** | NVIDIA non-commercial lisans; TRELLIS ve TRELLIS.2 kurulumu bunları getiriyor (texture baking, PBR render) | Baking/render'ı PyTorch3D veya kendi rasterizer'ımızla yaz |
| **diffoctreerast**, mip-splatting / Inria `diff-gaussian-rasterization` | Inria lisansı, non-commercial; TRELLIS v1 kurulumu getiriyor | **gsplat** (Apache-2.0) |
| Ultralytics YOLOv8/11 | AGPL-3.0 | Grounding DINO / OWLv2 |
| MinIO (self-host depolama) | AGPL-3.0 | S3 / Cloudflare R2 / SeaweedFS (Apache-2.0) |
| SAM 3, SAM 3D | Meta'nın özel "SAM License"ı | Okumadan ekleme; SAM 2 güvenli |
| VGGT (orijinal) | Non-commercial (ticari varyantı ayrı lisans) | Gerekirse ticari varyantın şartlarını oku |
| CogVideoX-5B, LTX-Video | Özel lisanslar / gelir eşiği | Wan + VACE |
| Blender | GPL | Sunucuda ayrı süreç olarak çağırmak sorun değil; kodumuza gömme/dağıtma |
| Objaverse vb. eğitim verisi | Obje başına karışık lisans | Fine-tune yaparsan veri lisansını filtrele |

**Süreç kuralı:** `LICENSES.md` (model, sürüm/commit hash, lisans, link, kontrol tarihi) + CI'da `pip-licenses` ve `license-checker` (npm) ile GPL/AGPL/NC yakalayan bir kontrol. İzin listesi: MIT, Apache-2.0, BSD-2/3, ISC, MPL-2.0 (dosya bazlı), Zlib.

---

## 5. Teknoloji yığını

### 5.1 Rust nerede, Python nerede? (hız kuralı)

İlke: **Rust'ı CPU'da çalışan, yoğun ve uzun ömürlü kodda kullan. GPU'daki model çıkarımını Python/PyTorch'ta bırak.** Model çıkarımında süre zaten CUDA çekirdeklerinde geçiyor. TRELLIS, Qwen-Image-Edit veya Wan'ı Rust'a taşımak aylar sürer ve hız kazandırmaz. Asıl hız kazancı modellerin *arasındaki* işlerde: nokta bulutu, mesh, splat, hizalama ön adımları, video kodlama ve orkestrasyon.

| Alan | Dil | Neden |
|---|---|---|
| **API + orkestratör** (iş akışı, kuyruk, kredi, WebSocket ilerleme) | **Rust** (axum + tokio, sqlx, redis) | Düşük gecikme, tip güvenliği, tek binary. Python GIL derdi yok |
| **Geometri çekirdeği `geom-core`**: derinlik → nokta bulutu → mesh, 2.5D katmanlar, zemin RANSAC, ICP ön hizalama, mesh sadeleştirme, UV, splat sıkıştırma/dönüştürme, glTF/PLY/OBJ/USD(A)/ASCII-FBX yazıcıları | **Rust** (glam/nalgebra, parry3d, kiddo, rayon, meshopt, gltf) | En büyük hız kazancı burada: Python döngülerine göre 10–100×, rayon ile tüm çekirdekler |
| Aynı çekirdeğin Python'dan kullanımı | Rust → **PyO3 + maturin** | GPU worker'ları `geom_core` modülünü doğrudan çağırır, veri kopyalamadan (numpy) |
| Aynı çekirdeğin tarayıcıdan kullanımı | Rust → **WASM** (wasm-bindgen) | Splat derinlik sıralaması, 2.5D mesh üretimi, sahne grafiği diff/undo tarayıcıda hızlı. **Tek kod hem sunucuda hem tarayıcıda** |
| Hafif modellerin çıkarımı (SAM 2 decoder, derinlik, BiRefNet) | İleride **Rust + ort (ONNX Runtime)** | Python worker'a gitmeden hızlı etkileşim (tıkla → maske). Önce Python'da çalıştır, darboğaz olursa ONNX'e taşı |
| Video kodlama (render pass'leri → MP4/AV1) | **Rust** (rav1e AV1, openh264) | Hızlı ve lisans-temiz kodlama |
| Ağır modeller (TRELLIS, Qwen-Image-Edit, Wan, MoGe) + diferansiyellenebilir hizalama | **Python + PyTorch** | Modellerin kendi kodu bu. Port etmek kazanç değil |
| Editör arayüzü | **TypeScript** (React + three.js) | UI ekosistemi burada. Ağır hesap WASM'a gider |

Sınır kuralı: Rust ile Python arası sözleşme, `scene-schema` içinde tek kaynaktan üretilen tiplerle kurulur (Rust `serde` struct'ları → JSON Schema → TS ve Pydantic tipleri).

Lisans notları:
- Rust tarafında `cargo-deny` CI'da çalışır; izinli liste `LICENSES.md` ile aynı.
- **H.264 kodlamada patent konusu var:** openh264'ü kaynaktan derlersen patent ücreti sana düşer, Cisco'nun hazır binary'sinde Cisco öder. AV1 (rav1e) telifsizdir, varsayılan olarak AV1 kullanılır, H.264 isteğe bağlıdır.
- FFmpeg kullanılacaksa sadece LGPL derlemesi (`--enable-gpl` olmadan, x264'süz) ve dinamik bağlama.

### 5.2 Diğer bileşenler

- **Frontend:** Next.js + React + React Three Fiber + drei, durum yönetimi Zustand, gizmo'lar için `TransformControls`. Ağır hesaplar `geom-core` WASM modülünde.
- **API:** Rust (axum), PostgreSQL (sqlx), Redis tabanlı iş kuyruğu (apalis). Her pipeline adımı ayrı job; ilerleme WebSocket/SSE ile ön yüze akar. OpenAPI dokümanı utoipa ile üretilir.
- **GPU worker'lar:** Python. Kuyruktan iş alır, `geom_core` (PyO3) modülünü kullanır. Her model için ayrı Docker imajı (bağımlılık çakışmalarını önler). Modal / RunPod / Lambda üzerinde otomatik ölçeklenen worker'lar. Kaba VRAM: SAM 2 + MoGe ~8 GB, TRELLIS ~16 GB, Qwen-Image-Edit ~24 GB+ (quantize ile daha az), Wan 2.2 TI2V-5B ~24 GB, Wan 14B ~80 GB.
- **Depolama:** S3 uyumlu (R2/S3); asset'ler content-hash ile adreslenir (aynı obje yeniden üretilmez).
- **Sahne formatı:** Kendi `scene.json` şemamız (objeler, transform'lar, kamera intrinsics, ışıklar, kamera yolu, asset referansları, kullanıcı onay durumu) + glTF asset'ler. USD export sonradan.
- **LLM/ajan:** Claude API tool use; sahne grafiği üzerinde tipli fonksiyonlar.

### Önerilen repo yapısı

```
3Dworld/
  Cargo.toml             # Rust workspace
  crates/
    api/                 # Rust: axum API + orkestratör + kredi sistemi
    geom-core/           # Rust: geometri çekirdeği (saf Rust, test edilebilir)
    geom-py/             # Rust → Python bağlayıcısı (PyO3/maturin)
    geom-wasm/           # Rust → tarayıcı bağlayıcısı (wasm-bindgen)
    scene-schema/        # Rust serde tipleri → JSON Schema → TS/Pydantic
    encode/              # Rust: render pass → AV1/H.264 video
  apps/web/              # Next.js + R3F editör (geom-wasm'ı kullanır)
  workers/               # Python GPU worker'ları
    understand/          # VLM etiketleme
    segment/             # Grounding DINO + SAM 2
    geometry/            # MoGe / depth
    complete/            # amodal + inpaint
    to3d/                # TRELLIS (+ lisans-temiz baking)
    align/               # poz/ölçek hizalama
    video/               # Wan+VACE ve kapalı API adaptörleri
  eval/                  # test görselleri + metrik scriptleri
  LICENSES.md
  PLAN.md
```

---

## 6. Yol haritası

### Faz 0 — Temel (1–2 hafta)
- Lisans izin listesi + CI kontrolü (`cargo-deny`, `pip-licenses`, `license-checker`), `LICENSES.md`.
- Monorepo iskeleti: Rust workspace (`api`, `geom-core`, `geom-py`, `geom-wasm`, `scene-schema`), `scene.json` şeması v0, adaptör arayüzü.
- `geom-core` v0: derinlik haritası → nokta bulutu → üçgen mesh → GLB. Python'dan (PyO3) ve tarayıcıdan (WASM) çağrılabilir. Python/numpy referans uygulamasına karşı hız ölçümü.
- Bir GPU ortamında SAM 2, MoGe, TRELLIS'i ayrı ayrı çalıştırıp çıktıları doğrula.
- **Çıktı:** Komut satırından `görsel → maskeler + point map + bir obje GLB`.

### Faz 1 — 2.5D MVP (3–5 hafta) — en hızlı değer
- Yükle → etiketle → maskele → arka planı inpaint et → her obje bir **derinlikli kart/katman**.
- Tarayıcıda paralaks kamera hareketi, basit kamera yolu, MP4 + depth video export.
- Onay/yeniden üret akışı (her adımda "doğru mu?").
- **Başarı ölçütü:** 10 test görselinde < 3 dk, orijinal kameradan render ≈ giriş görseli.

### Faz 2 — Tam 3D (4–6 hafta)
- Amodal tamamlama → TRELLIS ile obje başına 3D asset (lisans-temiz texture baking dahil).
- Hizalama: maske silüeti + point map ile ölçek/poz optimizasyonu, zemin düzlemi, temas (objeler havada durmasın).
- Arka plan için depth mesh (+ opsiyonel gsplat splat).
- Editör: seç/taşı/döndür, ışık, asset değiştir ("bot" → "kovboy botu" yeniden üret).
- GLB / OBJ / USD export.
- **Başarı ölçütü:** Orijinal kameradan render ile giriş görseli arasında LPIPS/maske IoU hedefleri; uçtan uca < 15 dk.

### Faz 3 — Kontrollü video (3–4 hafta)
- Kamera yolu (keyframe, lens, hız eğrisi) → depth / normal / kenar / obje-ID / clay pass'leri.
- Wan + VACE ile pass'ler + referans görselden video üretimi.
- Kapalı API adaptörleri (ilk kare + kontrol videosu / video-to-video, hangisi destekliyorsa).
- Karakter/obje tutarlılığı için asset referans görsellerini her üretimde tekrar kullan.

### Faz 4 — Ajan katmanı (2–3 hafta)
- Claude tool use: `move_object`, `rotate_object`, `add_light`, `set_camera_path`, `regenerate_asset`, `relabel_object`…
- Her komut sahne grafiğinde geri alınabilir bir diff; editörde önizleme → onay.
- Kullanıcı düzeltmelerini (etiket, tamamlama seçimleri) kaydet → ileride değerlendirme/ince ayar verisi.

### Faz 5 — B2B / robotik keşfi (paralel, müşteri konuşmalarıyla)
- Çoklu görsel / video girişi (daha tutarlı geometri).
- Parça düzeyinde etiketleme ("telefon arka kapağı, pil, ekran") + montaj sırası notları.
- MJCF / USD export, sentetik veri üretimi (aynı sahneden ışık/kamera/doku varyasyonları + otomatik etiketler).
- Bu fazı ancak gerçek bir pilot müşteri ihtiyacı netleşince derinleştir.

---

## 7. Değerlendirme

- `eval/` altında lisansı temiz ~50 test görseli (iç mekan, dış mekan, ürün, karakter).
- Metrikler: maske IoU (elle etiketli alt küme), **yeniden projeksiyon tutarlılığı** (orijinal kameradan render vs giriş: PSNR/LPIPS), obje başına üretim başarısı (kullanıcı ilk seferde onayladı mı?), uçtan uca süre ve GPU maliyeti.
- Her model değişikliğinde aynı set otomatik koşar; adaptör değişimi bir regresyon raporu üretir.

---

## 8. Riskler ve açık sorular

- **Tek görselden 3D sınırlıdır:** görünmeyen yüzler halüsinasyon. Çözüm: onay/yeniden üret akışı + ileride çoklu görsel girişi.
- **Hizalama en zor ve en farklılaştırıcı kısım:** hazır modeller obje üretir, sahneyi bire bir kurmaz. Mühendislik zamanının büyük kısmını buraya ayır.
- **GPU maliyeti:** adım başına önbellek (content-hash), düşük çözünürlüklü önizleme → onaydan sonra yüksek kalite.
- **Kapalı video API'leri** kontrol girdisi formatlarını değiştirebilir; ürün değeri açık modelle (Wan + VACE) kanıtlanabilir olmalı.
- **Açık soru:** İlk hedef kullanıcı kim? (Bireysel AI video üreticileri mi, stüdyo previs ekipleri mi?) Faz 1–3 önceliklerini bu belirler.
