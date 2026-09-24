# -*- coding: utf-8 -*-
"""
MİNİ HİDROLİK ASANSÖR MAKETİ — SİLİNDİR VE GÜÇ ÜNİTESİ (parametre + parça üreticileri)
=======================================================================================
Hem ana maket modeli (taban-dikme/maket_taban_dikme.py) hem de bu klasördeki
silindir_unite.py bu dosyayı kullanır. Ölçüler mm, kütleler kg.

Tahrik: 2:1 zincirli, dalgıç silindir. Çıkış VE iniş invertörle:
  - çıkışta pompa normal döner, yağ çek valften silindire gider;
  - inişte oturmalı iniş valfi açılır, yağ pompadan geri akar, pompa motor gibi döner,
    hızı invertör ayarlar (fren direnci ile). Duruşta oturmalı valf kapanır, kabin sızdırmadan durur.
"""
import math

import cadquery as cq
from cadquery import Vector

YOGUNLUK = 7.85e-6

# =====================================================================
# PARAMETRELER
# =====================================================================
# --- Yükler ve hız (hesap için) ---
KABIN_ASKI_KG = 45.0        # kabin + askı + paraşüt (tahmin)
GOSTERI_YUKU_KG = 20.0      # fuarda kabine konacak ağırlık
BAS_ZINCIR_KG = 6.0         # piston başı + makaralar + zincirler + milin payı
KABIN_HIZ = 130.0           # mm/s (hedef 120-150)
MOTOR_DEVIR = 1400.0        # d/dk, 4 kutup 50 Hz
POMPA_VOL_VERIM = 0.90
TOPLAM_VERIM = 0.60
EMNIYET_KATSAYI = 1.4       # emniyet valfi = tam yük basıncı x 1,4

# --- Silindir (dalgıç) ---
MIL_D = 20.0                # krom mil Ø20 h8
GOMLEK_D, GOMLEK_T = 40.0, 5.0   # gömlek borusu 40x5 (iç 30)
AYAK_A, AYAK_T = 80.0, 10.0      # ayak plakası 80x80x10, 4xM8
AYAK_DELIK_ARA = 60.0
DIP_A, DIP_H = 50.0, 40.0        # kaynaklı dip bloğu (yağ girişi burada, yandan)
GIRIS_Z = 20.0                   # yağ girişi ekseni, dip bloğu altından
HALKA_D, HALKA_H, HALKA_DUZ = 28.0, 20.0, 24.0   # strok sonu halkası, yağ geçişi için iki düzlük
ALT_BOSLUK = 10.0                # mil en altta: mil ucu ile dip bloğu arası
KAFA_D, KAFA_H = 55.0, 35.0      # kaynaklı kafa gövdesi (alt 10 mm Ø30 delik, üst 25 mm M42 diş)
KAFA_DIS_D, KAFA_DIS_H = 42.0, 25.0
KAPAK_FLANS_H = 15.0             # sökülebilir kapak: Ø55 flanş + M42 boyun (içinde burç + U-keçe + toz keçesi)

