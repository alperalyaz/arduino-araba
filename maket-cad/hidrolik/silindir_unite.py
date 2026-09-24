# -*- coding: utf-8 -*-
"""
MİNİ HİDROLİK ASANSÖR MAKETİ — SİLİNDİR VE GÜÇ ÜNİTESİ ÇİZİMLERİ
Çıktılar (bu klasöre):
  silindir.step, unite.step          — Onshape için
  silindir_teknik_resim.png          — kesit + alt/üst detay + ölçüler
  unite_resim.png                    — 3D görünüş + ön/yan görünüş + ölçüler
  hidrolik_hesap.txt                 — basınç, debi, pompa, motor, burkulma
  hidrolik_parca_listesi.csv         — imalat + satın alma (Türk Excel)
Çalıştırma:  & "C:\\ardiuno\\.venv-cad\\Scripts\\python.exe" silindir_unite.py
"""
import csv
import math
import os

import cadquery as cq
import numpy as np
from cadquery import Vector

import hidrolik_parcalar as h

CIKTI = os.path.dirname(os.path.abspath(__file__))
STROK = 850.0
MIL_DISARI = 115.0          # mil en altta iken kafadan dışarıda kalan (ana modelle aynı)

# --- Parçaları oluştur (silindir tabanı z=0, ünite taban sacı z=0) ---
so = h.silindir_olculer(0, STROK)
sil_p, SO = h.silindir(0, 0, 0, STROK, so["z_kapak_ust"] + MIL_DISARI)
uni_p, UO = h.unite(0, 0, 0)
# Pano (invertör) ana modeldeki yerine göre: ünite merkezi (780, 300, taban 140) → pano (657, 45, 790)
pano_p, PO = h.kumanda_panosu(657 - 780, 45 - 300, 790 - 140)
# Hortum başlangıcı (bloktan çıkan kısa parça) — ana modelde silindire kadar gider
bx, by, bz = UO["blok_cikis"]
hortum_ucu, _ = h.hortum_kiv([(bx, by, bz), (bx - 25, by + 2, bz - 15), (bx - 40, by + 8, bz - 70)], (-1, 0, 0), (0, 0.2, -1))
uni_gorunum = uni_p + pano_p + [("BASINC_HORTUMU_UCU", hortum_ucu, "HAYALET", "hortum", "HORTUM")]
H = h.hesap(STROK)
pcr, burk = h.burkulma(STROK + MIL_DISARI, H["kuvvet_dolu"])

# --- STEP ---
for ad, parcalar in (("silindir", sil_p), ("unite", uni_p + pano_p)):
    assy = cq.Assembly(name=ad.upper())
    for pad, s, tur, r, g in parcalar:
        assy.add(s, name=pad, color=cq.Color(*h.RENKLER[r]))
    assy.export(os.path.join(CIKTI, f"{ad}.step"))

