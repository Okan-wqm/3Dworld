# Dış Bileşen Lisans Kaydı

> **Bu projenin kendi lisansı:** [`LICENSE`](LICENSE): *3Dworld Evaluation License*. Yalnızca test ve değerlendirme amaçlıdır, ticari kullanım yasaktır. Bu dosya ise **dışarıdan aldığımız** bileşenlerin lisanslarını listeler. Onları ticari kullanıma uygun seçmeye devam ediyoruz, böylece ileride ticari sürüme geçmek istersek engel çıkmaz.

**Kural:** Projeye dışarıdan giren her model, kütüphane ve servis **ticari kullanıma uygun** olmalı. Bir bileşen bu listede ✅ olmadan koda eklenmez.

- **İzinli lisanslar:** MIT, Apache-2.0, BSD-2/3-Clause, ISC, Zlib, MPL-2.0 (dosya bazlı copyleft; değiştirilen dosyalar açılır)
- **Yasak:** Non-commercial (NC) lisanslar, "research only" lisanslar, AGPL, GPL (koda gömülü/dağıtılan), gelir veya kullanıcı eşikli özel lisanslar, bölge kısıtlı lisanslar
- **Özel lisanslar** (ör. Meta "SAM License"): okunmadan ve bu dosyaya gerekçesiyle yazılmadan kullanılmaz
- **Kapalı API'ler** (Claude, Veo, Seedance vb.): lisans değil servis koşulları (ToS) geçerli. Ticari kullanım ve çıktı hakları maddesi kontrol edilip buraya not edilir

Kontrol tarihi: **2026-11-21**. Kaynaklar: Hugging Face model kartındaki `license` alanı ve GitHub `LICENSE` dosyası. Lisanslar sürüm değiştikçe değişebilir. Yeni sürüme geçerken yeniden kontrol edin. Bu kayıt hukuki görüş değildir.

---

## ✅ Onaylı modeller (ağırlıklar)

| Bileşen | Kullanım | Lisans | Kaynak |
|---|---|---|---|
| `facebook/sam2.1-hiera-large` (Meta SAM 2.1) | Segmentasyon | Apache-2.0 | HF model kartı |
| `IDEA-Research/grounding-dino-base` | Etiketten kutu | Apache-2.0 | HF model kartı |
| `google/owlv2-base-patch16-ensemble` | Etiketten kutu (yedek) | Apache-2.0 | HF model kartı |
| `microsoft/Florence-2-large` | Etiketleme / kutu (yedek) | MIT | HF model kartı |
| `Qwen/Qwen2.5-VL-7B-Instruct` | Sahne anlama (self-host VLM) | Apache-2.0 | HF model kartı |
| `facebook/dinov2-large` | Görsel öznitelik | Apache-2.0 | HF model kartı |
| `ZhengPeng7/BiRefNet` | Maske kenarı iyileştirme | MIT | HF model kartı |
| `Ruicheng/moge-vitl`, `Ruicheng/moge-2-vitl` | Derinlik + kamera (FOV) | MIT | HF model kartı |
| `depth-anything/Depth-Anything-V2-Small` | Derinlik (yedek) | Apache-2.0 | HF model kartı |
| `Qwen/Qwen-Image-Edit`, `Qwen/Qwen-Image-Edit-2509` | Amodal tamamlama, inpaint | Apache-2.0 | HF model kartı |
| LaMa (`advimman/lama`) | Hızlı inpaint | Apache-2.0 | GitHub LICENSE |
| `microsoft/TRELLIS-image-large`, `microsoft/TRELLIS.2-4B` | Obje → 3D | MIT (model + kod) | HF + GitHub. ⚠️ alt bağımlılıklar aşağıda |
| `stabilityai/TripoSR` | Hızlı obje → 3D (yedek) | MIT | HF model kartı |
| `Wan-AI/Wan2.2-TI2V-5B` | Video üretimi | Apache-2.0 | HF model kartı |
| `Wan-AI/Wan2.1-VACE-1.3B`, `Wan-AI/Wan2.1-VACE-14B` | Kontrollü video (depth/pose) | Apache-2.0 | HF model kartı |