# --- Güç ünitesi (görünen kısımlar gerçek ölçüye yakın; tankın içi çizilmez) ---
TANK_X, TANK_Y, TANK_Z, TANK_T = 180.0, 260.0, 180.0, 3.0    # ~7,8 L brüt, ~5-6 L yağ
KAPAK_T = 10.0
TAVA_X, TAVA_Y, TAVA_Z, TAVA_T = 220.0, 340.0, 40.0, 1.5
TAVA_AYAK_H = 15.0
TAVA_AYAK_DX, TAVA_AYAK_DY = 85.0, 100.0     # tava ayaklarının merkeze uzaklığı (tabanda M8)
# Motor: IEC 71, 4 kutup, B5 (FF130) flanş, dikey. 0,25 kW = 71A4; 0,37 kW = 71B4 AYNI GÖVDE
MOTOR_KW = 0.25
MOTOR_GOVDE_D = 138.0            # kanatlar dahil
MOTOR_FLANS_D, MOTOR_FLANS_T = 160.0, 10.0
MOTOR_ON_H, MOTOR_GOVDE_H, MOTOR_ARKA_H, MOTOR_FAN_H = 20.0, 150.0, 15.0, 62.0
MOTOR_FAN_D = 134.0
MOTOR_KANAT_ADET = 16
MOTOR_KLEMENS = (95.0, 58.0, 95.0)          # x genişlik, y derinlik, z yükseklik (arkaya bakar)
MOTOR_EKSEN_DY = 45.0                        # motor ekseni tank merkezinin arkasında
MOTOR_H = MOTOR_FLANS_T + MOTOR_ON_H + MOTOR_GOVDE_H + MOTOR_ARKA_H + MOTOR_FAN_H
MOTOR_D = MOTOR_GOVDE_D
# Çan (kampana): alt flanş kapağa, üst flanş motora (B5 Ø160), gövdede kaplin pencereleri
CAN_ALT_D, CAN_GOVDE_D, CAN_UST_D, CAN_H, CAN_FLANS_T = 170.0, 118.0, 160.0, 90.0, 12.0
CAN_D = CAN_ALT_D
FAN_D, FAN_H = MOTOR_FAN_D, MOTOR_FAN_H
BLOK_X, BLOK_Y, BLOK_Z = 100.0, 75.0, 60.0
BLOK_DX = 5.0                                # blok merkezi tank merkezinin biraz sağında
# Kumanda panosu (invertör içinde) + fren direnci — ünitenin üstünde, iskeletin sağ yüzüne asılı
PANO_X, PANO_Y, PANO_Z = 220.0, 150.0, 320.0
HORTUM_D = 14.0                              # 1/4" 2SN hortum dış çapı
KABLO_D = 8.0


# =====================================================================
# HESAP
# =====================================================================
def hesap(strok):
    alan = math.pi * MIL_D ** 2 / 4                          # mm2
    kuvvet_bos = 2 * KABIN_ASKI_KG + BAS_ZINCIR_KG            # kgf (2:1)
    kuvvet_dolu = 2 * (KABIN_ASKI_KG + GOSTERI_YUKU_KG) + BAS_ZINCIR_KG
    p_bos = kuvvet_bos * 9.81 / alan * 10                      # bar
    p_dolu = kuvvet_dolu * 9.81 / alan * 10
    v_mil = KABIN_HIZ / 2                                      # mm/s
    q = alan * v_mil / 1e6 * 60                                # L/dk
    pompa_cc = q * 1000 / (MOTOR_DEVIR * POMPA_VOL_VERIM)
    guc_w = (p_dolu * 1e5) * (alan * 1e-6 * v_mil * 1e-3) / TOPLAM_VERIM     # Pa * m3/s = W
    emniyet_bar = p_dolu * EMNIYET_KATSAYI
    mil_hacim_l = alan * strok / 1e6
    # Burkulma: kafa kılavuzsuz (K=2), serbest boy = strok + kafadan en altta dışarıda kalan
    I = math.pi * MIL_D ** 4 / 64
    return dict(alan=alan, kuvvet_bos=kuvvet_bos, kuvvet_dolu=kuvvet_dolu, p_bos=p_bos, p_dolu=p_dolu,
                v_mil=v_mil, q=q, pompa_cc=pompa_cc, guc_w=guc_w, emniyet_bar=emniyet_bar,
                mil_hacim_l=mil_hacim_l, I=I)


def burkulma(serbest_boy, kuvvet_kgf):
    I = math.pi * MIL_D ** 4 / 64
    pcr = math.pi ** 2 * 210000 * I / (2 * serbest_boy) ** 2 / 9.81   # kgf, K=2
    return pcr, pcr / kuvvet_kgf


# =====================================================================
# YARDIMCILAR
# =====================================================================
def kutu(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def sil(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))


def sil_y(x, z, y0, y1, d):
    """Y ekseni boyunca silindir (y0 -> y1, y1 > y0)."""
    return cq.Solid.makeCylinder(d / 2, y1 - y0, Vector(x, y0, z), Vector(0, 1, 0))


def boru(x, y, z0, z1, d_dis, d_ic):
    return sil(x, y, z0, z1, d_dis).cut(sil(x, y, z0 - 1, z1 + 1, d_ic))


