# Kesim günlüğü, 7 Kasım 2026

Taban: repo tex (tucana1 @ 7cbdb98) + Isaac yaması = `versions/v1_repo_head_plus_isaac_7nov.tex`
(1.365 satır, ana metin 8.150 kelime, derlenince ana metin ~11 sayfa).
Sonuç: `overleaf/drift_attribution_aaai.tex` = `versions/v16_final_cut.tex`
(ana metin 5.769 kelime; **ana metin tam 8 sayfa, References 9. sayfanın başında**; toplam 19 sayfa).
Validator (`repo/sim2/validate_josh_results.py`): 11/11 ok; quoted() artık boşluk-duyarsız.

## Ek'e taşınanlar (kayıpsız)
- Tablo 2 information budget -> yeni `app:information` (Ek A)
- Fig 5 utility -> `app:intervals`; Fig 6 decision -> `app:decision`; Fig 4 triage -> `app:sites`
- Tablo e1_decision (keep-or-refit) -> `app:decision` (F4 metni sayıları koruyor)
- Prop RD (local-to-global gap) -> `app:rd`; ana metinde 2 cümle
- Dört marjinal katkı (two references) -> `app:robustness`, yeni paragraf
- Tablo 1 identification: table* -> tek sütun table

## Ana metinde kalan şekiller: Fig 1 attribution, Fig 2 positivity, Fig 3 retrain (0.68 genişlik), Fig 7 MIMIC (0.8)
## Ana metinde kalan tablolar: Tablo 1 identification (tek sütun)

## Üç ekip kararı metinde
1. Giriş P1: "AUROC falls and the score over-predicts at every event rate ... Brier ... rises at high
   event rates and falls at realistic ones; the misattribution we study does not depend on that sign."
2. F3 açılışı mekanizmayla: "The refit learns that the patients the alert flagged are low risk, because
   their events were prevented ..."
3. Output paragrafı: politika terimi + toplam ekzojen değişim birincil; X/Y ayrımı ikincil (MIMIC SD notu).

## Birleştirilen paragraflar
Environments+Structural model; What monitoring sees+attribution game; Decision endpoint+Estimand;
Reading+Remark; Related work 5 -> 3 paragraf (Prediction under interventions + monitoring + alerts tek paragraf).

## Validator yüzünden geri konan ifadeler (sayılar dosyaya bağlı)
$0.744$ in the rounds; still loses a third of the benefit; $8\%$ of S4 replicates; no two of the rules
in Table~\ref{tab:decision} differ by more than $1.3$ points; $+16.5\%$ induced; oracle policy
weights $+0.0268$ [...]; $I(\pi,Y)=+0.0004$; NB aralıkları; harm $11.50$ -> $10.56$; RD $-0.291$ /
overstates by $14\%$ (app:rd'ye); F7 union-graph aralığı; F7 weighted refit $0.183$ [...].

## Kalan işler (sırayla)
1. **Single-blind**: `\author{}` / `\affiliations{}` doldurulacak; şu an "Anonymous submission".
   `aaai2026.sty [submission]` -> AAAI-27 author kit (aaai2027.sty, non-anonymous mod). Kit aaai.org'dan
   indirilemedi (403); Alicem indirip `overleaf/` içine koyarsa ben değiştiririm.
2. Ek'teki figürlerin yerleşimi: Fig 4 ve Fig 5 `[t]` ile bölüm başlıklarından önce; derlemede kontrol.
3. İç hakem turu (W10): her sayı validator'dan; başlıklar tek başına okunur mu.
4. Overleaf'e yükleme: `overleaf/` klasörünün tamamı (tex, bib, sty, bst, figures/, tables/).
5. GitHub: PR #2, PR #6 merge; Isaac yaması + bu kesim tek PR olarak (token gelince ben).

# 8 Kasım ekleri
- GitHub: PR #2 merge (Alicem), Josh'un PR #6 branch'i `josh/status-figures-review` olarak aynalanıp PR #3 ile merge edildi;
  main = d6e489f. Bugünkü tüm iş PR #4 (`alicem/aaai27-medwm-cut`, 2 commit, 7d3a0d2): https://github.com/alicemkyn/drift-attribution/pull/4
- AAAI-27 kit: aaai2027.sty [preprint] + aaai2027.bst; sty pdfTeX zorunlu kılıyor (tectonic/XeTeX ile derlenmez).
  Yerel derleme: pdflatex (TeX Live 2026, conda) + TeX Live 2022 bundle dizini TEXINPUTS olarak. Overleaf'te pdfLaTeX seçili olmalı.
- newtxtext daha sıkı: ana metin 8. sayfanın %63'ünde bitiyor; Tablo 2 (keep-or-refit) ve dört marjinal katkı ana metne geri alındı.
- Yazar bloğu hâlâ placeholder (First/Second/Third Author). Dolunca 2–4 satır eklenir; pay var.
- Kalan: yazar bloğu; iç hakem turu (W10); Overleaf'e `overleaf/` zip'i yükle (derleyici: pdfLaTeX); PR #4 merge.