## ✅ Onaylı kod / kütüphaneler

| Bileşen | Kullanım | Lisans |
|---|---|---|
| sam2 (facebookresearch) | SAM 2 kodu | Apache-2.0 |
| GroundingDINO | Kod | Apache-2.0 |
| MoGe (microsoft) | Kod | MIT |
| TRELLIS, TRELLIS.2 (microsoft) | Kod | MIT |
| CuMesh, FlexGEMM, utils3d | TRELLIS.2 yardımcıları | MIT |
| Wan2.2 | Kod | Apache-2.0 |
| gsplat (nerfstudio) | Gaussian splat rasterizer / optimizasyon | Apache-2.0 |
| kaolin (NVIDIA) | 3D yardımcıları | Apache-2.0 |
| spconv | Sparse conv | Apache-2.0 |
| flash-attention | Attention çekirdeği | BSD-3-Clause |
| PyTorch3D | Diferansiyellenebilir render, texture baking | BSD |
| Open3D | ICP, RANSAC, nokta bulutu | MIT |
| xatlas | UV açma | MIT |
| three.js | Web 3D | MIT |
| Spark (sparkjsdev) | Web splat görüntüleyici (geçici yedek) | MIT |
| GaussianSplats3D (mkkellogg) | Web splat görüntüleyici (yedek) | MIT |
| MuJoCo | Robotik simülasyon / export (Faz 5) | Apache-2.0 |

## ✅ Onaylı Rust crate'leri (crates.io, son sürüm)

| Crate | Kullanım | Lisans |
|---|---|---|
| axum, tower-http | HTTP API | MIT |
| tokio | Async runtime | MIT |
| tonic | gRPC (gerekirse) | MIT |
| serde | Serileştirme | MIT OR Apache-2.0 |
| sqlx | PostgreSQL | MIT OR Apache-2.0 |
| redis | Redis istemcisi | BSD-3-Clause |
| apalis | İş kuyruğu | MIT OR Apache-2.0 |
| utoipa | OpenAPI üretimi | MIT OR Apache-2.0 |
| pyo3, maturin | Rust ↔ Python | MIT OR Apache-2.0 |
| wasm-bindgen | Rust → tarayıcı | MIT OR Apache-2.0 |
| glam | Vektör/matris | MIT OR Apache-2.0 |
| nalgebra | Lineer cebir | Apache-2.0 |
| parry3d | Geometri sorguları | Apache-2.0 |
| kiddo, rstar | KD-tree / R-tree | MIT OR Apache-2.0 |
| rayon | Paralellik | MIT OR Apache-2.0 |
| meshopt | Mesh sadeleştirme/optimizasyon | MIT OR Apache-2.0 |
| gltf | glTF okuma/yazma | MIT OR Apache-2.0 |
| ply-rs | PLY (splat/nokta bulutu) | MIT |
| xatlas-rs | UV açma | MIT |
| image | Görsel G/Ç | MIT OR Apache-2.0 |
| ort | ONNX Runtime bağlayıcısı | MIT OR Apache-2.0 |
| candle-core, burn | Rust'ta model çıkarımı (ileride) | MIT OR Apache-2.0 |
| rav1e | AV1 video kodlama (telifsiz) | BSD-2-Clause |
| openh264 | H.264 kodlama | BSD-2-Clause (⚠️ H.264 patent ücretleri ayrı konu; Cisco'nun hazır binary'si kullanılırsa Cisco öder) |
| cargo-deny | Lisans/güvenlik CI kontrolü | MIT OR Apache-2.0 |

`ffmpeg-next` (WTFPL) ancak FFmpeg'in LGPL derlemesiyle ve dinamik bağlamayla kullanılabilir. Varsayılan olarak kullanılmıyor.