# =====================================================================
# SİLİNDİR
# =====================================================================
def silindir_olculer(z_taban, strok):
    """Kotlar (z): ayak, dip bloğu, gömlek, kafa, kapak. Mil en altta iken halka dip bloğunun 10 mm üstünde."""
    z_ayak_ust = z_taban + AYAK_T
    z_dip_ust = z_ayak_ust + DIP_H
    z_mil_alt = z_dip_ust + ALT_BOSLUK
    z_halka_ust = z_mil_alt + HALKA_H
    z_bogaz_alt = z_halka_ust + strok                 # strok sonunda halka kapak boynuna dayanır
    z_gomlek_ust = z_bogaz_alt - (KAFA_H - KAFA_DIS_H)
    z_kafa_ust = z_gomlek_ust + KAFA_H
    z_kapak_ust = z_kafa_ust + KAPAK_FLANS_H
    return dict(z_taban=z_taban, z_ayak_ust=z_ayak_ust, z_dip_ust=z_dip_ust, z_mil_alt=z_mil_alt,
                z_halka_ust=z_halka_ust, z_bogaz_alt=z_bogaz_alt, z_gomlek_ust=z_gomlek_ust,
                z_kafa_ust=z_kafa_ust, z_kapak_ust=z_kapak_ust,
                gomlek_boy=z_gomlek_ust - z_dip_ust, kapali_boy=z_kapak_ust - z_taban)


def silindir(x, y, z_taban, strok, mil_ust_geri):
    """Dalgıç silindir. mil_ust_geri: mil en altta iken milin üst ucu (piston başlığının altı).
    Dönüş: [(ad, şekil, tür, renk, grup)], ölçüler sözlüğü. tür: GERCEK (imalat) / HAYALET (satın alma) / HAREKETLI."""
    o = silindir_olculer(z_taban, strok)
    p = []
    ayak = kutu(x - AYAK_A / 2, x + AYAK_A / 2, y - AYAK_A / 2, y + AYAK_A / 2, z_taban, o["z_ayak_ust"])
    for dx in (-AYAK_DELIK_ARA / 2, AYAK_DELIK_ARA / 2):
        for dy in (-AYAK_DELIK_ARA / 2, AYAK_DELIK_ARA / 2):
            ayak = ayak.cut(sil(x + dx, y + dy, z_taban - 1, o["z_ayak_ust"] + 1, 9))
    p.append(("SILINDIR_AYAK_PLAKASI", ayak, "GERCEK", "sil_govde", "SILINDIR"))
    dip = kutu(x - DIP_A / 2, x + DIP_A / 2, y - DIP_A / 2, y + DIP_A / 2, o["z_ayak_ust"], o["z_dip_ust"])
    zg = o["z_ayak_ust"] + GIRIS_Z
    dip = dip.cut(sil_y(x, zg, y - DIP_A / 2 - 1, y, 11.5))                 # 1/4" BSP giriş (yandan, -Y)
    dip = dip.cut(sil(x, y, zg - 6, o["z_dip_ust"] + 1, 14))               # dikey yağ yolu
    p.append(("SILINDIR_DIP_BLOGU", dip, "GERCEK", "sil_govde", "SILINDIR"))
    p.append(("SILINDIR_GOMLEK", boru(x, y, o["z_dip_ust"], o["z_gomlek_ust"], GOMLEK_D, GOMLEK_D - 2 * GOMLEK_T),
              "GERCEK", "sil_govde", "SILINDIR"))
    kafa = sil(x, y, o["z_gomlek_ust"], o["z_kafa_ust"], KAFA_D)
    kafa = kafa.cut(sil(x, y, o["z_gomlek_ust"] - 1, o["z_kafa_ust"] + 1, GOMLEK_D - 2 * GOMLEK_T))
    kafa = kafa.cut(sil(x, y, o["z_bogaz_alt"], o["z_kafa_ust"] + 1, KAFA_DIS_D))
    p.append(("SILINDIR_KAFA_GOVDESI", kafa, "GERCEK", "sil_govde", "SILINDIR"))
    kapak = sil(x, y, o["z_kafa_ust"], o["z_kapak_ust"], KAFA_D).fuse(sil(x, y, o["z_bogaz_alt"], o["z_kafa_ust"], KAFA_DIS_D))
    kapak = kapak.cut(sil(x, y, o["z_bogaz_alt"] - 1, o["z_kapak_ust"] + 1, MIL_D + 0.4))
    kapak = kapak.cut(sil(x + 20, y, o["z_kapak_ust"] - 12, o["z_kapak_ust"] + 1, 5))    # hava alma deliği
    p.append(("SILINDIR_KAFA_KAPAGI", kapak, "GERCEK", "sil_kapak", "SILINDIR"))
    p.append(("SILINDIR_HAVA_ALMA_VIDASI", sil(x + 20, y, o["z_kapak_ust"], o["z_kapak_ust"] + 6, 10),
              "HAYALET", "civata", "SILINDIR"))
    # Mil + strok sonu halkası (mil en altta)
    p.append(("PISTON_MILI", sil(x, y, o["z_mil_alt"], mil_ust_geri, MIL_D - 0.2), "HAREKETLI", "mil", "PISTON_MILI"))
    halka = sil(x, y, o["z_mil_alt"], o["z_halka_ust"], HALKA_D).cut(sil(x, y, o["z_mil_alt"] - 1, o["z_halka_ust"] + 1, MIL_D))
    for (a, b) in ((y + HALKA_DUZ / 2, y + 20), (y - 20, y - HALKA_DUZ / 2)):    # yağ geçişi için iki düzlük
        halka = halka.cut(kutu(x - 20, x + 20, a, b, o["z_mil_alt"] - 1, o["z_halka_ust"] + 1))
    p.append(("STROK_SONU_HALKASI", halka, "HAREKETLI", "sil_kapak", "PISTON_MILI"))
    # Hortum patlama valfi: doğrudan silindir girişinde; ucunda hortum rakoru (-Y yönüne)
    yv = y - DIP_A / 2 - 32
    p.append(("HORTUM_PATLAMA_VALFI", sil_y(x, zg, yv, y - DIP_A / 2, 22), "HAYALET", "valf", "SILINDIR"))
    rk, uc = rakor((x, yv, zg), (0, -1, 0))
    p.append(("HORTUM_RAKORU_SILINDIR", rk, "HAYALET", "rakor", "SILINDIR"))
    o["giris"] = uc
    o["mil_boy"] = mil_ust_geri - o["z_mil_alt"]
    o["mil_disari_geri"] = mil_ust_geri - o["z_kapak_ust"]
    return p, o