# --- Hesap raporu ---
satir = [
    "MİNİ HİDROLİK ASANSÖR MAKETİ — HİDROLİK HESAP",
    "=" * 60,
    f"Kabin + askı (tahmin) {h.KABIN_ASKI_KG:.0f} kg, gösteri yükü {h.GOSTERI_YUKU_KG:.0f} kg, 2:1 zincirli",
    f"Piston kuvveti: yüksüz {H['kuvvet_bos']:.0f} kgf, yüklü {H['kuvvet_dolu']:.0f} kgf",
    f"Dalgıç mil Ø{h.MIL_D:.0f} (alan {H['alan']:.0f} mm²) → basınç yüksüz {H['p_bos']:.1f} bar, yüklü {H['p_dolu']:.1f} bar",
    f"Emniyet valfi ayarı (1,4 x yüklü): {H['emniyet_bar']:.0f} bar",
    f"Kabin hızı {h.KABIN_HIZ:.0f} mm/s → mil hızı {H['v_mil']:.0f} mm/s → debi {H['q']:.2f} L/dk",
    f"Pompa: {H['q']:.2f} L/dk / ({h.MOTOR_DEVIR:.0f} d/dk x ηv {h.POMPA_VOL_VERIM}) = {H['pompa_cc']:.2f} cc/dev → ~1 cc",
    f"Motor gücü: {H['guc_w']:.0f} W (toplam verim {h.TOPLAM_VERIM}) → 0,25 kW 4 kutup, invertörle",
    f"İniş: pompa geri döner, hızı invertör ayarlar (fren kıyıcı + direnç); duruşta oturmalı NC valf kapanır",
    f"Piston hacmi {H['mil_hacim_l']:.2f} L; tank iç hacmi {UO['tank_ic_l']:.1f} L",
    f"Silindir kapalı boyu {SO['kapali_boy']:.0f} mm, gömlek {SO['gomlek_boy']:.0f}, mil {SO['mil_boy']:.0f}, strok {STROK:.0f}",
    f"Burkulma (kafa kılavuzsuz, K=2, serbest boy {STROK + MIL_DISARI:.0f}): kritik {pcr:.0f} kgf, emniyet {burk:.1f}",
    f"Gömlek çevre gerilmesi (emniyet basıncında): "
    f"{H['emniyet_bar'] / 10 * (h.GOMLEK_D - 2 * h.GOMLEK_T) / (2 * h.GOMLEK_T):.0f} MPa (çok düşük)",
    "",
    "NOTLAR",
    "- Pompa motor olarak geri dönebilen tipte olmalı; en düşük devrini tedarikçiden teyit edin (düşük devirde kaçak).",
    "- 1,2 L/dk, asansör hortum patlama valflerinin çoğunun altında; düşük debili ayarlı tip bulun.",
    "- İki zincir ortadan mafsallı terazi ile eşit çeker; mil yana yüklenmez.",
    "- Bu hesap maket içindir; gerçek asansörde EN 81-20/50 ve onaylanmış kuruluş hesabı gerekir.",
]
with open(os.path.join(CIKTI, "hidrolik_hesap.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(satir))
print("\n".join(satir))


# --- Parça listesi ---
def kg(on):
    return sum(s.Volume() for pad, s, *_ in sil_p + uni_p if pad.startswith(on)) * h.YOGUNLUK


def tr(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


liste = [
    ("İmalat", "Gömlek", f"Boru {h.GOMLEK_D:.0f}x{h.GOMLEK_T:.0f} (iç Ø{h.GOMLEK_D - 2 * h.GOMLEK_T:.0f}), boy {SO['gomlek_boy']:.0f}", 1, kg("SILINDIR_GOMLEK")),
    ("İmalat", "Dalgıç mil", f"Krom mil Ø{h.MIL_D:.0f} h8, boy {SO['mil_boy']:.0f}", 1, kg("PISTON_MILI")),
    ("İmalat", "Strok sonu halkası", f"Ø{h.HALKA_D:.0f}x{h.HALKA_H:.0f}, iki yağ düzlüğü {h.HALKA_DUZ:.0f}, mile pimli", 1, kg("STROK_SONU")),
    ("İmalat", "Dip bloğu", f"{h.DIP_A:.0f}x{h.DIP_A:.0f}x{h.DIP_H:.0f} dolu, 1/4\" BSP yan giriş + Ø14 yağ yolu", 1, kg("SILINDIR_DIP")),
    ("İmalat", "Ayak plakası", f"Lazer {h.AYAK_A:.0f}x{h.AYAK_A:.0f}x{h.AYAK_T:.0f}, 4xØ9 ({h.AYAK_DELIK_ARA:.0f}x{h.AYAK_DELIK_ARA:.0f})", 1, kg("SILINDIR_AYAK")),
    ("İmalat", "Kafa gövdesi", f"Ø{h.KAFA_D:.0f}x{h.KAFA_H:.0f}, iç Ø30 + M42x1,5 diş, gömleğe kaynaklı", 1, kg("SILINDIR_KAFA_GOVDESI")),
    ("İmalat", "Kafa kapağı", f"Ø{h.KAFA_D:.0f} flanş {h.KAPAK_FLANS_H:.0f} + M42 boyun {h.KAFA_DIS_H:.0f}; burç, U-keçe, toz keçesi yuvalı; hava alma M6", 1, kg("SILINDIR_KAFA_KAPAGI")),
    ("İmalat", "Tank", f"{h.TANK_T:.0f} mm sac {h.TANK_X:.0f}x{h.TANK_Y:.0f}x{h.TANK_Z:.0f}, kaynaklı", 1, kg("TANK") - kg("TANK_KAPAGI")),
    ("İmalat", "Tank kapağı", f"Lazer {h.TANK_X + 20:.0f}x{h.TANK_Y + 20:.0f}x{h.KAPAK_T:.0f}, Ø60 pompa deliği", 1, kg("TANK_KAPAGI")),
    ("İmalat", "Yağ tavası", f"{h.TAVA_T} mm sac {h.TAVA_X:.0f}x{h.TAVA_Y:.0f}x{h.TAVA_Z:.0f} + 4 ayak Ø20x{h.TAVA_AYAK_H:.0f}", 1, kg("YAG_TAVASI") + kg("TAVA_AYAGI")),
    ("Satın alma", "Motor", "IEC 71 B5 (FF130, Ø160 flanş), 0,25 kW 4 kutup (71A4), trifaze, dikey; 0,37 kW (71B4) aynı gövde", 1, None),
    ("Satın alma", "Dişli pompa", "~1 cc/dev, motor olarak da çalışabilen (çift yönlü)", 1, None),
    ("Satın alma", "Çan + kaplin", "71 B5 motor (Ø160 flanş) / grup 0-1 pompa, kaplin pencereli", 1, None),
    ("Satın alma", "Kumanda panosu", f"{h.PANO_X:.0f}x{h.PANO_Y:.0f}x{h.PANO_Z:.0f} sac pano, acil stop, KLASİK/KONFOR seçici, ekran", 1, None),
    ("Satın alma", "Fren direnci", "İnvertöre uygun (inişte enerji burada yanar), panonun yanına", 1, None),
    ("Satın alma", "Valf bloğu", f"Çek valf + oturmalı NC iniş valfi 24 V DC + emniyet valfi ({H['emniyet_bar']:.0f} bar) + elle acil indirme", 1, None),
    ("Satın alma", "Manometre", "0-100 bar, Ø63, gliserinli", 1, None),
    ("Satın alma", "Basınç transmitteri", "0-100 bar, 4-20 mA", 1, None),
    ("Satın alma", "Hortum patlama valfi", "1/4\", düşük debi 1-3 L/dk ayarlı", 1, None),
    ("Satın alma", "Keçe takımı", "Bronz burç Ø20x25x20, U-keçe 20x28x5, toz keçesi 20x28x4", 1, None),
    ("Satın alma", "Tank donanımı", "Emiş süzgeci, seviye göstergesi, hava/dolum tapası + taşıma kör tapası, boşaltma tapası", 1, None),
    ("Satın alma", "Hortum", "1/4\" ~2,5 m + rakorlar", 1, None),
    ("Satın alma", "Yağ", "HLP 32, 5 L", 1, None),
    ("Satın alma", "İnvertör", "0,4 kW monofaze giriş, vektör kontrol, dahili fren kıyıcı + fren direnci", 1, None),
]
with open(os.path.join(CIKTI, "hidrolik_parca_listesi.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Tür", "Parça", "Ölçü / açıklama", "Adet", "Ağırlık (kg)"])
    for t, p, o, a, k in liste:
        w.writerow([t, p, o, a, "" if k is None else tr(k, 2)])
    w.writerow(["TOPLAM (imalat çeliği)", "", "", "", tr(sum(k for *_, k in liste if k is not None), 2)])

# =====================================================================
# GÖRSELLER
# =====================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def bol(T, maks):
    while True:
        k = np.max(np.linalg.norm(T - np.roll(T, 1, axis=1), axis=2), axis=1)
        b = k > maks
        if not b.any():
            return T
        B = T[b]
        m01, m12, m20 = (B[:, 0] + B[:, 1]) / 2, (B[:, 1] + B[:, 2]) / 2, (B[:, 2] + B[:, 0]) / 2
        T = np.concatenate([T[~b]] + [np.stack(s, axis=1) for s in ((B[:, 0], m01, m20), (m01, B[:, 1], m12),
                                                                      (m20, m12, B[:, 2]), (m01, m12, m20))])


def sahne(ax, parcalar, elev, azim, maks=12, baslik=""):
    TT, CC = [], []
    for pad, s, tur, r, g in parcalar:
        V, F = s.tessellate(0.5, 0.3)
        if not F:
            continue
        V = np.array([(v.x, v.y, v.z) for v in V])
        T = bol(V[np.array(F)], maks)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        L = np.array([-0.45, -0.75, 0.5]); L /= np.linalg.norm(L)
        renk = h.RENKLER[r]
        c = np.clip(np.array(renk[:3])[None, :] * (0.45 + 0.55 * np.abs(n @ L))[:, None], 0, 1)
        TT.append(T); CC.append(np.hstack([c, np.full((len(T), 1), renk[3])]))
    T = np.concatenate(TT)
    ax.add_collection3d(Poly3DCollection(T, facecolors=np.concatenate(CC), edgecolors="none"))
    mn, mx = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    ax.set_xlim(mn[0], mx[0]); ax.set_ylim(mn[1], mx[1]); ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(mx - mn)
    ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(baslik, fontsize=11, fontweight="bold")


def olcu(ax, p1, p2, metin, ofs, dikey=True, fs=8, renk="k"):
    if dikey:
        x = p1[0] + ofs
        ax.annotate("", (x, p1[1]), (x, p2[1]), arrowprops=dict(arrowstyle="<->", lw=0.8, color=renk))
        ax.plot([p1[0], x], [p1[1], p1[1]], lw=0.4, color=renk); ax.plot([p2[0], x], [p2[1], p2[1]], lw=0.4, color=renk)
        ax.text(x + 3, (p1[1] + p2[1]) / 2, metin, rotation=90, va="center", fontsize=fs, color=renk)
    else:
        y = p1[1] + ofs
        ax.annotate("", (p1[0], y), (p2[0], y), arrowprops=dict(arrowstyle="<->", lw=0.8, color=renk))
        ax.text((p1[0] + p2[0]) / 2, y + 3, metin, ha="center", fontsize=fs, color=renk)


# --- SİLİNDİR TEKNİK RESMİ: Y-Z düzleminde kesit (giriş solda, -Y) ---
def kesit(ax, z0, z1):
    tar = dict(fc="#c9ced6", ec="k", lw=0.7, hatch="////")
    r_g, r_gi = h.GOMLEK_D / 2, h.GOMLEK_D / 2 - h.GOMLEK_T
    ax.add_patch(Rectangle((-h.AYAK_A / 2, 0), h.AYAK_A, h.AYAK_T, **tar))
    for dx in (-h.AYAK_DELIK_ARA / 2, h.AYAK_DELIK_ARA / 2):
        ax.add_patch(Rectangle((dx - 4.5, 0), 9, h.AYAK_T, fc="white", ec="k", lw=0.5))
    ax.add_patch(Rectangle((-h.DIP_A / 2, SO["z_ayak_ust"]), h.DIP_A, h.DIP_H, **tar))
    zg = SO["z_ayak_ust"] + h.GIRIS_Z
    ax.add_patch(Rectangle((-h.DIP_A / 2, zg - 5.75), h.DIP_A / 2, 11.5, fc="white", ec="k", lw=0.5))
    ax.add_patch(Rectangle((-7, zg - 6), 14, SO["z_dip_ust"] - zg + 6, fc="white", ec="k", lw=0.5))
    for s in (-1, 1):
        ax.add_patch(Rectangle((s * r_gi if s > 0 else -r_g, SO["z_dip_ust"]), h.GOMLEK_T, SO["gomlek_boy"], **tar))
        ax.add_patch(Rectangle((r_gi if s > 0 else -h.KAFA_D / 2, SO["z_gomlek_ust"]), h.KAFA_D / 2 - r_gi, SO["z_bogaz_alt"] - SO["z_gomlek_ust"], **tar))
        ax.add_patch(Rectangle((h.KAFA_DIS_D / 2 if s > 0 else -h.KAFA_D / 2, SO["z_bogaz_alt"]),
                               h.KAFA_D / 2 - h.KAFA_DIS_D / 2, SO["z_kafa_ust"] - SO["z_bogaz_alt"], **tar))
        kap = dict(fc="#aab2bd", ec="k", lw=0.7, hatch="\\\\\\\\")
        ax.add_patch(Rectangle((10.2 if s > 0 else -h.KAFA_DIS_D / 2, SO["z_bogaz_alt"]), h.KAFA_DIS_D / 2 - 10.2, h.KAFA_DIS_H, **kap))
        ax.add_patch(Rectangle((10.2 if s > 0 else -h.KAFA_D / 2, SO["z_kafa_ust"]), h.KAFA_D / 2 - 10.2, h.KAPAK_FLANS_H, **kap))
        # burç, U-keçe, toz keçesi (şematik)
        for (za, zb, rk) in ((SO["z_bogaz_alt"] + 2, SO["z_bogaz_alt"] + 18, "#c98b2b"),
                             (SO["z_bogaz_alt"] + 20, SO["z_bogaz_alt"] + 25, "#222"),
                             (SO["z_kapak_ust"] - 7, SO["z_kapak_ust"] - 2, "#222")):
            ax.add_patch(Rectangle((10.2 if s > 0 else -14.5, za), 4.3, zb - za, fc=rk, ec="k", lw=0.3))
        # strok sonu halkası (düzlüklerden görünüş)
        ax.add_patch(Rectangle((10 if s > 0 else -h.HALKA_DUZ / 2, SO["z_mil_alt"]), h.HALKA_DUZ / 2 - 10, h.HALKA_H, **kap))
    mil_ust = SO["z_kapak_ust"] + MIL_DISARI
    ax.add_patch(Rectangle((-10, SO["z_mil_alt"]), 20, mil_ust - SO["z_mil_alt"], fc="#e8eaee", ec="k", lw=0.8))
    ax.add_patch(Rectangle((-h.DIP_A / 2 - 32, zg - 11), 32, 22, fc="#d6d1bd", ec="k", lw=0.7))
    ax.set_ylim(z0, z1)
    ax.set_aspect("equal")
    ax.axvline(0, color="#c00", lw=0.5, ls="-.")
    ax.tick_params(labelsize=7)


fig = plt.figure(figsize=(18, 11), dpi=110)
gs = fig.add_gridspec(2, 3, width_ratios=[0.55, 1, 1], height_ratios=[1, 1])
a0 = fig.add_subplot(gs[:, 0])
kesit(a0, -30, SO["z_kapak_ust"] + MIL_DISARI + 40)
a0.set_xlim(-130, 110)
a0.set_title("GENEL (mil en altta)", fontsize=11, fontweight="bold")
olcu(a0, (h.KAFA_D / 2, 0), (h.KAFA_D / 2, SO["z_kapak_ust"]), f"kapalı boy {SO['kapali_boy']:.0f}", 25)
olcu(a0, (h.KAFA_D / 2, SO["z_halka_ust"]), (h.KAFA_D / 2, SO["z_bogaz_alt"]), f"strok {STROK:.0f}", 50, renk="#c00")
olcu(a0, (-h.DIP_A / 2, SO["z_dip_ust"]), (-h.DIP_A / 2, SO["z_gomlek_ust"]), f"gömlek {SO['gomlek_boy']:.0f}", -40)
olcu(a0, (-10, SO["z_kapak_ust"]), (-10, SO["z_kapak_ust"] + MIL_DISARI), f"{MIL_DISARI:.0f}", -60, fs=7)
a0.text(-128, SO["z_mil_alt"] + 400, f"mil Ø{h.MIL_D:.0f} x {SO['mil_boy']:.0f}", fontsize=8, rotation=90, va="center")

a1 = fig.add_subplot(gs[1, 1])
kesit(a1, -15, 115)
a1.set_xlim(-100, 70)
a1.set_title("ALT DETAY — ayak, dip bloğu, giriş, strok sonu halkası", fontsize=10, fontweight="bold")
zg = SO["z_ayak_ust"] + h.GIRIS_Z
a1.text(-h.DIP_A / 2 - 30, zg + 14, "hortum patlama\nvalfi (1/4\" BSP)", fontsize=8)
a1.text(27, SO["z_mil_alt"] + 5, f"halka Ø{h.HALKA_D:.0f}, iki düzlük\n(yağ geçer)", fontsize=8)
olcu(a1, (h.AYAK_A / 2, 0), (h.AYAK_A / 2, SO["z_ayak_ust"]), f"{h.AYAK_T:.0f}", 6, fs=7)
olcu(a1, (h.AYAK_A / 2, SO["z_ayak_ust"]), (h.AYAK_A / 2, SO["z_dip_ust"]), f"{h.DIP_H:.0f}", 6, fs=7)
olcu(a1, (-h.AYAK_A / 2, 0), (h.AYAK_A / 2, 0), f"ayak {h.AYAK_A:.0f}x{h.AYAK_A:.0f}x{h.AYAK_T:.0f}, 4xØ9", -12, dikey=False)
a1.text(-h.GOMLEK_D / 2 - 3, SO["z_dip_ust"] + 55, f"gömlek Ø{h.GOMLEK_D:.0f}x{h.GOMLEK_T:.0f}", fontsize=8, ha="right")

a2 = fig.add_subplot(gs[0, 1])
kesit(a2, SO["z_gomlek_ust"] - 40, SO["z_kapak_ust"] + 60)
a2.set_xlim(-100, 70)
a2.set_title("ÜST DETAY — kafa gövdesi (kaynaklı) + sökülebilir kapak", fontsize=10, fontweight="bold")
a2.text(30, SO["z_bogaz_alt"] + 5, "bronz burç\nU-keçe\ntoz keçesi", fontsize=8)
a2.text(-98, SO["z_kafa_ust"] - 18, f"M42x1,5\nkapak dişi", fontsize=8)
olcu(a2, (-h.KAFA_D / 2, SO["z_gomlek_ust"]), (-h.KAFA_D / 2, SO["z_kafa_ust"]), f"{h.KAFA_H:.0f}", -12, fs=7)
olcu(a2, (-h.KAFA_D / 2, SO["z_kafa_ust"]), (-h.KAFA_D / 2, SO["z_kapak_ust"]), f"{h.KAPAK_FLANS_H:.0f}", -12, fs=7)
olcu(a2, (-h.KAFA_D / 2, SO["z_kapak_ust"] + 30), (h.KAFA_D / 2, SO["z_kapak_ust"] + 30), f"Ø{h.KAFA_D:.0f}", 0, dikey=False)
a2.text(-98, SO["z_gomlek_ust"] - 30, "strok sonunda halka\nkapak boynuna dayanır", fontsize=8, color="#c00")

a3 = fig.add_subplot(gs[:, 2], projection="3d")
sahne(a3, sil_p, 18, -55, 15, "SİLİNDİR (3D)")
fig.suptitle(f"Dalgıç silindir — Ø{h.MIL_D:.0f} mil, strok {STROK:.0f}, kapalı boy {SO['kapali_boy']:.0f} mm  |  "
             f"yüklü {H['p_dolu']:.0f} bar, emniyet {H['emniyet_bar']:.0f} bar  |  MAKET İÇİN — TASLAK",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(os.path.join(CIKTI, "silindir_teknik_resim.png"))
plt.close(fig)

# --- ÜNİTE RESMİ: 3D + ön + yan görünüş ---
fig = plt.figure(figsize=(18, 9), dpi=110)
gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1])
a0 = fig.add_subplot(gs[0], projection="3d")
sahne(a0, uni_gorunum, 18, -55, 14, "GÜÇ ÜNİTESİ + PANO (3D)")


def gorunus(ax, eksen, baslik):
    """eksen 0: ön görünüş (X-Z), 1: yan görünüş (Y-Z) — parçaların dış kutularıyla."""
    ic = ("DISLI_POMPA", "EMIS_SUZGECI")                 # tankın içinde: kesik çizgi
    sonra = []
    for pad, s, tur, r, g in uni_gorunum:
        b = s.BoundingBox()
        u0, u1 = (b.xmin, b.xmax) if eksen == 0 else (b.ymin, b.ymax)
        renk = h.RENKLER[r]
        if pad.startswith(ic):
            sonra.append(Rectangle((u0, b.zmin), u1 - u0, b.zlen, fc="none", ec="#333", lw=0.9, ls="--"))
        elif pad.startswith("YAG_TAVASI"):
            sonra.append(Rectangle((u0, b.zmin), u1 - u0, b.zlen, fc="none", ec="#1f5fbf", lw=1.2))
        else:
            ax.add_patch(Rectangle((u0, b.zmin), u1 - u0, b.zlen, fc=renk[:3], ec="k", lw=0.4, alpha=0.9 if renk[3] > 0.7 else 0.5))
    for r_ in sonra:
        ax.add_patch(r_)
    ax.axhline(0, color="k", lw=1.2)
    ax.set_aspect("equal"); ax.tick_params(labelsize=7); ax.set_title(baslik, fontsize=11, fontweight="bold")
    ax.set_ylim(-40, 650 + h.PANO_Z + 40)


a1 = fig.add_subplot(gs[1]); gorunus(a1, 0, "ÖN GÖRÜNÜŞ")
a1.set_xlim(-160, h.TAVA_X / 2 + 110)
olcu(a1, (h.TAVA_X / 2 + 10, 0), (h.TAVA_X / 2 + 10, UO["tepe"]), f"toplam {UO['tepe']:.0f}", 25)
olcu(a1, (-h.TANK_X / 2, UO["zt0"]), (h.TANK_X / 2, UO["zt0"]), f"tank {h.TANK_X:.0f}", -35, dikey=False)
olcu(a1, (-h.TANK_X / 2, UO["zt0"]), (-h.TANK_X / 2, UO["zt1"]), f"{h.TANK_Z:.0f}", -45)
a1.text(0, UO["zk1"] + h.CAN_H + h.MOTOR_H / 2, "motor\n0,25 kW", ha="center", fontsize=8, color="white")
a2 = fig.add_subplot(gs[2]); gorunus(a2, 1, "YAN GÖRÜNÜŞ (manometre solda, öne bakar)")
a2.set_xlim(-h.TAVA_Y / 2 - 110, h.TAVA_Y / 2 + 40)
olcu(a2, (-h.TANK_Y / 2, UO["zt0"]), (h.TANK_Y / 2, UO["zt0"]), f"tank {h.TANK_Y:.0f}", -40, dikey=False)
olcu(a2, (-h.TAVA_Y / 2, 0), (h.TAVA_Y / 2, 0), f"tava {h.TAVA_Y:.0f} (tabana 4xM8)", -70, dikey=False)
a2.set_ylim(-90, 650 + h.PANO_Z + 40)
a1.set_ylim(-90, 650 + h.PANO_Z + 40)
fig.suptitle(f"Güç ünitesi — {str(round(UO['tank_ic_l'], 1)).replace('.', ',')} L tank, ~1 cc çift yönlü pompa, IEC 71 motor 0,25 kW, pano + invertör, çıkış ve iniş invertörle  |  TASLAK",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(CIKTI, "unite_resim.png"))
plt.close(fig)
print("\nÇıktılar:", ", ".join(sorted(f for f in os.listdir(CIKTI) if not f.endswith(".py") and f != "__pycache__")))
