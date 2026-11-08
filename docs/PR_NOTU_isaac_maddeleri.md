# PR taslağı — Isaac'in açık maddeleri (4, 5, 7, 8a, 8c, 8d)

Taban: `tucana1/drift-attribution` @ 7cbdb98 (PR #6 head). Validator yamadan sonra 11/11 `ok`.
Uygulama: `patch_isaac_7nov.zip` içindeki dosyaları aynı yollara kopyalayın veya
`git apply isaac_points_4_5_7_8.patch` (tex, bib, validator) + iki yeni dosya.

## Dosyalar
| Dosya | Değişiklik |
|---|---|
| `aaai/references.bib` | +4 giriş: `quintasmartinez2024multiply` (ICML 2024, PMLR 235), `gowerwinter2025performative` (AAAI 2025), `papadogeorgou2025selection` (Biometrics 81, 2025, doi 10.1093/biomtc/ujaf013), `santanna2026compositional` (J. Econometrics 253:106147, doi 10.1016/j.jeconom.2025.106147). Hepsi arXiv + CrossRef'ten doğrulandı. |
| `aaai/drift_attribution_aaai.tex` | 5 düzenleme (aşağıda) |
| `sim2/exp_G2_sites_clusterboot.py` | **yeni**: E5 için site-küme bootstrap; `exp_G2_sites` DGP/estimatörlerini import eder, nokta tahminleri birebir aynı (seed 0, iki satırda 6 basamağa kadar kontrol edildi) |
| `figures/merged_expG2_clusterboot.json` | **yeni**: 100 seed × B=300, 4 satır |
| `sim2/validate_josh_results.py` | PRODUCERS'a yeni JSON eklendi |

## Tex düzenlemeleri
1. **Related work / Attribution (8a):** Quintas-Martínez et al. cümlesi — çoklu-sağlamlık nuisance
   yanlış belirtimine karşıdır, Prop 1'in destek ihlaline karşı değil; koalisyon değeri
   dağıtım-öncesi veriyle belirlenmiyor.
2. **Related work / Monitoring (8c):** Gower-Winter et al. (AAAI 2025) — performatif vs intrinsik
   drift *tespiti*; biz atıf + hangi tasarımın tanımladığı.
3. **F5 sonu (4, 8d):** iki nitelik — küme randomizasyonu randomizasyon-sonrası kayıt
   değişimini ayırmaz (Papadogeorgou); crossover DiD'de kompozisyon değişimi bizde hedef,
   Sant'Anna–Xu'da nuisance; E5 veri içindeki kompozisyonu simüle eder, veriye seçimi değil.
4. **Limitations (5):** dağıtıma bağlı seçim paragrafı — dışlanan hastaların sonucu yok;
   randomize kol da site tasarımları da bunu çözmez.
5. **Appendix sites (7):** "Intervals that respect the design" paragrafı, sayılar JSON'dan.

## Küme bootstrap sonucu (yeni bulgu, Isaac 7)
| Rollout, trend | retro cov | DiD endo cov | DiD exog cov | bootSD/seedSD (retro) |
|---|---|---|---|---|
| random, common | 0.98 | 1.00 | 0.93 | 0.88 |
| random, site-specific | 0.99 | 1.00 | 0.87 | 0.99 |
| correlated, common | **0.82** | **0.64** | **0.13** | 0.74 |
| correlated, site-specific | 0.96 | 0.93 | 0.56 | 0.85 |

Okuma: tasarım terimi tanımlıyorsa site-küme aralığı nominal (%93–100) ve bootstrap SD'si
gerçek örnekleme SD'sinin %84–99'u; sıra z'ye bağlıysa aralık yanlı estimatörün örnekleme
belirsizliğini raporluyor ve paralel-eğilim ihlalini onaramıyor. Bu, Tablo 1'in
"If loss trends are parallel" satırını ampirik olarak destekliyor. Ekzojen parçanın random
sırada bile %87–93'te kalması: son crossover'da kontrol yalnız 12 site; not düşüldü.

## Uyarılar
- Bu yama tex'i **uzatıyor** (~+330 kelime); kesim turunda ana metindeki F5 ekinin (madde 3)
  tek cümleye inip kalanının appendix'e taşınması gerekecek.
- Prop numaraları/etiketleri değişmedi; `prop:absence` ve `sec:responsible` mevcut etiketler.