# =====================================================================
# EKSEN YÖNLÜ YARDIMCILAR, RAKOR, HORTUM
# =====================================================================
def dik_vektor(yon):
    y = Vector(*yon).normalized()
    ref = Vector(0, 0, 1) if abs(y.z) < 0.9 else Vector(1, 0, 0)
    return ref.cross(y).normalized()


def eksenel_sil(p0, yon, boy, d):
    return cq.Solid.makeCylinder(d / 2, boy, Vector(*p0), Vector(*yon).normalized())


def alti_kose(p0, yon, boy, anahtar):
    """Altıgen (somun/rakor) — p0'dan yon boyunca boy kadar; anahtar ağzı (düzlükler arası)."""
    pl = cq.Plane(origin=p0, xDir=dik_vektor(yon).toTuple(), normal=Vector(*yon).normalized().toTuple())
    return cq.Workplane(pl).polygon(6, anahtar / math.cos(math.radians(30))).extrude(boy).val()


def rakor(p0, yon, hex_ag=17.0, hex_boy=12.0, bogaz_d=16.0, bogaz_boy=22.0):
    """Hortum rakoru: altıgen somun + sıkma yüksüğü. Dönüş: (katı, hortumun bağlandığı uç noktası)."""
    y = Vector(*yon).normalized()
    a = Vector(*p0)
    govde = alti_kose(a.toTuple(), y.toTuple(), hex_boy, hex_ag)
    bogaz = eksenel_sil((a + y * hex_boy).toTuple(), y.toTuple(), bogaz_boy, bogaz_d)
    uc = a + y * (hex_boy + bogaz_boy)
    return govde.fuse(bogaz).clean(), uc.toTuple()


def hortum_kiv(noktalar, t0, t1, d=HORTUM_D):
    """Kıvrımlı hortum/kablo: noktalardan geçen yumuşak eğri boyunca daire kesit süpürülür."""
    pts = [Vector(*p) for p in noktalar]
    # kiriş boyuyla parametrele (yay uzunluğuna yakın) → birim teğetler tutarlı, eğri kendi üstüne kıvrılmaz
    par = [0.0]
    for a, b in zip(pts, pts[1:]):
        par.append(par[-1] + (b - a).Length)
    e = cq.Edge.makeSpline(pts, tangents=[Vector(*t0).normalized(), Vector(*t1).normalized()],
                           parameters=par, scale=False)
    w = cq.Wire.assembleEdges([e])
    daire = cq.Wire.makeCircle(d / 2, pts[0], e.tangentAt(0))
    return cq.Solid.sweep(daire, [], w, True, False), e.Length()


