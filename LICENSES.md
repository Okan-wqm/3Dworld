# Dış Bileşen Lisans Kaydı

> **Bu projenin kendi lisansı:** [`LICENSE`](LICENSE) (*3Dworld Evaluation License*). Yalnızca test ve değerlendirme amaçlıdır, ticari kullanım yasaktır. Bu dosya ise **dışarıdan aldığımız** bileşenlerin lisanslarını listeler. Onları ticari kullanıma uygun seçmeye devam ediyoruz, böylece ileride ticari sürüme geçmek istersek engel çıkmaz.

**Kural:** Projeye dışarıdan giren her model, kütüphane ve servis **ticari kullanıma uygun** olmalı. Bir bileşen bu listede ✅ olmadan koda veya sunucuya eklenmez.

- **İzinli lisanslar:** MIT, Apache-2.0, BSD-2/3-Clause, ISC, Zlib, HPND, MPL-2.0 (dosya bazlı copyleft; değiştirilen MPL dosyaları MPL olarak kalır ve açılır).
- **İstisna listesi** (adıyla onaylananlar, başkası değil):
  - `easydict`: LGPL-3.0, TRELLIS kullanıyor. Değiştirilmeden, ayrı paket olarak import edilir.
  - `opencv-python-headless`: Apache-2.0, ama tekerleği FFmpeg'in LGPL derlemesini ayrı `.so` dosyaları olarak içeriyor (libavcodec vb.). MoGe import ediyor. Değiştirilmeden, dinamik bağlı kullanılır.
  - `ffmpeg-next`: WTFPL. Yalnızca FFmpeg'in LGPL derlemesiyle kullanılabilir, varsayılan olarak kullanılmıyor.
- **Yasak:**
  - Ticari kullanımı yasaklayan (NC) ve "yalnızca araştırma" lisansları.
  - AGPL.
  - Koda gömülen veya dağıtılan GPL.
  - Gelir veya kullanıcı sayısı eşiği olan, ya da bölge kısıtlı özel lisanslar.
- **Özel lisanslar** (ör. Meta SAM License, DINOv3 License): okunmadan ve bu dosyaya gerekçesiyle yazılmadan kullanılmaz.
- **Kapalı API'ler** (Claude, Veo, Seedance vb.): lisans değil, servis koşulları (ToS) geçerli. Ticari kullanım ve çıktı hakları maddesi kontrol edilip buraya not edilir.

**Kontrol:**
- Tarih: **2026-11-21**.
- Kaynaklar: Hugging Face model kartındaki `license` alanı, GitHub'daki `LICENSE` dosyası ve crates.io.
- 4 bağımsız incelemeden geçti.
- Lisanslar sürüm değiştikçe değişebilir, yeni sürüme geçerken yeniden kontrol edilir.
- Bu kayıt hukuki görüş değildir.

---

## ✅ Onaylı modeller (ağırlıklar)