## ⏳ Kontrol edilecek (eklenmeden önce)

| Bileşen | Neden |
|---|---|
| VACE kod reposu (`ali-vilab/VACE`) | Model ağırlıkları Apache-2.0 doğrulandı. Repo LICENSE dosyası bu kontrolde bulunamadı. Wan2.x içindeki VACE entegrasyonunu (Apache-2.0) kullanmak yeterli olabilir |
| `facebook/sam3`, `facebook/sam-3d-objects` | Lisans alanı "other" (Meta SAM License). Ticari maddeler okunmadan kullanılmaz |
| Claude API, Veo, Seedance, Kling, Runway | Her birinin ToS'unda ticari kullanım ve çıktı hakları maddesi |

## ❌ Yasak, kullanılmayacak

| Bileşen | Lisans / sorun | Yerine |
|---|---|---|
| **nvdiffrast** (NVlabs) | NVIDIA Source Code License: NVIDIA dışındakiler için *"non-commercially … research or evaluation purposes only"*. **TRELLIS ve TRELLIS.2 kurulumu bunu kuruyor** (GLB texture baking, render) | PyTorch3D (BSD) veya kendi rasterizer'ımız |
| **nvdiffrec** (NVlabs ve JeffreyXiang fork'u) | NVIDIA Source Code License. TRELLIS.2 PBR render için kullanıyor | Kendi PBR baking kodumuz |
| **diffoctreerast** (JeffreyXiang) | Inria lisansından türetilmiş: *"cannot use … for commercial purposes"*. TRELLIS (v1) kuruyor | TRELLIS.2 yolu veya gsplat |
| **mip-splatting / Inria gaussian-splatting rasterizer** | Inria Gaussian-Splatting License (non-commercial). TRELLIS (v1) kuruyor | gsplat (Apache-2.0) |
| `depth-anything/Depth-Anything-V2-Base/Large/Giant` | CC-BY-NC-4.0 (Large doğrulandı) | V2-Small veya MoGe |
| Hunyuan3D 2.x, HunyuanWorld | Tencent lisansı: bölge kısıtı + kullanıcı eşiği | TRELLIS |
| Stable Fast 3D, SPAR3D, SD3.x | Stability Community License (gelir eşiği) | TRELLIS / Qwen-Image-Edit |
| FLUX.1 dev / Fill / Kontext dev | Non-commercial ağırlıklar | Qwen-Image-Edit |
| Ultralytics YOLOv8/11 | AGPL-3.0 | Grounding DINO / OWLv2 |
| MinIO | AGPL-3.0 | S3 / R2 / SeaweedFS |
| CogVideoX-5B, LTX-Video | Özel lisans / gelir eşiği | Wan + VACE |
| Autodesk FBX SDK | Kapalı lisans | glTF/OBJ/USD, ileride kendi ASCII-FBX yazıcımız |

> **TRELLIS uyarısı:** TRELLIS'in kendisi MIT ama resmi `setup.sh` ile kurulduğunda yukarıdaki yasaklı paketler de geliyor. Worker imajında bu paketler **kurulmayacak**. Mesh çıkarma, texture baking ve render adımlarını PyTorch3D/gsplat ile kendimiz yazacağız. CI'da bu paket adları için bir kara liste kontrolü olacak.

## Süreç

1. Yeni bileşen → bu dosyaya satır (lisans, sürüm/commit, kaynak linki, tarih).
2. CI: Python için `pip-licenses`, npm için `license-checker`. İzinli liste dışında bir lisans varsa build kırılır. Ek olarak kara liste: `nvdiffrast`, `nvdiffrec`, `diffoctreerast`, `diff-gaussian-rasterization`, `ultralytics`.
3. Docker imajları sabit sürüm/commit hash ile kurulur. Ağırlıklar kendi depolamamıza kopyalanır, lisans dosyalarıyla birlikte saklanır.