# =====================================================================
# GÜÇ ÜNİTESİ
# =====================================================================
def motor_71(mx, my, z0):
    """IEC 71 B5 motor, dikey (flanş altta). Tek katı: flanş, ön kapak, kanatlı gövde, arka kapak, fan kapağı,
    arkaya bakan klemens kutusu + kablo rakoru, etiket."""
    z = z0
    parca = sil(mx, my, z, z + MOTOR_FLANS_T, MOTOR_FLANS_D)
    z += MOTOR_FLANS_T
    parca = parca.fuse(sil(mx, my, z, z + MOTOR_ON_H, 128))
    z += MOTOR_ON_H
    zg0, zg1 = z, z + MOTOR_GOVDE_H
    govde = sil(mx, my, zg0, zg1, MOTOR_GOVDE_D - 12)
    for i in range(MOTOR_KANAT_ADET):
        a = 2 * math.pi * i / MOTOR_KANAT_ADET
        kanat = kutu(-1.5, 1.5, (MOTOR_GOVDE_D - 12) / 2 - 2, MOTOR_GOVDE_D / 2, zg0 + 5, zg1 - 5)
        govde = govde.fuse(kanat.rotate(Vector(0, 0, 0), Vector(0, 0, 1), math.degrees(a)).translate(Vector(mx, my, 0)))
    parca = parca.fuse(govde)
    z = zg1
    parca = parca.fuse(sil(mx, my, z, z + MOTOR_ARKA_H, 128))
    z += MOTOR_ARKA_H
    fan = sil(mx, my, z, z + MOTOR_FAN_H, MOTOR_FAN_D)
    for r in (20, 34, 48):                       # fan kapağı ızgarası (üstte halka oluklar)
        fan = fan.cut(sil(mx, my, z + MOTOR_FAN_H - 2, z + MOTOR_FAN_H + 1, 2 * r + 4).cut(
            sil(mx, my, z + MOTOR_FAN_H - 3, z + MOTOR_FAN_H + 2, 2 * r)))
    parca = parca.fuse(fan)
    kx, ky, kz = MOTOR_KLEMENS
    kutu_k = kutu(mx - kx / 2, mx + kx / 2, my + MOTOR_GOVDE_D / 2 - 8, my + MOTOR_GOVDE_D / 2 - 8 + ky,
                  zg0 + 20, zg0 + 20 + kz)
    rakor_k = sil_y(mx + kx / 2 - 20, zg0 + 20 + kz / 2, my + MOTOR_GOVDE_D / 2 - 8 + ky, my + MOTOR_GOVDE_D / 2 + ky + 7, 20)
    parca = parca.fuse(kutu_k, rakor_k)
    etiket = kutu(mx - 30, mx + 30, my - MOTOR_GOVDE_D / 2 - 1, my - MOTOR_GOVDE_D / 2 + 8, zg0 + 50, zg0 + 90)
    parca = parca.fuse(etiket).clean()
    klemens_giris = (mx + kx / 2 - 20, my + MOTOR_GOVDE_D / 2 + ky + 7, zg0 + 20 + kz / 2)
    return parca, z + MOTOR_FAN_H, klemens_giris