| Bileşen | Kullanım | Lisans | Not |
|---|---|---|---|
| `facebook/sam2.1-hiera-large` (Meta SAM 2.1) | Segmentasyon | Apache-2.0 | |
| `IDEA-Research/grounding-dino-base` | Etiketten kutu | Apache-2.0 | |
| `google/owlv2-base-patch16-ensemble` | Etiketten kutu (yedek) | Apache-2.0 | |
| `microsoft/Florence-2-large` | Etiketleme / kutu (yedek) | MIT | |
| `Qwen/Qwen2.5-VL-7B-Instruct` | Sahne anlama (kendi makinemizde) | Apache-2.0 | 3B sürümünün lisans alanı boş, **kullanılmaz** |
| `facebook/dinov2-*` | Görsel öznitelik (TRELLIS v1 kullanıyor) | Apache-2.0 | |
| `ZhengPeng7/BiRefNet` | Maske kenarı, arka plan silme | MIT | |
| `Ruicheng/moge-2-vitl` (MoGe-2) | Derinlik + kamera (metrik) | MIT | v1 metrik ölçek vermez, MoGe-2 kullanılır |
| `depth-anything/Depth-Anything-V2-Small` | Göreli derinlik (yedek) | Apache-2.0 | Yalnızca Small |
| `Qwen/Qwen-Image-Edit`, `Qwen/Qwen-Image-Edit-2509` | Tamamlama, doldurma | Apache-2.0 | |
| `QuantStack/Qwen-Image-Edit-GGUF` | 4-bit sürüm (20 GB GPU için) | Apache-2.0 | |
| `lightx2v/Qwen-Image-Lightning` | 4–8 adımda hızlı üretim | Apache-2.0 | |
| LaMa (`advimman/lama`) | Hızlı arka plan doldurma | Apache-2.0 | |
| `JosephCatrambone/big-lama-torchscript` | LaMa'nın TorchScript dönüşümü (yalnızca PyTorch gerektirir) | Apache-2.0 | Üçüncü taraf dönüşümü; kaynak advimman/lama |
| `facebook/sam2.1-hiera-small` | Segmentasyon (CPU'da hızlı) | Apache-2.0 | |
| `microsoft/TRELLIS-image-large` (v1) | Obje → 3D | MIT (model + kod) | ⚠️ Kurulum bağımlılıkları aşağıda yasaklı. Girdi **RGBA** verilir, rembg devreye girmez |
| `stabilityai/TripoSR` | Hızlı obje → 3D (yedek) | MIT | Stability'nin diğer 3D modelleri (SF3D, SPAR3D) yasaklı |
| `Wan-AI/Wan2.1-VACE-1.3B`, `Wan-AI/Wan2.1-VACE-14B` | Kontrollü video | Apache-2.0 | 14B, 20 GB'a sığmaz. HF kartında "zararlı içerik paylaşma" kullanım maddesi var, engelleyici değil |
| `Wan-AI/Wan2.1-T2V-1.3B`, `alibaba-pai/Wan2.1-Fun-1.3B-Control` | Video (yedek) | Apache-2.0 | |
| `Wan-AI/Wan2.2-TI2V-5B` | Video (kontrolsüz) | Apache-2.0 | VACE kontrolü almaz |
| `zai-org/CogVideoX-2b` | Video (yedek) | Apache-2.0 | 5B sürümü yasaklı |

## ✅ Onaylı kod / kütüphaneler

| Bileşen | Kullanım | Lisans |
|---|---|---|
| PyTorch | Model çalıştırma | BSD-3-Clause |
| sam2 (facebookresearch) | SAM 2 kodu | Apache-2.0 |
| GroundingDINO | Kod | Apache-2.0 |
| MoGe (microsoft) + utils3d | Kod | MIT |
| TRELLIS (microsoft) | Kod (yasaklı bağımlılıklar olmadan) | MIT |
| rembg + U²-Net | TRELLIS import ediyor (RGBA girdide çalışmaz) | MIT / Apache-2.0 |
| VACE (`ali-vilab/VACE`) | Kod | Apache-2.0 (`LICENSE.txt`) |
| Wan2.1 / Wan2.2 | Kod | Apache-2.0 |
| kaolin (NVIDIA) | FlexiCubes, 3D yardımcıları | Apache-2.0 |
| spconv | Sparse conv | Apache-2.0 |
| flash-attention | Attention çekirdeği | BSD-3-Clause |
| PyTorch3D | Diferansiyellenebilir render, doku basma | BSD-3-Clause |
| gsplat (nerfstudio) | Gaussian splat (Faz 2+) | Apache-2.0 |
| xatlas | UV açma | MIT |
| MuJoCo | Robotik (Faz 5) | Apache-2.0 |
| three.js, React Three Fiber, drei | Web 3D | MIT |
| React, Next.js, Zustand | Web arayüz | MIT |
| Spark (sparkjsdev) | Web splat önizleme | MIT |
| GaussianSplats3D (mkkellogg) | Web splat önizleme (yedek) | MIT |
| PostgreSQL | Veritabanı + iş kuyruğu | PostgreSQL License (BSD benzeri) |
| SeaweedFS | S3 uyumlu depolama (opsiyonel) | Apache-2.0 |
| Pillow | Görsel G/Ç | HPND (MIT-CMU) |
| NumPy, SciPy | Sayısal işlemler | BSD-3-Clause |
| huggingface_hub | Ağırlık indirme (ayna üzerinden) | Apache-2.0 |
| hydra-core, omegaconf, iopath | SAM 2 bağımlılıkları | MIT / BSD-3-Clause / MIT |
| jsonschema (+ referencing, rpds-py, attrs) | Şema sözleşme testleri | MIT |
| pytest | Testler | MIT |
| ruff | Python lint/format | MIT |
| mypy (+ mypy_extensions, librt) | Python tip kontrolü | MIT |
| pathspec | mypy bağımlılığı | MPL-2.0 |
| maturin | Rust → Python derleme | MIT OR Apache-2.0 |

## ✅ Onaylı Rust crate'leri (crates.io, son sürüm)

| Crate | Kullanım | Lisans |
|---|---|---|
| axum, tower-http | HTTP API | MIT |
| tokio | Async runtime | MIT |
| tonic | gRPC (gerekirse) | MIT |
| serde | Serileştirme | MIT OR Apache-2.0 |
| sqlx | PostgreSQL (kuyruk dahil) | MIT OR Apache-2.0 |
| redis | Önbellek (gerekirse) | BSD-3-Clause |
| utoipa | OpenAPI üretimi | MIT OR Apache-2.0 |
| pyo3, maturin, numpy | Rust ↔ Python | MIT OR Apache-2.0 / BSD-2-Clause (numpy crate) |
| wasm-bindgen | Rust → tarayıcı | MIT OR Apache-2.0 |
| glam | Vektör/matris | MIT OR Apache-2.0 |
| nalgebra | Lineer cebir | Apache-2.0 |
| parry3d | Geometri sorguları | Apache-2.0 |
| kiddo, rstar | KD-tree / R-tree | MIT OR Apache-2.0 |
| rayon | Paralellik | MIT OR Apache-2.0 |
| meshopt | Mesh sadeleştirme (yalnızca sunucu) | MIT OR Apache-2.0 |
| gltf | glTF okuma/yazma | MIT OR Apache-2.0 |
| ply-rs | PLY | MIT |
| xatlas-rs | UV açma (yalnızca sunucu) | MIT |
| image | Görsel G/Ç | MIT OR Apache-2.0 |
| ort | ONNX Runtime (ileride) | MIT OR Apache-2.0 |
| candle-core, burn | Rust'ta model çıkarımı (ileride) | MIT OR Apache-2.0 |
| rav1e | AV1 video kodlama (telifsiz) | BSD-2-Clause |
| openh264 | H.264 kodlama | BSD-2-Clause. ⚠️ H.264 patent ücreti ayrı: Cisco'nun hazır binary'si kullanılırsa Cisco öder |
| cargo-deny, cargo-about | Lisans kontrolü, bildirim dosyası üretimi | MIT OR Apache-2.0 |

`apalis` iş kuyruğu **kaldırıldı**: işleri Rust'a özgü formatta sakladığı için Python worker'ları okuyamıyor. Yerine PostgreSQL `SKIP LOCKED` kuyruğu kullanılıyor.

## ⏳ Kontrol edilecek (eklenmeden önce)

| Bileşen | Neden |
|---|---|
| `microsoft/TRELLIS.2-4B` | Kendisi MIT, ama **DINOv3** (Meta özel lisansı: ticari kullanıma izin veriyor, fakat ihracat/ITAR yasakları, tazminat maddesi ve fesih hakkı var) üzerine eğitilmiş, değiştirilemez. Varsayılan olarak RMBG-2.0 (yasaklı) yüklüyor; BiRefNet ile değiştirilmeli. DINOv3 şartları okunup kabul edilene kadar beklemede |
| `facebook/sam3`, `facebook/sam-3d-objects` | Meta SAM License, ticari maddeleri okunmadı |
| Metric3D v2 | HF'de lisans alanı yok, README ticari kullanım için iletişim istiyor |
| Real-ESRGAN | Kod BSD-3; kullanılacak ağırlıkların lisansı kontrol edilmeli |
| imageio-ffmpeg | Paket BSD-2 ama tekerlekleri **GPL FFmpeg** binary'si içeriyor. Kullanılırsa PyAV + LGPL FFmpeg ile değiştirilmeli |
| Wan2.2-VACE-Fun-A14B | Apache-2.0 görünüyor, ama 20 GB'a sığmaz. Gerekirse ayrıntılı kontrol |
| Claude API, Veo, Seedance, Kling, Runway | Her birinin ToS'unda ticari kullanım ve çıktı hakları maddesi |

## ❌ Yasak, kullanılmayacak

| Bileşen | Lisans / sorun | Yerine |
|---|---|---|
| **nvdiffrast** (NVlabs) | NVIDIA Source Code License: *"research or evaluation purposes only"*. TRELLIS ve TRELLIS.2 kurulumu getiriyor | PyTorch3D veya kendi rasterizer'ımız |
| **nvdiffrec** | NVIDIA Source Code License. TRELLIS.2 PBR render için kullanıyor | Kendi PBR doku basma kodumuz |
| **diffoctreerast** | Inria türevi: *"cannot use … for commercial purposes"*. TRELLIS v1 getiriyor | TRELLIS'in mesh yolu + kaolin |
| **mip-splatting / Inria `diff-gaussian-rasterization`** | Inria lisansı, ticari yasak. TRELLIS v1 getiriyor | gsplat (Apache-2.0) |
| **pymeshfix** | GPL-3.0 (PyPI'de AGPL-3). TRELLIS v1 son işleme | Kendi mesh temizleme kodumuz |
| **igraph** (python-igraph) | GPL-2. TRELLIS v1 son işleme | Kendi kodumuz |
| **plyfile** | GPL-3.0. TRELLIS v1 ve TRELLIS.2 (o-voxel) | Rust PLY yazıcımız (ply-rs, MIT) |
| **briaai/RMBG-2.0**, RMBG-1.4 | CC BY-NC-4.0 / Bria lisansı. TRELLIS.2 varsayılan olarak yüklüyor | BiRefNet (MIT) |
| `depth-anything/Depth-Anything-V2-Base/Large/Giant` | CC-BY-NC-4.0 | V2-Small veya MoGe-2 |
| Hunyuan3D 2.x, HunyuanWorld | Tencent lisansı: bölge kısıtı + kullanıcı eşiği | TRELLIS |
| Stable Fast 3D, SPAR3D, SD3.x | Stability Community License (gelir eşiği) | TRELLIS / Qwen-Image-Edit |
| FLUX.1 dev / Fill / Kontext dev | Ticari yasak ağırlıklar | Qwen-Image-Edit |
| Ultralytics YOLOv8/11 | AGPL-3.0 | Grounding DINO / OWLv2 |
| MinIO | AGPL-3.0 | Yerel disk / R2 / SeaweedFS |
| CogVideoX-5B, LTX-Video | Özel lisans / gelir eşiği | Wan + VACE |
| VGGT (orijinal) | Ticari yasak | MoGe-2 |
| Blender | GPL. Koda gömülmez, dağıtılmaz | Kendi yazıcılarımız. Yalnızca geliştiricinin elle kontrol aracı olarak kullanılabilir |
| Autodesk FBX SDK | Kapalı lisans | GLB/OBJ/USD, ileride kendi ikili FBX yazıcımız |

> **TRELLIS uyarısı:** TRELLIS kodu ve ağırlıkları MIT, ama resmi `setup.sh` yukarıdaki yasaklı paketleri kuruyor. Worker imajında bunlar **kurulmuyor**. Mesh çıkarma, doku basma, mesh temizleme ve PLY yazma adımlarını kendimiz yazıyoruz (PyTorch3D, kaolin, Rust `geom-core`).

## Süreç

1. **Yeni bileşen:** Bu dosyaya satır eklenir (lisans, sürüm/commit, kaynak, tarih).
Şu an otomatik çalışanlar (`make licenses` ve CI):

2. **Rust paketleri:** `cargo-deny` (izinli liste `deny.toml`'da, bu dosyayla aynı). İzinli liste dışında bir lisans varsa build kırılır.
3. **Kara liste:** `scripts/check_blacklist.py`; bağımlılık dosyalarında, betiklerde, Makefile'da ve CI iş akışlarında yasaklı paket adı geçerse build kırılır: `nvdiffrast`, `nvdiffrec`, `diffoctreerast`, `diff-gaussian-rasterization`, `mip-splatting`, `pymeshfix`, `igraph`, `plyfile`, `ultralytics`, `imageio-ffmpeg`, RMBG.
4. **Ağırlıklar:** Paket kontrolüne görünmezler, bu yüzden ayrıca yönetilir:
   - Tek indirme yolu `workers.common.weights.fetch()`. Yalnızca `weights/allowlist.txt`'deki kimlikleri yükler, `weights/revisions.txt`'de sabitlenen sürümü indirir.
   - `workers/tests/test_licenses.py`: izin listesindeki her model burada ✅ olmalı, koddaki her model kimliği izin listesinde ve sürümü sabitlenmiş olmalı.
   - `HF_HUB_OFFLINE` varsayılan olarak açık **değil**: henüz ağırlık aynası yok, yeni bir oturum ilk çalıştırmada indirebilmeli. Ağırlıklar önbelleğe alındıktan sonra elle açılabilir.
5. **Python paketleri:** sürümler `requirements/` altında sabit. Python lisans taraması (`pip-licenses`) henüz otomatik değil; yeni paket bu dosyaya elle işlenir.

Planlanan (henüz yok): npm için `license-checker` (web editörü gelince), `THIRD_PARTY_NOTICES.md`'nin `cargo-about` ile otomatik üretimi, kendi ağırlık aynamız, sabit sürümlü Docker imajları.