def unite(xc, yc, z_taban):
    """Güç ünitesi (görünen kısımlar): ayaklı tava, tank, cıvatalı kapak, çan + IEC 71 motor,
    valf bloğu (iniş valfi bobini + fişi, emniyet valfi, elle indirme, manometre, basınç sensörü, hortum rakoru),
    seviye göstergesi, hava/dolum tapası, boşaltma tapası, etiket. xc, yc: tank merkezi; z_taban: taban sacı üstü."""
    p = []
    z_tava = z_taban + TAVA_AYAK_H
    tx0, tx1 = xc - TAVA_X / 2, xc + TAVA_X / 2
    ty0, ty1 = yc - TAVA_Y / 2, yc + TAVA_Y / 2
    tava = kutu(tx0, tx1, ty0, ty1, z_tava, z_tava + TAVA_Z).cut(
        kutu(tx0 + TAVA_T, tx1 - TAVA_T, ty0 + TAVA_T, ty1 - TAVA_T, z_tava + TAVA_T, z_tava + TAVA_Z + 1))
    p.append(("YAG_TAVASI", tava, "GERCEK", "unite_sac", "GUC_UNITESI"))
    ayaklar = [(xc + sx * TAVA_AYAK_DX, yc + sy * TAVA_AYAK_DY) for sx in (-1, 1) for sy in (-1, 1)]
    for ax, ay in ayaklar:
        p.append((f"TAVA_AYAGI_{ax:.0f}_{ay:.0f}", sil(ax, ay, z_taban, z_tava, 20).cut(sil(ax, ay, z_taban - 1, z_tava + 1, 9)),
                  "GERCEK", "unite_sac", "GUC_UNITESI"))
    zt0 = z_tava + TAVA_T
    zt1 = zt0 + TANK_Z
    kx0, kx1 = xc - TANK_X / 2, xc + TANK_X / 2
    ky0, ky1 = yc - TANK_Y / 2, yc + TANK_Y / 2
    tank = kutu(kx0, kx1, ky0, ky1, zt0, zt1).cut(kutu(kx0 + TANK_T, kx1 - TANK_T, ky0 + TANK_T, ky1 - TANK_T, zt0 + TANK_T, zt1 + 1))
    p.append(("TANK", tank, "GERCEK", "unite_sac", "GUC_UNITESI"))
    zk1 = zt1 + KAPAK_T
    mx, my = xc, yc + MOTOR_EKSEN_DY
    kapak = kutu(kx0 - 10, kx1 + 10, ky0 - 10, ky1 + 10, zt1, zk1).cut(sil(mx, my, zt1 - 1, zk1 + 1, 60))
    p.append(("TANK_KAPAGI", kapak, "GERCEK", "unite_kapak", "GUC_UNITESI"))
    for bx, by in ((kx0 - 3, ky0 - 3), (kx1 + 3, ky0 - 3), (kx0 - 3, ky1 + 3), (kx1 + 3, ky1 + 3), (kx0 - 3, yc), (kx1 + 3, yc)):
        p.append((f"KAPAK_CIVATASI_{bx:.0f}_{by:.0f}", alti_kose((bx, by, zk1), (0, 0, 1), 5.3, 13), "HAYALET", "civata", "GUC_UNITESI"))
    # Çan (kampana): alt flanş + pencereli gövde + üst flanş
    can = sil(mx, my, zk1, zk1 + CAN_FLANS_T, CAN_ALT_D)
    govde = sil(mx, my, zk1 + CAN_FLANS_T, zk1 + CAN_H - CAN_FLANS_T, CAN_GOVDE_D)
    for s in (-1, 1):
        govde = govde.cut(kutu(mx - 22, mx + 22, my + s * 40 - 30, my + s * 40 + 30, zk1 + CAN_FLANS_T + 15, zk1 + CAN_H - CAN_FLANS_T - 12)
                          .cut(sil(mx, my, zk1, zk1 + CAN_H, CAN_GOVDE_D - 16)))
    can = can.fuse(govde, sil(mx, my, zk1 + CAN_H - CAN_FLANS_T, zk1 + CAN_H, CAN_UST_D)).clean()
    p.append(("CAN_KAMPANA", can, "HAYALET", "can", "GUC_UNITESI"))
    motor, motor_tepe, klemens_giris = motor_71(mx, my, zk1 + CAN_H)
    p.append((f"MOTOR_IEC71_B5_{MOTOR_KW:.2f}kW".replace(".", "_"), motor, "HAYALET", "motor", "GUC_UNITESI"))
    # Valf bloğu (kapakta, önde)
    bxc = xc + BLOK_DX
    bx0, bx1 = bxc - BLOK_X / 2, bxc + BLOK_X / 2
    by0, by1 = ky0, ky0 + BLOK_Y
    bt = zk1 + BLOK_Z
    byc = (by0 + by1) / 2
    p.append(("VALF_BLOGU", kutu(bx0, bx1, by0, by1, zk1, bt), "HAYALET", "valf", "GUC_UNITESI"))
    # İniş valfi: kartuş altıgeni + kare bobin + DIN fişi (öne bakar) + üst somun
    sx = bx0 + 20
    p.append(("INIS_VALFI_KARTUSU", alti_kose((sx, byc, bt), (0, 0, 1), 12, 24), "HAYALET", "valf", "GUC_UNITESI"))
    p.append(("INIS_VALFI_BOBINI", kutu(sx - 18, sx + 18, byc - 18, byc + 18, bt + 12, bt + 62), "HAYALET", "bobin", "GUC_UNITESI"))
    p.append(("INIS_VALFI_SOMUNU", sil(sx, byc, bt + 62, bt + 70, 16), "HAYALET", "civata", "GUC_UNITESI"))
    p.append(("INIS_VALFI_FISI_DIN", kutu(sx - 14, sx + 14, byc - 18 - 28, byc - 18, bt + 22, bt + 58), "HAYALET", "fis", "GUC_UNITESI"))
    # Emniyet valfi: +X yüzünde, yatay (altıgen gövde + ayar başlığı)
    ez = zk1 + 30
    p.append(("EMNIYET_VALFI", alti_kose((bx1, byc, ez), (1, 0, 0), 18, 27).fuse(eksenel_sil((bx1 + 18, byc, ez), (1, 0, 0), 25, 18)),
              "HAYALET", "valf", "GUC_UNITESI"))
    # Elle acil indirme: ön yüzde topuz
    p.append(("ELLE_INDIRME", eksenel_sil((bx1 - 20, by0, zk1 + 30), (0, -1, 0), 14, 10)
              .fuse(eksenel_sil((bx1 - 20, by0 - 14, zk1 + 30), (0, -1, 0), 12, 28)), "HAYALET", "fis", "GUC_UNITESI"))
    # Manometre: üstte dik boğaz + öne bakan kadran (Ø63, gliserinli)
    gx, gy = bx1 - 23, by0 + 20
    p.append(("MANOMETRE_BOGAZI", sil(gx, gy, bt, bt + 25, 12), "HAYALET", "valf", "GUC_UNITESI"))
    p.append(("MANOMETRE", sil_y(gx, bt + 25 + 32, gy - 12, gy + 13, 63), "HAYALET", "manometre", "GUC_UNITESI"))
    # Basınç sensörü: üstte arka tarafta
    p.append(("BASINC_SENSORU", sil(bx1 - 20, by1 - 14, bt, bt + 55, 22).fuse(sil(bx1 - 20, by1 - 14, bt + 55, bt + 70, 15)),
              "HAYALET", "fis", "GUC_UNITESI"))
    # Hortum çıkışı (A): -X yüzünde rakor
    rk, blok_cikis = rakor((bx0, byc, zk1 + 45), (-1, 0, 0))
    p.append(("HORTUM_RAKORU_BLOK", rk, "HAYALET", "rakor", "GUC_UNITESI"))
    # Tank donanımı
    p.append(("HAVA_DOLUM_TAPASI", sil(kx0 + 15, byc + 20, zk1, zk1 + 8, 22).fuse(sil(kx0 + 15, byc + 20, zk1 + 8, zk1 + 30, 30)),
              "HAYALET", "fis", "GUC_UNITESI"))
    p.append(("SEVIYE_GOSTERGESI", kutu(kx1 - 50, kx1 - 28, ky0 - 12, ky0, zt0 + 20, zt0 + 150), "HAYALET", "manometre", "GUC_UNITESI"))
    for zz in (zt0 + 30, zt0 + 140):
        p.append((f"SEVIYE_CIVATASI_{zz:.0f}", eksenel_sil((kx1 - 39, ky0 - 12, zz), (0, -1, 0), 6, 12), "HAYALET", "civata", "GUC_UNITESI"))
    p.append(("BOSALTMA_TAPASI", alti_kose((kx0 + 30, ky0, zt0 + 14), (0, -1, 0), 10, 19), "HAYALET", "civata", "GUC_UNITESI"))
    p.append(("UNITE_ETIKETI", kutu(kx0 + 25, kx0 + 95, ky0 - 1, ky0, zt0 + 70, zt0 + 115), "HAYALET", "etiket", "GUC_UNITESI"))
    o = dict(z_tava=z_tava, zt0=zt0, zt1=zt1, zk1=zk1, tepe=motor_tepe, ayaklar=ayaklar, blok_cikis=blok_cikis,
             motor_eksen=(mx, my), klemens_giris=klemens_giris,
             din_fis=(sx, byc - 18 - 28, bt + 40), blok=(bx0, bx1, by0, by1, zk1, bt),
             tank_ic_l=(TANK_X - 2 * TANK_T) * (TANK_Y - 2 * TANK_T) * (TANK_Z - TANK_T) / 1e6)
    return p, o


def kumanda_panosu(x0, y0, z0):
    """İnvertörlü kumanda panosu (kapak öne, -Y), acil stop, mod seçici, ekran, fren direnci (yanda), askı kulakları.
    x0, y0, z0: panonun sol-ön-alt köşesi (kapak y0'da)."""
    p = []
    x1, y1, z1 = x0 + PANO_X, y0 + PANO_Y, z0 + PANO_Z
    p.append(("KUMANDA_PANOSU", kutu(x0, x1, y0, y1, z0, z1), "HAYALET", "pano", "PANO"))
    p.append(("PANO_KAPAGI", kutu(x0 + 5, x1 - 5, y0 - 2, y0, z0 + 5, z1 - 5), "HAYALET", "pano_kapak", "PANO"))
    p.append(("ACIL_STOP", eksenel_sil((x0 + 45, y0 - 2, z1 - 50), (0, -1, 0), 2, 60).fuse(
        eksenel_sil((x0 + 45, y0 - 4, z1 - 50), (0, -1, 0), 22, 40)), "HAYALET", "acil", "PANO"))
    p.append(("MOD_SECICI_KLASIK_KONFOR", eksenel_sil((x0 + 110, y0 - 2, z1 - 50), (0, -1, 0), 20, 28), "HAYALET", "fis", "PANO"))
    p.append(("EKRAN_HIZ_GRAFIGI", kutu(x0 + 30, x0 + 150, y0 - 3, y0 - 2, z0 + 130, z0 + 210), "HAYALET", "ekran", "PANO"))
    p.append(("PANO_KOLU", kutu(x1 - 25, x1 - 15, y0 - 18, y0 - 2, z0 + 120, z0 + 190), "HAYALET", "civata", "PANO"))
    glandlar = []
    for gx in (x0 + 40, x0 + 90, x0 + 140):
        p.append((f"PANO_KABLO_RAKORU_{gx:.0f}", sil(gx, y0 + 75, z0 - 15, z0, 20), "HAYALET", "fis", "PANO"))
        glandlar.append((gx, y0 + 75, z0 - 15))
    p.append(("FREN_DIRENCI", kutu(x1, x1 + 20, y0 + 25, y0 + 65, z0 + 60, z0 + 225), "HAYALET", "direnc", "PANO"))
    for zz in (z0 + 40, z1 - 60):
        p.append((f"PANO_ASKI_KULAGI_{zz:.0f}", kutu(x0 - 7, x0, y0 + 50, y0 + 100, zz, zz + 25), "HAYALET", "civata", "PANO"))
    return p, dict(glandlar=glandlar)


RENKLER = {
    "sil_govde": (0.30, 0.34, 0.40, 1.0),
    "sil_kapak": (0.45, 0.48, 0.55, 1.0),
    "mil": (0.85, 0.87, 0.90, 1.0),
    "valf": (0.78, 0.74, 0.60, 1.0),
    "bobin": (0.10, 0.10, 0.10, 1.0),
    "fis": (0.25, 0.25, 0.28, 1.0),
    "unite_sac": (0.15, 0.42, 0.70, 1.0),
    "unite_kapak": (0.12, 0.35, 0.60, 1.0),
    "motor": (0.16, 0.36, 0.60, 1.0),
    "can": (0.62, 0.64, 0.66, 1.0),
    "manometre": (0.90, 0.92, 0.95, 1.0),
    "etiket": (0.85, 0.85, 0.80, 1.0),
    "pompa": (0.55, 0.55, 0.58, 0.8),
    "cam": (0.60, 0.80, 0.95, 0.6),
    "civata": (0.12, 0.12, 0.12, 1.0),
    "rakor": (0.80, 0.70, 0.25, 1.0),
    "hortum": (0.06, 0.06, 0.06, 1.0),
    "kablo": (0.20, 0.20, 0.20, 1.0),
    "pano": (0.86, 0.87, 0.88, 1.0),
    "pano_kapak": (0.80, 0.82, 0.84, 1.0),
    "acil": (0.85, 0.10, 0.10, 1.0),
    "ekran": (0.05, 0.15, 0.25, 1.0),
    "direnc": (0.70, 0.70, 0.72, 1.0),
}
