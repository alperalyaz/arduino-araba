# -*- coding: utf-8 -*-
"""
MİNİ HİDROLİK ASANSÖR MAKETİ — TABAN SACI + DİKMELER
====================================================
Bu dosya bir TASLAK YERLEŞİM MODELİDİR. Lazere gönderilecek çizim DEĞİLDİR.

Ne çizer?
  * Gerçek parçalar (üretilecek): taban sacı, 4 alt + 4 üst dikme, 12 köşe plakası
    (dikme ayağı + ek flanşı), 4 sökülebilir destek kulağı.
  * Cıvata / somun / pim: basit silindir olarak (çakışma kontrolü için).
  * "Hayalet" hacimler: kabin, askı, raylar, piston, makara, tank vb.
    Bunlar sadece "her şey sığıyor mu?" kontrolü içindir; kesim listesine girmez.

Birimler: mm, kg.  Koordinatlar:
  X = genişlik (0 = sol kenar),  Y = derinlik (0 = ön / kapı tarafı),  Z = yukarı (0 = zemin)

Çalıştırma:
  & "C:\\ardiuno\\.venv-cad\\Scripts\\python.exe" maket_taban_dikme.py
"""
import csv
import math
import os

import cadquery as cq
import numpy as np
from cadquery import Vector

CIKTI = os.path.dirname(os.path.abspath(__file__))
YOGUNLUK = 7.85e-6  # çelik, kg/mm3
import sys
sys.path.insert(0, os.path.join(os.path.dirname(CIKTI), "hidrolik"))
import hidrolik_parcalar as hid   # silindir + güç ünitesi (ortak parametreler ve parça üreticileri)

# =====================================================================
# PARAMETRELER  (değiştirmek için sadece burayı düzenleyin)
# =====================================================================

# --- Taban sacı ---
TABAN_EN = 900          # X
TABAN_DERIN = 600       # Y  (80'lik kapıdan bu kenar geçer)
TABAN_T = 10            # sac kalınlığı
TABAN_KOSE_R = 10       # köşe yuvarlatma (fuarda keskin köşe olmasın)
TEKER_H = 130           # zemin → taban altı. TEKER ALININCA ÖLÇÜP DÜZELTİN

# --- Dikme profili: kutu 40x40x3 (EN 10219) ---
PROFIL_A = 40
PROFIL_T = 3
PROFIL_RO = 6           # dış köşe yarıçapı (≈2t)
PROFIL_RI = 3           # iç köşe yarıçapı (≈t)
TABLO_KG_M = 3.30       # katalog değeri, kontrol için

# --- Köşe plakası (dikme ayağı ve ek flanşı AYNI parça) ---
KOSE_PL = 110
KOSE_PL_T = 10
# Delikler dikmenin DIŞ köşesine göre (x, y) — içe doğru
KOSE_CIVATA = [(85, 35), (85, 85), (35, 85)]   # Ø11, M10 — kuşaklardan uzak, lokma anahtar girsin
KOSE_PIM = [(55, 25), (25, 55)]                # Ø10 pim
CIVATA_DELIK = 11
PIM_D = 10

# --- Taşıma bölmesi ---
BOLME_Z = 1750          # alt modül üst yüzü (zeminden). Kapı 2000 → alt modül ≤ 1950 olmalı
KAPI_H = 2000
KAPI_PAY = 50

# --- Kabin ve kuyu yerleşimi: SIRT ÇANTASI, 2:1 ZİNCİRLİ (kullanıcının ürünü gibi) ---
#   Kılavuzlar ve silindir arka duvarda; askı kılavuzlarda kayar, kabin askıdan öne taşınır.
KUYU_EN = 650
KABIN_EN = 300
KABIN_DERIN = 300
KABIN_H = 350
KABIN_ON_Y = 75         # kabin ön yüzü; ön dikme iç yüzü 40 → eşik boşluğu 35
DURAK_ARASI = 800
DURAK_SAYISI = 3

# Kılavuz: U profil (ağzı kuyunun ortasına bakar), askı makaraları kanalın içinde döner
KILAVUZ_H = 50          # U yüksekliği (Y yönünde)
KILAVUZ_B = 38          # flanş boyu (X yönünde, içe)
KILAVUZ_T = 5
KILAVUZ_Y = 480         # kılavuz ve silindir ekseni (arka duvara yakın)
KILAVUZ_ARASI = 300     # iki U profilin sırt yüzleri arası
KIZAK_MAKARA_D = 30     # askı makarası (U kanalın içinde)

# Askı (sırt çantası)
ASKI_DIKME = 30         # askı dikmesi (X genişliği), U kanalın ağzının hemen içinde
ASKI_ALT_Y = (405, 445)  # askı alt kirişi = zincir bağlantısı, silindirin ÖNÜNDE
ASKI_UST_Y = (375, 405)  # askı üst kirişi, kabinin hemen arkasında (makaraların önünde)
TASIYICI_KOL_X = (30, 60)  # kabin altındaki taşıyıcı kolların kabin kenarından içeri konumu

# --- Yükseklik bütçesi: kabin altındaki yığın ---
RAY_AYAK_H = 50         # kılavuz ayağı (tabana oturan plaka + konsol)
PARASUT_PAY = 20        # paraşüt en altta iken kılavuz ayağına kalan boşluk
ALT_ASIM = 50           # alt durağın altına fazla gidiş (tampon sıkışması dahil)
PARASUT_H = 50          # paraşüt fren bloğu yüksekliği (askı altında)
ASKI_ALT = 60           # kabin tabanı → askı alt kirişinin altı
TAMPON_H = 40           # kauçuk tampon
# --- kabin üstündeki yığın ---
ASKI_UST = 60           # kabin tavanı → askı üst kirişi + üst kızak üstü
UST_ASIM = 50           # üst durağın üstüne fazla gidiş
UST_PAY = 40            # en üst kızak → dikme tepesi

# --- Silindir ve zincir tahriki (2:1): piston başında iki yanda birer zincir makarası ---
PISTON_GOVDE_D = hid.KAFA_D   # silindirin en geniş yeri (kafa Ø55); ayrıntılar hidrolik_parcalar.py'de
PISTON_MIL_D = hid.MIL_D      # dalgıç piston mili Ø20
UNITE_XC, UNITE_YC = 780, 300  # güç ünitesi tankının merkezi
MAKARA_D = 120          # zincir makarası bölüm dairesi (≥Ø120: zincir titreşimi az olsun)
MAKARA_GEN = 16
ZINCIR_X_OFS = 38       # makaraların silindir eksenine uzaklığı (sağ/sol)
ZINCIR_KAL = 8          # zincir kalınlığı (görsel/kontrol)
BASLIK_ALT = 40         # makara ekseni → piston başlığının altı
MAKARA_MARJ = 50        # en üstte askı alt kirişi ile makara arası boşluk
SILINDIR_OLU_PAY = 10   # piston tam içerdeyken başlık ile silindir kafası arası
SABIT_UC_PAY = 15       # arka zincir kolu → arka kuşak arası (gergi saplaması için)

# --- İskelet: her modül kendi içinde KAYNAKLI kafes (ürün gibi) ---
KUSAK_H = 40            # kuşak kutu 40x20x2: 40 dikey
KUSAK_D = 20            #                     20 derin (dış yüzü dikmeyle aynı hizada; paneller düz otursun)
KUSAK_T = 2
KUSAK_RO, KUSAK_RI = 4, 2
TABLO_KUSAK_KG_M = 1.68  # EN 10219 40x20x2
CAPRAZ_A = 20           # çapraz kutu 20x20x2, kuşakla aynı düzlemde, düğümlere kaynaklı
CAPRAZ_T = 2
CAPRAZ_RO, CAPRAZ_RI = 4, 2
TABLO_CAPRAZ_KG_M = 1.05  # EN 10219 20x20x2
KAPI_ACIKLIK = 330      # kat kapısı açıklık yüksekliği (durak tabanından); ön yüzde bu aralıkta kuşak olmaz
BOSLUK_MIN = 5          # hareketli parçalar ile sabit parçalar arasında en az boşluk

# --- Kat kapıları: yarı otomatik, menteşeli, dışa açılır (ürün gibi) ---
KAPI_NET_W = 180        # net geçiş genişliği (kabin kapısıyla aynı)
KAPI_NET_H = 310        # net geçiş yüksekliği (durak seviyesinden)
KAPI_SAG_PAY = 5        # kapı açıklığının sağ kenarı = kabin sağ duvarı - bu pay (kilit kabinin yanına sığsın)
KASA_P = 30             # kasa yüz genişliği (2 mm bükme sac U)
KASA_D = 40             # kasa derinliği (y 0..40)
KANAT_T = 20            # kanat (1,5 mm sac tepsi) kalınlığı, kasanın önünde y -20..0
KANAT_BINDIRME = (10, 25)   # kanadın kasaya bindirmesi: menteşe tarafı, kilit tarafı
ESIK_H = 15             # alüminyum eşik yüksekliği
ESIK_Y1 = 45            # eşiğin kuyu tarafı kenarı (kabin önüyle arası ≤35 olmalı)
PENCERE = (30, 180)     # kanattaki dar cam (genişlik, yükseklik)
# Gerçek standart kilit (kullanıcının ürünündeki); ölçüler yaklaşık — KİLİT ALINCA ÖLÇÜN
KILIT_W, KILIT_D, KILIT_H = 45, 45, 180
KILIT_Z_OFS = 110       # kilit gövdesinin altı, durak seviyesinden
KILIT_MAKARA_Z = 195    # kilit makarası ekseni, durak seviyesinden
KAM_BOSLUK = 10         # geri çekik kam ile kilit makarası arası
KAM_BOY = 120
# Otomatik kabin kapısı (2 kanat teleskopik, yana açılır) + kabin etek sacı
KABIN_KAPI_T = 6
KABIN_KAPI_OPERATOR_H = 50
ETEK_H = 115            # kabin etek sacı (apron) yüksekliği

# --- Sökülebilir destek kulağı (devrilmeye karşı, fuarda takılır) ---
KULAK_GEN = 120
KULAK_TASMA = 200       # tabandan dışarı taşan kısım
KULAK_ICERI = 190       # tabanın altına giren kısım
KULAK_T = 15
KULAK_CIVATA = [(25, 130), (95, 130), (25, 165), (95, 165)]  # tabanın köşesine göre
KULAK_AYAK = (60, -170)         # M16 ayar ayağı deliği
KULAK_AYAK_DELIK = 17
KULAK_CEP_D = 24                # dikme ayak somunları için boşluk cebi

# --- Teker (TEKER ALINMADAN DELİK KESMEYİN) ---
TEKER_MERKEZ = [(200, 75), (200, 525), (710, 75), (710, 525)]
TEKER_TABLA = (100, 85)
TEKER_DELIK = (80, 60)
TEKER_OFSET = 35        # döner tekerin kaçıklığı
TEKER_D = 100

# --- Hayaletlere TAHMİNİ kütleler (devrilme hesabı için) ---
KUTLE = {
    "kabin + askı + paraşüt": 45.0,
    "piston başı + zincirler + terazi": 6.0,
    "motor (IEC 71) + pompa + çan + valf bloğu": 11.0,
    "hidrolik yağ (~5 L)": 4.4,
    "şeffaf paneller (ileride)": 30.0,
    "kat kapıları (ileride)": 10.0,
    "kumanda panosu + invertör + fren direnci": 7.0,
    "teker x4": 6.0,
    "ayar ayağı x4": 2.4,
}

# =====================================================================
# TÜRETİLEN ÖLÇÜLER
# =====================================================================
TABAN_UST = TEKER_H + TABAN_T                     # taban sacı üst yüzü
KABIN_MX = KUYU_EN / 2
KABIN_X0 = KABIN_MX - KABIN_EN / 2
KABIN_X1 = KABIN_MX + KABIN_EN / 2
KABIN_Y1 = KABIN_ON_Y + KABIN_DERIN
SOL_KILAVUZ_SIRT = KABIN_MX - KILAVUZ_ARASI / 2   # U profil sırtı (dış yüz)
SAG_KILAVUZ_SIRT = KABIN_MX + KILAVUZ_ARASI / 2
KANAL_Y = (KILAVUZ_Y - KILAVUZ_H / 2 + KILAVUZ_T, KILAVUZ_Y + KILAVUZ_H / 2 - KILAVUZ_T)  # kanal içi
ASKI_X_SOL = (SOL_KILAVUZ_SIRT + KILAVUZ_B + BOSLUK_MIN, SOL_KILAVUZ_SIRT + KILAVUZ_B + BOSLUK_MIN + ASKI_DIKME)
ASKI_X_SAG = (SAG_KILAVUZ_SIRT - KILAVUZ_B - BOSLUK_MIN - ASKI_DIKME, SAG_KILAVUZ_SIRT - KILAVUZ_B - BOSLUK_MIN)
SILINDIR_Y = KILAVUZ_Y
ZINCIR_X = (KABIN_MX - ZINCIR_X_OFS, KABIN_MX + ZINCIR_X_OFS)
ARKA_KUSAK_Y = TABAN_DERIN - KUSAK_D              # arka kuşağın iç yüzü (konsollar, kelepçe buraya)

# Çukur: iki yığından büyüğü
yigin_parasut = RAY_AYAK_H + PARASUT_PAY + ALT_ASIM + PARASUT_H + ASKI_ALT
yigin_tampon = TAMPON_H + ALT_ASIM + ASKI_ALT
CUKUR = max(yigin_parasut, yigin_tampon)
Z0 = TABAN_UST + CUKUR                            # 1. durak kabin tabanı
DURAKLAR = [Z0 + i * DURAK_ARASI for i in range(DURAK_SAYISI)]
YOL = DURAK_ARASI * (DURAK_SAYISI - 1)
ASKI_UST_ENUST = DURAKLAR[-1] + KABIN_H + ASKI_UST + UST_ASIM
Z_TEPE = int(math.ceil((ASKI_UST_ENUST + UST_PAY) / 10.0) * 10)
RAY_UST = Z_TEPE - 10
STROK = (YOL + ALT_ASIM + UST_ASIM) / 2

# Dikme boyları
AYAK_UST = TABAN_UST + KOSE_PL_T                  # alt dikme başlangıcı
DIKME_ALT_BOY = BOLME_Z - KOSE_PL_T - AYAK_UST
DIKME_UST_BOY = Z_TEPE - (BOLME_Z + KOSE_PL_T)

# Kuşak kotları (kuşağın ALT yüzü, z). Ön yüz kapılara göre; yan/arka yüzler çaprazlara göre.
KUSAK = {
    "R1": DURAKLAR[0] - KUSAK_H,                   # 1. durak eşiği
    "R2": DURAKLAR[0] + KAPI_ACIKLIK + 10,         # 1. kapı üstü
    "R3": DURAKLAR[1] - KUSAK_H,                   # 2. durak eşiği (silindir kelepçesi)
    "R4": DURAKLAR[1] + KAPI_ACIKLIK + 10,         # 2. kapı üstü (sadece ön)
    "R5": BOLME_Z - KOSE_PL_T - KUSAK_H,           # alt modülün tepesi, flanşın hemen altı
    "R6": BOLME_Z + KOSE_PL_T,                     # üst modülün dibi, flanşın hemen üstü
    "R7": DURAKLAR[2] - KUSAK_H,                   # 3. durak eşiği (sadece ön)
    "R8": DURAKLAR[2] + KAPI_ACIKLIK + 10,         # 3. kapı üstü (sadece ön)
    "R9": Z_TEPE - KUSAK_H,                        # tepe
}
YUZ_KUSAKLARI = {
    "ON": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"],
    "SOL": ["R1", "R2", "R3", "R5", "R6", "R9"],
    "SAG": ["R1", "R2", "R3", "R5", "R6", "R9"],
    "ARKA": ["R1", "R2", "R3", "R5", "R6", "R9"],
}
CAPRAZ_PANELLERI = [("R1", "R2"), ("R2", "R3"), ("R3", "R5"), ("R6", "R9")]   # yan + arka yüzlerde
KONSOL_KOTLARI = ["R1", "R2", "R3", "R5", "R6", "R9"]                         # kılavuz konsolları (arka)

def modul(r):
    return "ALT" if KUSAK[r] + KUSAK_H <= BOLME_Z else "UST"


# Kat kapısı yerleşimi (X): açıklık kabinin sağ tarafına yakın, kilit kabinin sağ yanında
KAPI_X1 = KABIN_X1 - KAPI_SAG_PAY                 # açıklık sağ kenarı
KAPI_X0 = KAPI_X1 - KAPI_NET_W                    # açıklık sol kenarı
KASA_X = (KAPI_X0 - KASA_P, KAPI_X1 + KASA_P)     # kasanın dış kenarları
KANAT_X = (KAPI_X0 - KANAT_BINDIRME[0], KAPI_X1 + KANAT_BINDIRME[1])
KILIT_MAKARA_X0 = KABIN_X1 + KAM_BOSLUK + 3       # geri çekik kam 3 mm kalın
KILIT_X = (KILIT_MAKARA_X0 + 5, KILIT_MAKARA_X0 + 5 + KILIT_W)
KAPI_UST_KUSAK = {DURAKLAR[0]: "R2", DURAKLAR[1]: "R4", DURAKLAR[2]: "R8"}
assert KILIT_X[0] <= KASA_X[1], "Kilit kasanın kilit tarafı kenarına oturmuyor"
assert KILIT_X[1] + 20 <= KUYU_EN - PROFIL_A, "Kilit sağ ön dikmeye çok yakın"
assert KAPI_X0 - KAPI_NET_W / 2 >= KABIN_X0 + 5, "Kabin kapısı kanatları kabinin içinde toplanamıyor"
assert KABIN_ON_Y - ESIK_Y1 <= 35, "Eşik boşluğu 35 mm'yi aşıyor"
for s, r in KAPI_UST_KUSAK.items():
    assert s + KAPI_NET_H + KASA_P <= KUSAK[r], f"{s} durağının kasası üst kuşağa ({r}) sığmıyor"

# Kapı açıklıkları temiz mi, kuşaklar üst üste biniyor mu, çaprazlar bölmeyi geçiyor mu?
for s in DURAKLAR:
    for r in YUZ_KUSAKLARI["ON"]:
        assert not (KUSAK[r] < s + KAPI_ACIKLIK and KUSAK[r] + KUSAK_H > s), f"{r} kuşağı {s} durağının kapısını kesiyor"
for yuz, rr in YUZ_KUSAKLARI.items():
    zs = sorted(KUSAK[r] for r in rr)
    assert all(b - a >= KUSAK_H for a, b in zip(zs, zs[1:])), f"{yuz} yüzünde kuşaklar üst üste"
for a, b in CAPRAZ_PANELLERI:
    assert modul(a) == modul(b), f"{a}-{b} çaprazı bölmeyi geçiyor"
    assert KUSAK[b] - (KUSAK[a] + KUSAK_H) >= 300, f"{a}-{b} paneli çok basık, çapraz yatay kalır"

# Zincir kolları ve piston başı
ZINCIR_ON_Y = SILINDIR_Y - MAKARA_D / 2           # kabine (askı alt kirişine) inen kol
ZINCIR_ARKA_Y = SILINDIR_Y + MAKARA_D / 2         # tabandaki sabit uca inen kol
MAKARA_R = MAKARA_D / 2 + 5                       # makaranın dış yarıçapı
KANCA_Z0 = Z0 - 20                                # askı alt kirişi üstü (zincir bağlantısı), 1. durakta
KABIN_MAKS_YUKSELME = YOL + UST_ASIM
MAKARA_Z0 = KANCA_Z0 + KABIN_MAKS_YUKSELME / 2 + MAKARA_R + MAKARA_MARJ
MAKARA_Z_MIN = MAKARA_Z0 - ALT_ASIM / 2
MAKARA_Z_MAX = MAKARA_Z0 + KABIN_MAKS_YUKSELME / 2
SIL_OLCU = hid.silindir_olculer(TEKER_H + TABAN_T, STROK)
SILINDIR_UST = SIL_OLCU["z_kapak_ust"]               # silindir kafa kapağının üstü
assert SILINDIR_UST + SILINDIR_OLU_PAY <= MAKARA_Z_MIN - BASLIK_ALT, "Silindir kafası piston başına çarpar"
PISTON_Y = SILINDIR_Y
CATAL_ALT = BASLIK_ALT

# --- Yerleşim zinciri kontrolleri (Y ve X payları; taşarsa dur) ---
assert KUYU_EN < TABAN_EN
assert KABIN_Y1 <= ASKI_UST_Y[0], "Kabin arkası askı üst kirişine giriyor"
assert ASKI_UST_Y[1] + 5 <= SILINDIR_Y - MAKARA_R, "Askı üst kirişi zincir makaralarına çarpar"
assert ASKI_ALT_Y[1] + 5 <= SILINDIR_Y - PISTON_GOVDE_D / 2, "Askı alt kirişi silindire çarpar"
assert ASKI_ALT_Y[0] + 10 <= ZINCIR_ON_Y <= ASKI_ALT_Y[1] - 10, "Ön zincir kolu askı alt kirişine denk gelmiyor"
assert ZINCIR_ARKA_Y + ZINCIR_KAL / 2 + SABIT_UC_PAY <= ARKA_KUSAK_Y, "Arka zincir kolu arka kuşağa çok yakın"
assert KILAVUZ_Y + KILAVUZ_H / 2 + 20 <= ARKA_KUSAK_Y, "Kılavuz konsoluna yer yok"
assert ZINCIR_X[0] - MAKARA_GEN / 2 - 15 >= ASKI_X_SOL[1], "Zincir makarası askı dikmesine çok yakın"
assert KANAL_Y[1] - KANAL_Y[0] >= KIZAK_MAKARA_D + 4, "Askı makarası U kanala sığmıyor"

# =====================================================================
# YARDIMCI FONKSİYONLAR
# =====================================================================


def kutu(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def silindir(x, y, z0, z1, d, eksen="Z"):
    if eksen == "Z":
        return cq.Solid.makeCylinder(d / 2, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))
    if eksen == "X":  # x=z0..z1, merkez (y, z)=(x, y) parametreleri
        return cq.Solid.makeCylinder(d / 2, z1 - z0, Vector(z0, x, y), Vector(1, 0, 0))
    raise ValueError(eksen)


def halka(x, y, z0, z1, d_dis, d_ic):
    return silindir(x, y, z0, z1, d_dis).cut(silindir(x, y, z0 - 1, z1 + 1, d_ic))


def kose_donustur(sekil, cx, cy, sx, sy):
    """Yerel köşe koordinatındaki (içe doğru +x, +y) parçayı ilgili köşeye taşır."""
    s = sekil
    if sx < 0:
        s = s.mirror("YZ")
    if sy < 0:
        s = s.mirror("XZ")
    return s.translate(Vector(cx, cy, 0))


def kose_nokta(p, cx, cy, sx, sy):
    return (cx + sx * p[0], cy + sy * p[1])


def kutu_profil(x0, y0, z0, boy):
    a = PROFIL_A
    dis = cq.Workplane("XY").rect(a, a).extrude(boy).edges("|Z").fillet(PROFIL_RO)
    ic = cq.Workplane("XY").rect(a - 2 * PROFIL_T, a - 2 * PROFIL_T).extrude(boy).edges("|Z").fillet(PROFIL_RI)
    return dis.cut(ic).val().translate(Vector(x0 + a / 2, y0 + a / 2, z0))


def civata_ustten(x, y, z_yuzey, boy):
    """Başı z_yuzey üstünde, gövdesi aşağı giden M10 cıvata."""
    return silindir(x, y, z_yuzey, z_yuzey + 6.4, 17).fuse(silindir(x, y, z_yuzey - boy, z_yuzey, 9.8))


def civata_alttan(x, y, z_yuzey, boy):
    """Başı z_yuzey altında, gövdesi yukarı giden M10 cıvata."""
    return silindir(x, y, z_yuzey - 6.4, z_yuzey, 17).fuse(silindir(x, y, z_yuzey, z_yuzey + boy, 9.8))


def somun_pul(x, y, z_ust):
    """Pul (2) + somun (8) = 10 mm, üst yüzü z_ust."""
    return halka(x, y, z_ust - 10, z_ust, 20, 10)


# =====================================================================
# PARÇA LİSTESİ
# =====================================================================
parcalar = []   # dict: ad, sekil, tur, renk, grup
#   tur: GERCEK | BAGLANTI | HAYALET | HAREKETLI | ZARF | HALAT

RENK = {
    "taban": (0.42, 0.44, 0.47, 1.0),
    "dikme": (0.16, 0.38, 0.72, 1.0),
    "kusak": (0.22, 0.50, 0.85, 1.0),
    "capraz": (0.45, 0.68, 0.92, 1.0),
    "kasa": (0.55, 0.30, 0.25, 1.0),
    "kanat": (0.93, 0.88, 0.72, 1.0),
    "esik": (0.75, 0.76, 0.78, 1.0),
    "cam": (0.60, 0.80, 0.95, 0.45),
    "kilit": (0.85, 0.70, 0.10, 1.0),
    "kabin_kapi": (0.80, 0.80, 0.82, 0.6),
    "kose": (0.10, 0.25, 0.50, 1.0),
    "kulak": (0.93, 0.55, 0.13, 1.0),
    "civata": (0.12, 0.12, 0.12, 1.0),
    "pim": (0.55, 0.20, 0.60, 1.0),
    "kaynak_somun": (0.25, 0.25, 0.25, 1.0),
    "teker": (0.20, 0.20, 0.22, 0.9),
    "ayak": (0.30, 0.30, 0.30, 0.9),
    "ray": (0.35, 0.35, 0.38, 0.55),
    "klips": (0.60, 0.60, 0.65, 0.18),
    "kabin": (0.98, 0.85, 0.35, 0.35),
    "aski": (0.55, 0.55, 0.60, 0.55),
    "parasut": (0.85, 0.20, 0.20, 0.55),
    "piston": (0.75, 0.75, 0.80, 0.60),
    "makara": (0.85, 0.15, 0.15, 0.70),
    "halat": (0.10, 0.10, 0.10, 0.80),
    "tank": (0.20, 0.60, 0.30, 0.35),
    "motor": (0.20, 0.45, 0.25, 0.45),
    "tampon": (0.10, 0.10, 0.10, 0.60),
    "yer_tutucu": (0.70, 0.70, 0.70, 0.30),
}


RENK = {**RENK, **hid.RENKLER}      # hidrolik parçaların renkleri öncelikli


def ekle(ad, sekil, tur, renk, grup=None):
    parcalar.append({"ad": ad, "sekil": sekil, "tur": tur, "renk": RENK[renk], "renk_ad": renk, "grup": grup or ad})


DIKME_KOSELERI = {
    "SOL_ON": (0, 0, 1, 1),
    "SOL_ARKA": (0, TABAN_DERIN, 1, -1),
    "SAG_ON": (KUYU_EN, 0, -1, 1),
    "SAG_ARKA": (KUYU_EN, TABAN_DERIN, -1, -1),
}
TABAN_KOSELERI = {
    "SOL_ON": (0, 0, 1, 1),
    "SOL_ARKA": (0, TABAN_DERIN, 1, -1),
    "SAG_ON": (TABAN_EN, 0, -1, 1),
    "SAG_ARKA": (TABAN_EN, TABAN_DERIN, -1, -1),
}

# ---------------------------------------------------------------------
# 1) TABAN SACI ve delik tablosu
# ---------------------------------------------------------------------
delikler = []   # (x, y, çap, görev)
for k, (cx, cy, sx, sy) in DIKME_KOSELERI.items():
    for p in KOSE_CIVATA:
        delikler.append((*kose_nokta(p, cx, cy, sx, sy), CIVATA_DELIK, f"dikme ayağı M10 ({k})"))
    for p in KOSE_PIM:
        delikler.append((*kose_nokta(p, cx, cy, sx, sy), PIM_D, f"pim Ø10 ({k})"))
for (tx, ty) in TEKER_MERKEZ:
    for dx in (-TEKER_DELIK[0] / 2, TEKER_DELIK[0] / 2):
        for dy in (-TEKER_DELIK[1] / 2, TEKER_DELIK[1] / 2):
            delikler.append((tx + dx, ty + dy, CIVATA_DELIK, "teker M10"))
for k, (cx, cy, sx, sy) in TABAN_KOSELERI.items():
    for p in KULAK_CIVATA:
        delikler.append((*kose_nokta(p, cx, cy, sx, sy), CIVATA_DELIK, f"destek kulağı M10 + üstte kaynak somunu ({k})"))
for dx in (-hid.AYAK_DELIK_ARA / 2, hid.AYAK_DELIK_ARA / 2):
    for dy in (-hid.AYAK_DELIK_ARA / 2, hid.AYAK_DELIK_ARA / 2):
        delikler.append((KABIN_MX + dx, SILINDIR_Y + dy, 9, "silindir ayağı M8"))
for ax in (UNITE_XC - hid.TAVA_AYAK_DX, UNITE_XC + hid.TAVA_AYAK_DX):
    for ay in (UNITE_YC - hid.TAVA_AYAK_DY, UNITE_YC + hid.TAVA_AYAK_DY):
        delikler.append((ax, ay, 9, "yağ tavası ayağı M8"))

taban_wp = cq.Workplane("XY").box(TABAN_EN, TABAN_DERIN, TABAN_T, centered=False).edges("|Z").fillet(TABAN_KOSE_R)
taban = taban_wp.val()
delik_silindirleri = [silindir(x, y, -1, TABAN_T + 1, d) for (x, y, d, _) in delikler]
taban = taban.cut(*delik_silindirleri).translate(Vector(0, 0, TEKER_H))
ekle("TABAN_SACI", taban, "GERCEK", "taban")

# Delikler birbirine çok yakın mı?
for i in range(len(delikler)):
    for j in range(i + 1, len(delikler)):
        a, b = delikler[i], delikler[j]
        ara = math.hypot(a[0] - b[0], a[1] - b[1]) - (a[2] + b[2]) / 2
        assert ara > 8, f"Delikler çok yakın: {a} {b} ({ara:.1f} mm et)"
for (x, y, d, g) in delikler:
    kenar = min(x, y, TABAN_EN - x, TABAN_DERIN - y) - d / 2
    assert kenar >= 8, f"Delik kenara çok yakın: {(x, y, g)} ({kenar:.1f} mm)"

# ---------------------------------------------------------------------
# 2) KÖŞE PLAKASI (yerel) + DİKMELER
# ---------------------------------------------------------------------
kose_yerel = kutu(0, KOSE_PL, 0, KOSE_PL, 0, KOSE_PL_T)
kose_yerel = kose_yerel.cut(
    *[silindir(x, y, -1, KOSE_PL_T + 1, CIVATA_DELIK) for (x, y) in KOSE_CIVATA],
    *[silindir(x, y, -1, KOSE_PL_T + 1, PIM_D) for (x, y) in KOSE_PIM],
)
KOSE_PL_KG = kose_yerel.Volume() * YOGUNLUK

kose_z = {
    "AYAK": TABAN_UST,                       # 140..150
    "EK_ALT": BOLME_Z - KOSE_PL_T,           # 1740..1750
    "EK_UST": BOLME_Z,                       # 1750..1760
}
for k, (cx, cy, sx, sy) in DIKME_KOSELERI.items():
    for rol, z in kose_z.items():
        ekle(f"KOSE_PLAKASI_{rol}_{k}", kose_donustur(kose_yerel, cx, cy, sx, sy).translate(Vector(0, 0, z)),
             "GERCEK", "kose")
    x0 = cx if sx > 0 else cx - PROFIL_A
    y0 = cy if sy > 0 else cy - PROFIL_A
    ekle(f"DIKME_ALT_{k}", kutu_profil(x0, y0, AYAK_UST, DIKME_ALT_BOY), "GERCEK", "dikme")
    ekle(f"DIKME_UST_{k}", kutu_profil(x0, y0, BOLME_Z + KOSE_PL_T, DIKME_UST_BOY), "GERCEK", "dikme")

    # Bağlantılar: ayak cıvatası (üstten, somun taban altında) ve ek flanşı cıvatası
    for p in KOSE_CIVATA:
        x, y = kose_nokta(p, cx, cy, sx, sy)
        ekle(f"CIVATA_AYAK_{k}_{p}", civata_ustten(x, y, AYAK_UST, 35), "BAGLANTI", "civata", "CIVATA_DIKME_AYAGI")
        ekle(f"SOMUN_AYAK_{k}_{p}", somun_pul(x, y, TEKER_H), "BAGLANTI", "civata", "CIVATA_DIKME_AYAGI")
        # Ek flanşı: cıvata sadece üstten takılır, alt flanşın altında kaynak somunu var
        ekle(f"CIVATA_EK_{k}_{p}", civata_ustten(x, y, BOLME_Z + KOSE_PL_T, 30), "BAGLANTI", "civata", "CIVATA_EK_FLANSI")
        ks = kutu(x - 8.5, x + 8.5, y - 8.5, y + 8.5, BOLME_Z - KOSE_PL_T - 8, BOLME_Z - KOSE_PL_T).cut(
            silindir(x, y, BOLME_Z - KOSE_PL_T - 9, BOLME_Z - KOSE_PL_T + 1, 10))
        ekle(f"KAYNAK_SOMUNU_EK_{k}_{p}", ks, "BAGLANTI", "kaynak_somun", "KAYNAK_SOMUNLARI")
    for p in KOSE_PIM:
        x, y = kose_nokta(p, cx, cy, sx, sy)
        ekle(f"PIM_AYAK_{k}_{p}", silindir(x, y, TEKER_H, AYAK_UST, 9.8), "BAGLANTI", "pim", "PIMLER")
        ekle(f"PIM_EK_{k}_{p}", silindir(x, y, BOLME_Z - KOSE_PL_T, BOLME_Z + KOSE_PL_T, 9.8), "BAGLANTI", "pim", "PIMLER")

# ---------------------------------------------------------------------
# 3) DESTEK KULAKLARI (yerel: tabanın köşesi (0,0), içe +x +y, dışa -y)
# ---------------------------------------------------------------------
kulak_yerel = kutu(0, KULAK_GEN, -KULAK_TASMA, KULAK_ICERI, 0, KULAK_T)
kulak_yerel = kulak_yerel.cut(
    *[silindir(x, y, -1, KULAK_T + 1, CIVATA_DELIK) for (x, y) in KULAK_CIVATA],
    *[silindir(x, y, -1, KULAK_T + 1, KULAK_CEP_D) for (x, y) in KOSE_CIVATA],
    silindir(KULAK_AYAK[0], KULAK_AYAK[1], -1, KULAK_T + 1, KULAK_AYAK_DELIK),
)
KULAK_KG = kulak_yerel.Volume() * YOGUNLUK
KULAK_Z0 = TEKER_H - KULAK_T
for k, (cx, cy, sx, sy) in TABAN_KOSELERI.items():
    ekle(f"DESTEK_KULAGI_{k}", kose_donustur(kulak_yerel, cx, cy, sx, sy).translate(Vector(0, 0, KULAK_Z0)),
         "GERCEK", "kulak")
    for p in KULAK_CIVATA:
        x, y = kose_nokta(p, cx, cy, sx, sy)
        ekle(f"CIVATA_KULAK_{k}_{p}", civata_alttan(x, y, KULAK_Z0, 35), "BAGLANTI", "civata", "CIVATA_KULAK")
        ks = kutu(x - 8.5, x + 8.5, y - 8.5, y + 8.5, TABAN_UST, TABAN_UST + 8).cut(silindir(x, y, TABAN_UST - 1, TABAN_UST + 9, 10))
        ekle(f"KAYNAK_SOMUNU_{k}_{p}", ks, "BAGLANTI", "kaynak_somun", "KAYNAK_SOMUNLARI")
    # Ayar ayağı (satın alma, yer tutucu)
    ax, ay = kose_nokta(KULAK_AYAK, cx, cy, sx, sy)
    ayak = silindir(ax, ay, 0, 15, 80).fuse(silindir(ax, ay, 15, TEKER_H + 13, 16))
    ekle(f"AYAR_AYAGI_{k}", ayak, "HAYALET", "ayak", "AYAR_AYAKLARI")
    ekle(f"AYAK_SOMUN_ALT_{k}", halka(ax, ay, KULAK_Z0 - 13, KULAK_Z0, 26, 16.2), "HAYALET", "ayak", "AYAR_AYAKLARI")
    ekle(f"AYAK_SOMUN_UST_{k}", halka(ax, ay, TEKER_H, TEKER_H + 13, 26, 16.2), "HAYALET", "ayak", "AYAR_AYAKLARI")

# ---------------------------------------------------------------------
# 4) TEKERLER (satın alma; tabla + döner yatak + tekerin dönme zarfı)
# ---------------------------------------------------------------------
for i, (tx, ty) in enumerate(TEKER_MERKEZ, 1):
    tw, td = TEKER_TABLA
    tabla = kutu(tx - tw / 2, tx + tw / 2, ty - td / 2, ty + td / 2, TEKER_H - 5, TEKER_H)
    pts = [(tx + dx, ty + dy) for dx in (-TEKER_DELIK[0] / 2, TEKER_DELIK[0] / 2) for dy in (-TEKER_DELIK[1] / 2, TEKER_DELIK[1] / 2)]
    tabla = tabla.cut(*[silindir(x, y, TEKER_H - 6, TEKER_H + 1, CIVATA_DELIK) for (x, y) in pts])
    ekle(f"TEKER_{i}_TABLA", tabla.fuse(silindir(tx, ty, TEKER_D + 5, TEKER_H - 5, 70)), "HAYALET", "teker", "TEKERLER")
    r_don = math.hypot(TEKER_OFSET + TEKER_D / 2, 16)
    ekle(f"TEKER_{i}_DONME_ZARFI", silindir(tx, ty, 0, TEKER_D + 5, 2 * r_don), "ZARF", "teker", "TEKERLER")
    for (x, y) in pts:
        ekle(f"CIVATA_TEKER_{i}_{x}_{y}", civata_ustten(x, y, TABAN_UST, 30), "BAGLANTI", "civata", "CIVATA_TEKER")
        ekle(f"SOMUN_TEKER_{i}_{x}_{y}", somun_pul(x, y, TEKER_H - 5), "BAGLANTI", "civata", "CIVATA_TEKER")

# ---------------------------------------------------------------------
# 4b) KAFES: KUŞAKLAR + ÇAPRAZLAR (her modül kendi içinde kaynaklı, ürün gibi)
# ---------------------------------------------------------------------
def kutu_boru(eksen, boy, en_u, en_v, t, ro, ri):
    """Dikdörtgen kutu profil, 'X' ya da 'Y' ekseni boyunca 0..boy.
    en_u: eksene dik yatay ölçü, en_v: dikey ölçü (Z). Kesit merkezi (0, 0)."""
    if eksen == "X":
        dis = cq.Workplane("YZ").rect(en_u, en_v).extrude(boy).edges("|X").fillet(ro)
        ic = cq.Workplane("YZ").rect(en_u - 2 * t, en_v - 2 * t).extrude(boy).edges("|X").fillet(ri)
    else:
        dis = cq.Workplane("XZ").rect(en_u, en_v).extrude(-boy).edges("|Y").fillet(ro)
        ic = cq.Workplane("XZ").rect(en_u - 2 * t, en_v - 2 * t).extrude(-boy).edges("|Y").fillet(ri)
    return dis.cut(ic).val()


KAFES_BOY_X = KUYU_EN - 2 * PROFIL_A        # ön/arka kuşak boyu (dikmeler arası)
KAFES_BOY_Y = TABAN_DERIN - 2 * PROFIL_A    # yan kuşak boyu
kusak_x = kutu_boru("X", KAFES_BOY_X, KUSAK_D, KUSAK_H, KUSAK_T, KUSAK_RO, KUSAK_RI)
kusak_y = kutu_boru("Y", KAFES_BOY_Y, KUSAK_D, KUSAK_H, KUSAK_T, KUSAK_RO, KUSAK_RI)
KUSAK_KG_M = kusak_x.Volume() / KAFES_BOY_X * 1000 * YOGUNLUK
YUZ_YERI = {   # (şekil, x kayması, y kayması) — dış yüz dikmenin dış yüzüyle aynı hizada
    "ON": (kusak_x, PROFIL_A, KUSAK_D / 2),
    "ARKA": (kusak_x, PROFIL_A, TABAN_DERIN - KUSAK_D / 2),
    "SOL": (kusak_y, KUSAK_D / 2, PROFIL_A),
    "SAG": (kusak_y, KUYU_EN - KUSAK_D / 2, PROFIL_A),
}
kusak_kutulari = {}
for yuz, rr in YUZ_KUSAKLARI.items():
    sek, dx, dy = YUZ_YERI[yuz]
    for r in rr:
        s = sek.translate(Vector(dx, dy, KUSAK[r] + KUSAK_H / 2))
        ekle(f"KUSAK_{modul(r)}_{yuz}_{r}", s, "GERCEK", "kusak")
        b = s.BoundingBox()
        kusak_kutulari[(yuz, r)] = kutu(b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def dikme_kutusu(x0, y0):
    return kutu(x0, x0 + PROFIL_A, y0, y0 + PROFIL_A, 0, Z_TEPE + 10)


# Çaprazlar: yan ve arka yüzlerde zikzak; uçlar dikme ve kuşak yüzlerine göre açılı kesilir
UZATMA = 40
capraz_bilgi = []
CAPRAZ_KG_M = None
for yuz in ("SOL", "SAG", "ARKA"):
    if yuz == "ARKA":
        u_min, u_max = PROFIL_A, KUYU_EN - PROFIL_A
        dikmeler = [dikme_kutusu(0, TABAN_DERIN - PROFIL_A), dikme_kutusu(KUYU_EN - PROFIL_A, TABAN_DERIN - PROFIL_A)]
    else:
        u_min, u_max = PROFIL_A, TABAN_DERIN - PROFIL_A
        x0 = 0 if yuz == "SOL" else KUYU_EN - PROFIL_A
        dikmeler = [dikme_kutusu(x0, 0), dikme_kutusu(x0, TABAN_DERIN - PROFIL_A)]
    for k, (a, b) in enumerate(CAPRAZ_PANELLERI):
        za, zb = KUSAK[a] + KUSAK_H, KUSAK[b]
        (u0, u1) = (u_min, u_max) if k % 2 == 0 else (u_max, u_min)
        du, dz = u1 - u0, zb - za
        L = math.hypot(du, dz)
        phi = math.degrees(math.atan2(dz, du))
        if yuz == "ARKA":
            t = kutu_boru("X", L + 2 * UZATMA, CAPRAZ_A, CAPRAZ_A, CAPRAZ_T, CAPRAZ_RO, CAPRAZ_RI)
            t = t.translate(Vector(-UZATMA, 0, 0)).rotate(Vector(0, 0, 0), Vector(0, 1, 0), -phi)
            t = t.translate(Vector(u0, TABAN_DERIN - CAPRAZ_A / 2, za))
            d = (math.cos(math.radians(phi)), 0, math.sin(math.radians(phi)))
        else:
            xc = CAPRAZ_A / 2 if yuz == "SOL" else KUYU_EN - CAPRAZ_A / 2
            t = kutu_boru("Y", L + 2 * UZATMA, CAPRAZ_A, CAPRAZ_A, CAPRAZ_T, CAPRAZ_RO, CAPRAZ_RI)
            t = t.translate(Vector(0, -UZATMA, 0)).rotate(Vector(0, 0, 0), Vector(1, 0, 0), phi)
            t = t.translate(Vector(xc, u0, za))
            d = (0, math.cos(math.radians(phi)), math.sin(math.radians(phi)))
        if CAPRAZ_KG_M is None:
            CAPRAZ_KG_M = t.Volume() / (L + 2 * UZATMA) * 1000 * YOGUNLUK
        kesilmis = t.cut(*dikmeler, kusak_kutulari[(yuz, a)], kusak_kutulari[(yuz, b)])
        parca = max(kesilmis.Solids(), key=lambda s: s.Volume())
        izd = [v.X * d[0] + v.Y * d[1] + v.Z * d[2] for v in parca.Vertices()]
        kesim_boyu = max(izd) - min(izd)
        ad = f"CAPRAZ_{modul(a)}_{yuz}_{a}_{b}"
        ekle(ad, parca, "GERCEK", "capraz")
        capraz_bilgi.append(dict(ad=ad, yuz=yuz, a=a, b=b, u0=u0, u1=u1, za=za, zb=zb, boy=kesim_boyu,
                                 aci=abs(phi) if abs(phi) <= 90 else 180 - abs(phi), kg=parca.Volume() * YOGUNLUK))

# ---------------------------------------------------------------------
# 4c) KAT KAPILARI (her durakta aynı takım; kasa ve kanat imal edilir, kilit/eşik/menteşe satın alınır)
# ---------------------------------------------------------------------
def u_kanal(x0, x1, y0, y1, z0, z1, t, ic):
    """Bükme sac U: dış kutu eksi iç kutu. 'ic' iç kutunun (x0,x1,y0,y1,z0,z1) sınırları."""
    return kutu(x0, x1, y0, y1, z0, z1).cut(kutu(*ic))


kapi_bilgi = []
for i, s in enumerate(DURAKLAR, 1):
    on = f"KAT_KAPISI_{i}"
    z_bas = s + KAPI_NET_H                                   # başlığın altı
    # Kasa: iki dikme + başlık, 2 mm U, ağzı kuyuya (y+) açık
    jamb_sol = u_kanal(KASA_X[0], KAPI_X0, 0, KASA_D, s, z_bas, 2,
                       (KASA_X[0] + 2, KAPI_X0 - 2, 2, KASA_D + 1, s - 1, z_bas + 1))
    jamb_sag = u_kanal(KAPI_X1, KASA_X[1], 0, KASA_D, s, z_bas, 2,
                       (KAPI_X1 + 2, KASA_X[1] - 2, 2, KASA_D + 1, s - 1, z_bas + 1))
    baslik = u_kanal(KASA_X[0], KASA_X[1], 0, KASA_D, z_bas, z_bas + KASA_P, 2,
                     (KASA_X[0] - 1, KASA_X[1] + 1, 2, KASA_D + 1, z_bas + 2, z_bas + KASA_P - 2))
    ekle(f"{on}_KASA", jamb_sol.fuse(jamb_sag, baslik).clean(), "GERCEK", "kasa")
    # Eşik: alüminyum profil, kasanın altına kadar uzun, alt kuşağın iç yüzüne bağlı
    ekle(f"{on}_ESIK", kutu(KASA_X[0], KASA_X[1], KUSAK_D, ESIK_Y1, s - ESIK_H, s), "HAYALET", "esik", "KAT_KAPILARI")
    # Kanat: 1,5 mm sac tepsi, dar camlı; kasanın önünde, sol menteşeli, dışa açılır
    kz0, kz1 = s - 5, z_bas + 10
    kanat = kutu(KANAT_X[0], KANAT_X[1], -KANAT_T, 0, kz0, kz1).cut(
        kutu(KANAT_X[0] + 1.5, KANAT_X[1] - 1.5, -KANAT_T + 1.5, 1, kz0 + 1.5, kz1 - 1.5))
    pw, ph = PENCERE
    px = (KANAT_X[0] + KANAT_X[1]) / 2 - 20
    pz = s + 80
    kanat = kanat.cut(kutu(px - pw / 2, px + pw / 2, -KANAT_T - 1, -KANAT_T + 2, pz, pz + ph))
    ekle(f"{on}_KANAT", kanat, "GERCEK", "kanat")
    ekle(f"{on}_PENCERE", kutu(px - pw / 2 - 5, px + pw / 2 + 5, -KANAT_T + 2, -KANAT_T + 5, pz - 5, pz + ph + 5),
         "HAYALET", "cam", "KAT_KAPILARI")
    ekle(f"{on}_KOL", kutu(KANAT_X[1] - 30, KANAT_X[1] - 15, -KANAT_T - 30, -KANAT_T, s + 140, s + 165),
         "HAYALET", "civata", "KAT_KAPILARI")
    for mz in (s + 30, z_bas - 60):
        ekle(f"{on}_MENTESE_{mz:.0f}", silindir(KANAT_X[0] - 6, -KANAT_T / 2, mz, mz + 40, 12), "HAYALET", "civata", "KAT_KAPILARI")
    # Kilit (gerçek standart kilit, kontaklı) + makarası: kabinin sağ yanında, kasa kilit kenarının arkasında
    ekle(f"{on}_KILIT", kutu(KILIT_X[0], KILIT_X[1], KASA_D, KASA_D + KILIT_D, s + KILIT_Z_OFS, s + KILIT_Z_OFS + KILIT_H),
         "HAYALET", "kilit", "KAT_KAPILARI")
    ekle(f"{on}_KILIT_MAKARASI", kutu(KILIT_MAKARA_X0, KILIT_X[0], KABIN_ON_Y + 7, KABIN_ON_Y + 23,
                                      s + KILIT_MAKARA_Z - 10, s + KILIT_MAKARA_Z + 10), "HAYALET", "kilit", "KAT_KAPILARI")
    # Kat buton kutusu (kapının sağında, önde)
    ekle(f"{on}_BUTON_KUTUSU", kutu(KILIT_X[1] - 20, KILIT_X[1] + 20, -25, -5, s + 150, s + 210), "HAYALET", "kilit", "KAT_KAPILARI")
    # Kanadın açılma zarfı (menteşe ekseni etrafında çeyrek daire, y<0 tarafında)
    R = KANAT_X[1] - KANAT_X[0] + 6
    hx, hy = KANAT_X[0] - 6, -KANAT_T / 2
    zarf = silindir(hx, hy, kz0, kz1, 2 * R).intersect(kutu(hx, hx + R, hy - R, 0, kz0, kz1))
    ekle(f"{on}_ACILMA_ZARFI", zarf, "ZARF", "kanat", "KAT_KAPILARI")
    kapi_bilgi.append(dict(s=s, R=R))

# ---------------------------------------------------------------------
# 5) KUYU İÇİ HAYALETLER
# ---------------------------------------------------------------------
def ayna_x(sekil):
    """Kuyu eksenine (x = KABIN_MX) göre ayna — sol taraf parçaları için."""
    return sekil.mirror("YZ", (KABIN_MX, 0, 0))


def tarama(sekil, asagi, yukari):
    """Parçanın asagi..yukari hareketinde taradığı hacim.
    Dik prizma ise alt yüzü uzatılır (yarıklar korunur); değilse dış kutusu alınır (temkinli)."""
    bb = sekil.BoundingBox()
    yuzler = cq.Workplane().add(sekil).faces("<Z").vals()
    if len(yuzler) == 1 and abs(yuzler[0].Area() * bb.zlen - sekil.Volume()) < 1e-3 * sekil.Volume():
        return cq.Solid.extrudeLinear(yuzler[0].translate(Vector(0, 0, -asagi)), Vector(0, 0, bb.zlen + asagi + yukari))
    return kutu(bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin - asagi, bb.zmax + yukari)


# Kılavuzlar: U profil, sırtı dışta, ağzı kuyunun ortasına bakar (sağda çiz, sola aynala)
RAY_ALT = TABAN_UST + RAY_AYAK_H
Y_K0, Y_K1 = KILAVUZ_Y - KILAVUZ_H / 2, KILAVUZ_Y + KILAVUZ_H / 2


def kilavuz_sag(z0, z1):
    sirt = kutu(SAG_KILAVUZ_SIRT - KILAVUZ_T, SAG_KILAVUZ_SIRT, Y_K0, Y_K1, z0, z1)
    f1 = kutu(SAG_KILAVUZ_SIRT - KILAVUZ_B, SAG_KILAVUZ_SIRT - KILAVUZ_T, Y_K0, Y_K0 + KILAVUZ_T, z0, z1)
    f2 = kutu(SAG_KILAVUZ_SIRT - KILAVUZ_B, SAG_KILAVUZ_SIRT - KILAVUZ_T, Y_K1 - KILAVUZ_T, Y_K1, z0, z1)
    return sirt.fuse(f1, f2).clean()


for taraf, f in (("SAG", lambda s: s), ("SOL", ayna_x)):
    ekle(f"KILAVUZ_{taraf}_U50", f(kilavuz_sag(RAY_ALT, RAY_UST)), "HAYALET", "ray", "KILAVUZLAR")
    ekle(f"KILAVUZ_AYAGI_{taraf}",
         f(kutu(SAG_KILAVUZ_SIRT - KILAVUZ_B - 3, SAG_KILAVUZ_SIRT + 3, Y_K0 - 10, Y_K1 + 10, TABAN_UST, RAY_ALT)),
         "HAYALET", "ray", "KILAVUZLAR")
    # Kılavuz konsolları: arka kuşaklardan kılavuzun arka flanşına (oval delikli L konsol çifti)
    for r in KONSOL_KOTLARI:
        ekle(f"KILAVUZ_KONSOLU_{taraf}_{r}",
             f(kutu(SAG_KILAVUZ_SIRT - KILAVUZ_B, SAG_KILAVUZ_SIRT, Y_K1, ARKA_KUSAK_Y, KUSAK[r], KUSAK[r] + KUSAK_H)),
             "HAYALET", "klips", "KILAVUZ_KONSOLLARI")

# Kabin + sırt çantası askı (1. durakta)
z_aski_alt = Z0 - ASKI_ALT
z_tavan = Z0 + KABIN_H
z_aski_ust = z_tavan + ASKI_UST
hareketli = []   # (ad, sekil, renk) — 1. durak konumunda
hareketli.append(("KABIN", kutu(KABIN_X0, KABIN_X1, KABIN_ON_Y, KABIN_Y1, Z0, z_tavan), "kabin"))
for i, (a, b) in enumerate([(KABIN_X0 + TASIYICI_KOL_X[0], KABIN_X0 + TASIYICI_KOL_X[1]),
                            (KABIN_X1 - TASIYICI_KOL_X[1], KABIN_X1 - TASIYICI_KOL_X[0])], 1):
    hareketli.append((f"TASIYICI_KOL_{i}", kutu(a, b, KABIN_ON_Y, ASKI_ALT_Y[0], Z0 - 40, Z0), "aski"))
hareketli.append(("ASKI_ALT_KIRIS", kutu(ASKI_X_SOL[0], ASKI_X_SAG[1], *ASKI_ALT_Y, z_aski_alt, Z0 - 20), "aski"))
hareketli.append(("ASKI_UST_KIRIS", kutu(ASKI_X_SOL[0], ASKI_X_SAG[1], *ASKI_UST_Y, z_tavan + 20, z_aski_ust), "aski"))
y_d0, y_d1 = KANAL_Y[0] + 2, KANAL_Y[1] - 2          # askı dikmesi, kanal ağzının önünde
for taraf, f in (("SAG", lambda s: s), ("SOL", ayna_x)):
    x0, x1 = ASKI_X_SAG
    hareketli.append((f"ASKI_DIKME_{taraf}", f(kutu(x0, x1, y_d0, y_d1, z_aski_alt, z_aski_ust)), "aski"))
    hareketli.append((f"ASKI_ALT_BAGLANTI_{taraf}", f(kutu(x0, x1, ASKI_ALT_Y[1], y_d0, z_aski_alt, Z0 - 20)), "aski"))
    hareketli.append((f"ASKI_UST_BAGLANTI_{taraf}", f(kutu(x0, x1, ASKI_UST_Y[1], y_d0, z_tavan + 20, z_aski_ust)), "aski"))
    xm0, xm1 = SAG_KILAVUZ_SIRT - KILAVUZ_B + BOSLUK_MIN, SAG_KILAVUZ_SIRT - KILAVUZ_T - BOSLUK_MIN
    ym0, ym1 = KILAVUZ_Y - KIZAK_MAKARA_D / 2, KILAVUZ_Y + KIZAK_MAKARA_D / 2
    hareketli.append((f"KIZAK_MAKARASI_ALT_{taraf}", f(kutu(xm0, xm1, ym0, ym1, z_aski_alt, z_aski_alt + KIZAK_MAKARA_D)), "aski"))
    hareketli.append((f"KIZAK_MAKARASI_UST_{taraf}", f(kutu(xm0, xm1, ym0, ym1, z_aski_ust - KIZAK_MAKARA_D, z_aski_ust)), "aski"))
    hareketli.append((f"PARASUT_{taraf}", f(kutu(x0, x1, y_d0, y_d1, z_aski_alt - PARASUT_H, z_aski_alt)), "parasut"))

# Otomatik kabin kapısı (2 kanat teleskopik, sola açılır; kapalı hâl), kapı motoru, etek sacı, kilit kamı
yarim = KAPI_NET_W / 2
hareketli.append(("KABIN_KAPISI_HIZLI", kutu(KAPI_X0 + yarim - 5, KAPI_X1 + 5, KABIN_ON_Y + 3, KABIN_ON_Y + 3 + KABIN_KAPI_T,
                                              Z0, Z0 + KAPI_NET_H + 10), "kabin_kapi"))
hareketli.append(("KABIN_KAPISI_YAVAS", kutu(KAPI_X0 - 5, KAPI_X0 + yarim + 5, KABIN_ON_Y + 11, KABIN_ON_Y + 11 + KABIN_KAPI_T,
                                              Z0, Z0 + KAPI_NET_H + 10), "kabin_kapi"))
hareketli.append(("KABIN_KAPI_MOTORU", kutu(KAPI_X0 - yarim - 10, KAPI_X1 + 5, KABIN_ON_Y, KABIN_ON_Y + 55,
                                             z_tavan, z_tavan + KABIN_KAPI_OPERATOR_H), "kabin_kapi"))
hareketli.append(("KABIN_ETEK_SACI", kutu(KAPI_X0 - 5, KABIN_X1, KABIN_ON_Y, KABIN_ON_Y + 3, Z0 - ETEK_H, Z0), "kabin_kapi"))
hareketli.append(("KILIT_KAMI_GERI_CEKIK", kutu(KABIN_X1, KABIN_X1 + 3, KABIN_ON_Y + 5, KABIN_ON_Y + 25,
                                                Z0 + KILIT_MAKARA_Z - KAM_BOY / 2, Z0 + KILIT_MAKARA_Z + KAM_BOY / 2), "kilit"))
assert z_tavan + KABIN_KAPI_OPERATOR_H <= z_tavan + ASKI_UST, "Kabin kapı motoru yükseklik bütçesini aşıyor"
assert Z0 - ETEK_H - ALT_ASIM > TABAN_UST + 20, "Etek sacı alt fazla gidişte tabana yaklaşıyor"

for ad, s, r in hareketli:
    ekle(f"HAYALET_{ad}", s, "HAREKETLI", r, "KABIN_ASKI")
kabin_tarama = [tarama(s, ALT_ASIM, KABIN_MAKS_YUKSELME) for (_, s, _) in hareketli]

# Tamponlar (askı alt kirişinin altında, zincir kollarının dışında)
tampon_ust = z_aski_alt - ALT_ASIM
tampon_ayak_h = tampon_ust - TAMPON_H - TABAN_UST
TAMPON_Y = (ASKI_ALT_Y[0] + ASKI_ALT_Y[1]) / 2
TAMPON_X = (KABIN_MX - 75, KABIN_MX + 75)
for i, tx in enumerate(TAMPON_X, 1):
    ekle(f"TAMPON_AYAGI_{i}", kutu(tx - 20, tx + 20, TAMPON_Y - 20, TAMPON_Y + 20, TABAN_UST, TABAN_UST + tampon_ayak_h),
         "HAYALET", "tampon", "TAMPONLAR")
    ekle(f"TAMPON_{i}", silindir(tx, TAMPON_Y, TABAN_UST + tampon_ayak_h, tampon_ust, 36), "HAYALET", "tampon", "TAMPONLAR")

# Silindir (dalgıç, ortada, arka duvara yakın) — gerçek parçalar hidrolik_parcalar.py'den
MIL_UST_GERI = MAKARA_Z_MIN - BASLIK_ALT                  # mil en altta iken üst ucu = piston başlığının altı
sil_parcalar, SIL_O = hid.silindir(KABIN_MX, SILINDIR_Y, TABAN_UST, STROK, MIL_UST_GERI)
for ad, s, tur, r, g in sil_parcalar:
    if tur == "HAREKETLI":
        # mil ve halka: 1. durakta (en alttan ALT_ASIM/2 yukarıda)
        s = s.translate(Vector(0, 0, ALT_ASIM / 2))
        ad = "HAYALET_" + ad
    ekle(ad, s, tur, r, g)
# Mil kafadan dışarı çıktığı bölge boyunca taradığı hacim (kontrol için)
mil_tarama = silindir(KABIN_MX, SILINDIR_Y, SILINDIR_UST + 0.5, MAKARA_Z_MAX - BASLIK_ALT, PISTON_MIL_D)
ekle("SILINDIR_KELEPCESI", kutu(KABIN_MX - 10, KABIN_MX + 10, SILINDIR_Y + hid.GOMLEK_D / 2, ARKA_KUSAK_Y,
                                KUSAK["R2"], KUSAK["R2"] + 30), "HAYALET", "yer_tutucu", "PISTON")
assert KUSAK["R2"] + 30 < SIL_O["z_gomlek_ust"] - 50, "Silindir kelepçesi gömleğin üstünde kalıyor"

# Zincir sabit uçları: ortadan mafsallı EŞİTLEME TERAZİSİ + gergi saplamaları (iki zincir her zaman eşit çeker)
TERAZI_Z = (TABAN_UST + 28, TABAN_UST + 48)
GERGI_UST = TERAZI_Z[1] + 80
SABIT_TRAVERS_Z = TERAZI_Z[1]
ekle("ZINCIR_TERAZI_MAFSAL_AYAGI", kutu(KABIN_MX - 8, KABIN_MX + 8, ZINCIR_ARKA_Y - 12, ZINCIR_ARKA_Y + 12, TABAN_UST, TERAZI_Z[0]),
     "HAYALET", "piston", "ZINCIRLER")
ekle("ZINCIR_ESITLEME_TERAZISI", kutu(ZINCIR_X[0] - 25, ZINCIR_X[1] + 25, ZINCIR_ARKA_Y - 10, ZINCIR_ARKA_Y + 10, *TERAZI_Z),
     "HAYALET", "piston", "ZINCIRLER")
for i, zx in enumerate(ZINCIR_X, 1):
    ekle(f"ZINCIR_GERGI_SAPLAMASI_{i}", silindir(zx, ZINCIR_ARKA_Y, TERAZI_Z[1], GERGI_UST, 12), "HAYALET", "civata", "ZINCIRLER")


def makara_grubu(zm):
    """Makara ekseni zm'de iken piston başlığı + mil + iki zincir makarası."""
    baslik = kutu(KABIN_MX - 20, KABIN_MX + 20, SILINDIR_Y - 20, SILINDIR_Y + 20, zm - BASLIK_ALT, zm + 20)
    mil = silindir(SILINDIR_Y, zm, ZINCIR_X[0] - MAKARA_GEN / 2 - 4, ZINCIR_X[1] + MAKARA_GEN / 2 + 4, 16, eksen="X")
    m1 = silindir(SILINDIR_Y, zm, ZINCIR_X[0] - MAKARA_GEN / 2, ZINCIR_X[0] + MAKARA_GEN / 2, 2 * MAKARA_R, eksen="X")
    m2 = silindir(SILINDIR_Y, zm, ZINCIR_X[1] - MAKARA_GEN / 2, ZINCIR_X[1] + MAKARA_GEN / 2, 2 * MAKARA_R, eksen="X")
    return baslik, mil, m1, m2


baslik0, mil0, m1_0, m2_0 = makara_grubu(MAKARA_Z0)
ekle("HAYALET_PISTON_BASLIGI", baslik0, "HAREKETLI", "piston", "MAKARA")
ekle("HAYALET_MAKARA_MILI", mil0, "HAREKETLI", "piston", "MAKARA")
ekle("HAYALET_ZINCIR_MAKARASI_1", m1_0, "HAREKETLI", "makara", "MAKARA")
ekle("HAYALET_ZINCIR_MAKARASI_2", m2_0, "HAREKETLI", "makara", "MAKARA")
makara_tarama = [tarama(s, ALT_ASIM / 2, KABIN_MAKS_YUKSELME / 2) for s in (baslik0, mil0, m1_0, m2_0)]

# Zincirler (görsel; kontrolde tüm yolu kapsayan çizgi olarak)
halat_tarama = []
for i, zx in enumerate(ZINCIR_X, 1):
    ekle(f"ZINCIR_KABIN_KOLU_{i}", silindir(zx, ZINCIR_ON_Y, KANCA_Z0, MAKARA_Z0, ZINCIR_KAL), "HALAT", "halat", "ZINCIRLER")
    ekle(f"ZINCIR_SABIT_KOL_{i}", silindir(zx, ZINCIR_ARKA_Y, GERGI_UST, MAKARA_Z0, ZINCIR_KAL), "HALAT", "halat", "ZINCIRLER")
    halat_tarama.append(silindir(zx, ZINCIR_ON_Y, KANCA_Z0 - ALT_ASIM, MAKARA_Z_MAX, ZINCIR_KAL))
    halat_tarama.append(silindir(zx, ZINCIR_ARKA_Y, GERGI_UST, MAKARA_Z_MAX, ZINCIR_KAL))

# Son durak şalterleri: dik dişli çubuk (üründeki gibi, ayarlı)
SALTER_CUBUK = (KABIN_MX - 80, ARKA_KUSAK_Y - 30)
ekle("SINIR_SALTER_CUBUGU", silindir(*SALTER_CUBUK, TABAN_UST + 20, RAY_UST, 12), "HAYALET", "yer_tutucu", "SALTERLER")


# Güç ünitesi (tava ayaklı ve tabana cıvatalı) — gerçek parçalar hidrolik_parcalar.py'den
uni_parcalar, UNI_O = hid.unite(UNITE_XC, UNITE_YC, TABAN_UST)
for ad, s, tur, r, g in uni_parcalar:
    ekle(ad, s, tur, r, g)
TAVA_Z = UNI_O["z_tava"]

# Kumanda panosu (invertör içinde): ünitenin üstünde, iskeletin sağ yüzüne asılı; kapağı öne bakar
PANO_X0, PANO_Y0, PANO_Z0 = KUYU_EN + 7, 45, 790
pano_parcalar, PANO_O = hid.kumanda_panosu(PANO_X0, PANO_Y0, PANO_Z0)
for ad, s, tur, r, g in pano_parcalar:
    ekle(ad, s, tur, r, g)
PANO_MERKEZ = (PANO_X0 + hid.PANO_X / 2, PANO_Y0 + hid.PANO_Y / 2, PANO_Z0 + hid.PANO_Z / 2)
assert PANO_Z0 > UNI_O["tepe"] + 50, "Pano motorun tepesine çok yakın"

# Basınç hortumu (1/4" 2SN): valf bloğu rakorundan → ünitenin solundan aşağı → sağ yüzden R1 altından kuyuya
# → tabanda kabinin altından (hareketli parçaların altında) → silindirin hortum patlama valfi rakoruna
bx, by, bz = UNI_O["blok_cikis"]
gx, gy, gz = SIL_O["giris"]
hx = KUYU_EN + 10                                   # iskelet (x<=650) ile tava arasından iner
hortum_noktalari = [(bx, by, bz), (bx - 21, by + 1, bz - 5), (hx + 4, by + 5, bz - 35), (hx, by + 12, 300),
                    (hx, by + 20, 230), (KUYU_EN - 10, by + 25, 192), (560, 236, 184), (430, 240, 182),
                    (350, 290, 178), (gx + 3, 350, gz + 2), (gx, gy, gz)]
hortum, HORTUM_BOY = hid.hortum_kiv(hortum_noktalari, (-1, 0, 0), (0, 1, 0))
ekle("BASINC_HORTUMU_1_4", hortum, "HALAT", "hortum", "HORTUM")      # görünüş + STEP
# Kontrol için hortumun vekili: eğri boyunca 40 kısa düz silindir (eğri yüzeyle çakışma hesabı çok yavaş)
_e = cq.Edge.makeSpline([Vector(*q) for q in hortum_noktalari],
                        tangents=[Vector(-1, 0, 0), Vector(0, 1, 0)],
                        parameters=[0.0] + list(np.cumsum([(Vector(*b) - Vector(*a)).Length
                                                            for a, b in zip(hortum_noktalari, hortum_noktalari[1:])])),
                        scale=False)
_orn = [_e.positionAt(i / 40) for i in range(41)]
hortum_vekil = [{"ad": f"HORTUM_VEKIL_{i}", "sekil": cq.Solid.makeCylinder(hid.HORTUM_D / 2, (b - a).Length, a, (b - a).normalized()),
                 "tur": "HAYALET"} for i, (a, b) in enumerate(zip(_orn, _orn[1:]))]
for i, (kx_, ky_) in enumerate(((560, 236), (430, 240)), 1):   # hortum kelepçesi ayakları (tabana)
    ekle(f"HORTUM_KELEPCESI_{i}", kutu(kx_ - 8, kx_ + 8, ky_ - 10, ky_ + 10, TABAN_UST, TABAN_UST + 25),
         "HALAT", "civata", "HORTUM")

# Kablolar (görsel): panodan motor klemens kutusuna ve iniş valfi fişine
g1, g2 = PANO_O["glandlar"][0], PANO_O["glandlar"][1]
kl = UNI_O["klemens_giris"]
kablo_motor, _ = hid.hortum_kiv([g1, (g1[0] - 5, g1[1] + 10, g1[2] - 40), (672, 200, 720), (672, 420, 680),
                                 (kl[0] - 40, kl[1] + 25, kl[2] + 60), (kl[0], kl[1] + 20, kl[2] + 5), kl],
                                (0, 0, -1), (0, -1, 0), hid.KABLO_D)
ekle("KABLO_MOTOR", kablo_motor, "HALAT", "kablo", "KABLOLAR")
df = UNI_O["din_fis"]
kablo_valf, _ = hid.hortum_kiv([g2, (g2[0] + 3, g2[1] + 5, g2[2] - 120), (df[0], df[1] - 25, df[2] + 40),
                                (df[0], df[1] - 12, df[2]), (df[0], df[1], df[2] - 6)],
                               (0, 0, -1), (0, 1, 0), hid.KABLO_D)
ekle("KABLO_INIS_VALFI", kablo_valf, "HALAT", "kablo", "KABLOLAR")

# =====================================================================
# DOĞRULAMA
# =====================================================================
rapor = []


def yaz(s=""):
    print(s)
    rapor.append(s)


def kesisim(a, b):
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if (ba.xmin >= bb.xmax - 1e-6 or bb.xmin >= ba.xmax - 1e-6 or ba.ymin >= bb.ymax - 1e-6 or
            bb.ymin >= ba.ymax - 1e-6 or ba.zmin >= bb.zmax - 1e-6 or bb.zmin >= ba.zmax - 1e-6):
        return 0.0
    return a.intersect(b).Volume()


yaz("=" * 70)
yaz("MAKET TABAN + DİKME — TASLAK YERLEŞİM MODELİ KONTROL RAPORU")
yaz("=" * 70)

# --- Yükseklik bütçesi ---
yaz("\n[1] YÜKSEKLİK BÜTÇESİ (zeminden, mm)")
yaz(f"  Taban sacı üstü ............... {TABAN_UST}")
yaz(f"  Çukur (hesaplanan) ............ {CUKUR}  (paraşüt yığını {yigin_parasut}, tampon yığını {yigin_tampon})")
for i, z in enumerate(DURAKLAR, 1):
    yaz(f"  {i}. durak kabin tabanı ........ {z}")
yaz(f"  Bölme (ek flanşı) ............. {BOLME_Z}")
yaz(f"  Askı üstü, en üst fazla gidişte  {ASKI_UST_ENUST}")
yaz(f"  Ray tepesi .................... {RAY_UST}")
yaz(f"  Dikme tepesi (toplam yükseklik)  {Z_TEPE}")
yaz(f"  Piston stroku ................. {STROK:.0f}  (yol {YOL} + alt {ALT_ASIM} + üst {UST_ASIM}) / 2")
yaz(f"  Silindir kapalı boyu (ayak dahil) {SILINDIR_UST - TABAN_UST:.0f}, kafa kotu {SILINDIR_UST:.0f}")
yaz(f"  Makara ekseni: en alt {MAKARA_Z_MIN:.0f}, 1. durakta {MAKARA_Z0:.0f}, en üst {MAKARA_Z_MAX:.0f}")
alt_modul = BOLME_Z
yaz(f"  Alt modül yüksekliği (teker dahil) {alt_modul}  → kapı {KAPI_H} - pay {KAPI_PAY} = {KAPI_H - KAPI_PAY}: "
    f"{'GEÇER' if alt_modul <= KAPI_H - KAPI_PAY else 'GEÇMEZ!'}")
yaz(f"  Bölme kotu ile en yakın kat kapısı: 2. durak kapı üstü ≈{DURAKLAR[1] + KABIN_H}, 3. durak eşiği {DURAKLAR[2]}")
assert alt_modul <= KAPI_H - KAPI_PAY
assert DURAKLAR[1] + KABIN_H + 100 < BOLME_Z < DURAKLAR[2] - 100
assert SILINDIR_UST < BOLME_Z

# Askı alt kirişi (zincir bağlantısı) ile zincir makarası, en üst fazla gidişte
kol_ust_enust = KANCA_Z0 + KABIN_MAKS_YUKSELME
makara_alt_enust = MAKARA_Z_MAX - MAKARA_R
yaz(f"  En üstte: askı alt kirişi üstü {kol_ust_enust:.0f}, zincir makarası altı {makara_alt_enust:.0f} "
    f"→ boşluk {makara_alt_enust - kol_ust_enust:.0f} mm")
assert makara_alt_enust - kol_ust_enust >= MAKARA_MARJ - 1e-6

yaz("\n[1b] DERİNLİK (Y) YERLEŞİMİ — önden arkaya, mm")
for ad, a, b in [("kat kapısı kanadı (dışarıda)", -KANAT_T, 0),
                 ("kat kapısı kasası", 0, KASA_D),
                 ("kat eşiği", KUSAK_D, ESIK_Y1),
                 ("kabin", KABIN_ON_Y, KABIN_Y1),
                 ("askı üst kirişi", *ASKI_UST_Y),
                 ("askı alt kirişi (zincir bağlantısı)", *ASKI_ALT_Y),
                 ("ön zincir kolu", ZINCIR_ON_Y, ZINCIR_ON_Y),
                 ("zincir makarası (dış)", SILINDIR_Y - MAKARA_R, SILINDIR_Y + MAKARA_R),
                 ("silindir gövdesi", SILINDIR_Y - PISTON_GOVDE_D / 2, SILINDIR_Y + PISTON_GOVDE_D / 2),
                 ("U kılavuzlar", Y_K0, Y_K1),
                 ("arka zincir kolu", ZINCIR_ARKA_Y, ZINCIR_ARKA_Y),
                 ("arka kuşak", ARKA_KUSAK_Y, TABAN_DERIN)]:
    yaz(f"  {ad:40s} {a:6.0f}" + ("" if a == b else f" .. {b:.0f}"))
yaz(f"  Eşik boşluğu (kabin önü - kat eşiği): {KABIN_ON_Y - ESIK_Y1} mm;  "
    f"askı kancası kabin ağırlık merkezinin {ZINCIR_ON_Y - (KABIN_ON_Y + KABIN_DERIN / 2):.0f} mm arkasında (sırt çantası)")

# --- Dış ölçü ---
gercek = [p for p in parcalar if p["tur"] == "GERCEK"]
bb = cq.Compound.makeCompound([p["sekil"] for p in gercek]).BoundingBox()
yaz("\n[2] DIŞ ÖLÇÜ (üretilecek parçalar)")
yaz(f"  X {bb.xmin:.0f}..{bb.xmax:.0f} = {bb.xlen:.0f}   Y {bb.ymin:.0f}..{bb.ymax:.0f} = {bb.ylen:.0f}   Z {bb.zmin:.0f}..{bb.zmax:.0f}")
yaz(f"  Taşıma (kulaklar sökülü): {TABAN_EN} x {TABAN_DERIN}   Fuar (kulaklar takılı): {TABAN_EN} x {TABAN_DERIN + 2 * KULAK_TASMA}")
assert abs(bb.xlen - TABAN_EN) < 0.5 and abs(bb.ylen - (TABAN_DERIN + 2 * KULAK_TASMA)) < 0.5
assert abs(bb.zmax - Z_TEPE) < 0.5

# --- Profil kg/m ---
alan = PROFIL_A ** 2 - (PROFIL_A - 2 * PROFIL_T) ** 2 - (4 - math.pi) * (PROFIL_RO ** 2 - PROFIL_RI ** 2)
kg_m = alan * 1000 * YOGUNLUK
dikme_ornek = [p for p in parcalar if p["ad"] == "DIKME_ALT_SOL_ON"][0]["sekil"]
kg_m_model = dikme_ornek.Volume() / DIKME_ALT_BOY * 1000 * YOGUNLUK
yaz("\n[3] PROFİL KONTROLÜ  kutu 40x40x3")
yaz(f"  Formül {kg_m:.2f} kg/m, model {kg_m_model:.2f} kg/m, katalog {TABLO_KG_M:.2f} kg/m "
    f"→ fark %{abs(kg_m_model - TABLO_KG_M) / TABLO_KG_M * 100:.1f}")
assert abs(kg_m_model - TABLO_KG_M) / TABLO_KG_M < 0.03
yaz(f"  Kuşak 40x20x2: model {KUSAK_KG_M:.2f} kg/m, katalog {TABLO_KUSAK_KG_M:.2f}  |  "
    f"Çapraz 20x20x2: model {CAPRAZ_KG_M:.2f} kg/m, katalog {TABLO_CAPRAZ_KG_M:.2f}")
assert abs(KUSAK_KG_M - TABLO_KUSAK_KG_M) / TABLO_KUSAK_KG_M < 0.05
assert abs(CAPRAZ_KG_M - TABLO_CAPRAZ_KG_M) / TABLO_CAPRAZ_KG_M < 0.06

# --- Çakışma ---
yaz("\n[4] ÇAKIŞMA KONTROLÜ")
sabit = [p for p in parcalar if p["tur"] in ("GERCEK", "BAGLANTI", "HAYALET")] + hortum_vekil
zarflar = ([("KABIN_ASKI_YOL_ZARFI", s) for s in kabin_tarama] +
           [("MAKARA_YOL_ZARFI", s) for s in makara_tarama] +
           [(p["ad"], p["sekil"]) for p in parcalar if p["tur"] == "ZARF"] +
           [("ZINCIR_YOL_ZARFI", s) for s in halat_tarama] +
           [("PISTON_MILI_YOL_ZARFI", mil_tarama)])
hatalar = []
cift_sayisi = 0
for i in range(len(sabit)):
    for j in range(i + 1, len(sabit)):
        ai, aj = sabit[i]["ad"], sabit[j]["ad"]
        if ai.startswith("HORTUM_VEKIL") and aj.startswith(("HORTUM_VEKIL", "HORTUM_RAKORU")):
            continue                                    # vekil parçalar uç uca eklenir, uçları rakora girer
        if aj.startswith("HORTUM_VEKIL") and ai.startswith("HORTUM_RAKORU"):
            continue
        cift_sayisi += 1
        v = kesisim(sabit[i]["sekil"], sabit[j]["sekil"])
        if v > 1e-3:
            hatalar.append((sabit[i]["ad"], sabit[j]["ad"], v))
for (zad, zs) in zarflar:
    for p in sabit:
        # teker dönme zarfı kendi tablasıyla; kapı açılma zarfı kendi kanadıyla temas eder — atla
        if zad.startswith("TEKER_") and p["ad"].startswith(zad.split("_DONME")[0]):
            continue
        if (zad.startswith("KAT_KAPISI_") and p["ad"].startswith(zad.rsplit("_ACILMA", 1)[0])
                and not p["ad"].endswith(("_KASA", "_ESIK", "_KILIT", "_KILIT_MAKARASI", "_BUTON_KUTUSU"))):
            continue
        cift_sayisi += 1
        v = kesisim(zs, p["sekil"])
        if v > 1e-3:
            hatalar.append((zad, p["ad"], v))
yaz(f"  {len(sabit)} sabit katı + {len(zarflar)} hareket zarfı, {cift_sayisi} çift kontrol edildi.")
if hatalar:
    for a, b, v in hatalar:
        yaz(f"  ÇAKIŞMA: {a}  x  {b}  = {v:.1f} mm3")
else:
    yaz("  Çakışma yok (tüm hacimler 0).")

# --- Hareketli parçalar için en az boşluk ---
yaz(f"\n[4b] HAREKETLİ PARÇA BOŞLUK KONTROLÜ (en az {BOSLUK_MIN} mm; tasarım gereği temas edenler hariç)")
tasarim_temas = [("KABIN_ASKI_YOL_ZARFI", "TAMPON_"), ("ZINCIR_YOL_ZARFI", "ZINCIR_GERGI"),
                 ("ZINCIR_YOL_ZARFI", "ZINCIR_SABIT_UC"), ("PISTON_MILI_YOL_ZARFI", "SILINDIR_KAFA_KAPAGI")]
dar = []
en_dar = {}
for (zad, zs) in zarflar:
    if zad.startswith("KAT_KAPISI_"):
        continue                  # kanat kasaya kapanır; açılma zarfı sadece çakışma için kontrol edildi
    zb = zs.BoundingBox()
    for p in sabit:
        if zad.startswith("TEKER_") and p["ad"].startswith(zad.split("_DONME")[0]):
            continue
        if any(zad == a and p["ad"].startswith(b) for a, b in tasarim_temas):
            continue
        pb = p["sekil"].BoundingBox()
        ayrik = max(pb.xmin - zb.xmax, zb.xmin - pb.xmax, pb.ymin - zb.ymax,
                    zb.ymin - pb.ymax, pb.zmin - zb.zmax, zb.zmin - pb.zmax)
        if ayrik >= BOSLUK_MIN + 20:
            continue
        mesafe = zs.distance(p["sekil"])
        onceki = en_dar.get(zad)
        if onceki is None or mesafe < onceki[1]:
            en_dar[zad] = (p["ad"], mesafe)
        if mesafe < BOSLUK_MIN - 1e-6:
            dar.append((zad, p["ad"], mesafe))
for zad, (pad, m) in sorted(en_dar.items()):
    yaz(f"  {zad:24s} en yakın: {pad:38s} {m:6.1f} mm")
if dar:
    for a, b, m in dar:
        yaz(f"  DAR: {a}  x  {b}  = {m:.1f} mm")
else:
    yaz(f"  Tüm hareketli parçalar sabit parçalardan en az {BOSLUK_MIN} mm uzakta.")
hatalar += [(a, b, -m) for a, b, m in dar]

# --- Ağırlık ve devrilme ---
yaz("\n[5] AĞIRLIK VE DEVRİLME (hayaletlerin kütlesi TAHMİN)")
kutleler = []   # (ad, kg, (x,y,z))
for p in parcalar:
    if p["tur"] in ("GERCEK", "BAGLANTI") or p["ad"] in ("HAYALET_PISTON_MILI", "HAYALET_STROK_SONU_HALKASI"):
        c = p["sekil"].Center()
        kutleler.append((p["ad"], p["sekil"].Volume() * YOGUNLUK, (c.x, c.y, c.z)))
ray_kg = sum(p["sekil"].Volume() for p in parcalar if p["ad"].startswith("KILAVUZ_") and "U50" in p["ad"]) * YOGUNLUK
kutleler.append(("kılavuzlar U50", ray_kg, (KABIN_MX, KILAVUZ_Y, (RAY_ALT + RAY_UST) / 2)))
# kabin + askı ağırlık merkezi: kabin ortası ile askı arasında, biraz arkada
en_ust_kabin = (KABIN_MX, (KABIN_ON_Y + ASKI_ALT_Y[1]) / 2 + 20, DURAKLAR[-1] + KABIN_H / 2)
kuyu_merkez = (KUYU_EN / 2, TABAN_DERIN / 2)
tahmini_konum = {
    "kabin + askı + paraşüt": en_ust_kabin,
    "piston başı + zincirler + terazi": (KABIN_MX, SILINDIR_Y, MAKARA_Z_MAX),
    "motor (IEC 71) + pompa + çan + valf bloğu": (UNITE_XC, UNITE_YC + 30, UNI_O["zk1"] + 130),
    "hidrolik yağ (~5 L)": (UNITE_XC, UNITE_YC, (UNI_O["zt0"] + UNI_O["zt1"]) / 2 - 20),
    "şeffaf paneller (ileride)": (*kuyu_merkez, 1300),
    "kat kapıları (ileride)": (KABIN_MX, 20, 1300),
    "kumanda panosu + invertör + fren direnci": PANO_MERKEZ,
    "teker x4": (TABAN_EN / 2, TABAN_DERIN / 2, TEKER_H / 2),
    "ayar ayağı x4": (TABAN_EN / 2, TABAN_DERIN / 2, 40),
}
for ad, kg in KUTLE.items():
    kutleler.append((ad, kg, tahmini_konum[ad]))
M = sum(k for _, k, _ in kutleler)
gx = sum(k * c[0] for _, k, c in kutleler) / M
gy = sum(k * c[1] for _, k, c in kutleler) / M
gz = sum(k * c[2] for _, k, c in kutleler) / M
gercek_kg = sum(k for a, k, _ in kutleler if not any(a == t for t in KUTLE) and a != "kılavuzlar U50")
yaz(f"  Üretilen çelik + bağlantı: {gercek_kg:.1f} kg,  raylar: {ray_kg:.1f} kg,  toplam (tahminlerle): {M:.0f} kg")
yaz(f"  Ağırlık merkezi (kabin en üstte): x={gx:.0f}, y={gy:.0f}, z={gz:.0f}")
W = M * 9.81


def devirme_kuvveti(kol_mm, h_mm):
    return W * kol_mm / h_mm / 9.81   # kgf


ayak_on = KULAK_AYAK[1]                       # -170
ayak_arka = TABAN_DERIN - KULAK_AYAK[1]       # 770
teker_on = TEKER_MERKEZ[0][1] + TEKER_OFSET   # en kötü: teker içe dönmüş
teker_arka = TEKER_MERKEZ[1][1] - TEKER_OFSET
devir = {
    "Tekerler üstünde (kulak yok)": (gy - teker_on, teker_arka - gy),
    "Fuar: kulaklar + ayaklar": (gy - ayak_on, ayak_arka - gy),
}
yaz(f"  Öne/arkaya devirmek için gereken yatay itme (kgf):")
yaz(f"    {'Durum':32s} {'öne, tepeden':>14s} {'öne, 1,5 m':>12s} {'arkaya, tepeden':>16s}")
for ad, (kol_on, kol_arka) in devir.items():
    yaz(f"    {ad:32s} {devirme_kuvveti(kol_on, Z_TEPE):14.0f} {devirme_kuvveti(kol_on, 1500):12.0f} "
        f"{devirme_kuvveti(kol_arka, Z_TEPE):16.0f}")
yan_kol = min(gx - KULAK_AYAK[0], (TABAN_EN - KULAK_AYAK[0]) - gx)
yaz(f"    Yana (fuar, tepeden): {devirme_kuvveti(yan_kol, Z_TEPE):.0f} kgf")

# --- Taban delik özeti ---
yaz("\n[6] TABAN DELİKLERİ (TASLAK)")
from collections import Counter
sayac = Counter((d, g.split(" (")[0]) for (_, _, d, g) in delikler)
for (d, g), n in sayac.items():
    yaz(f"  {n:3d} x Ø{d}  {g}")
yaz(f"  Toplam {len(delikler)} delik. Delikler arası en az 8 mm et, kenara en az 8 mm: kontrol edildi.")

yaz("\n[7] BU TURDA TABANDA OLMAYAN DELİKLER (parça ölçüleri gelince eklenecek)")
for s in ("U kılavuz ayakları (2)", "zincir eşitleme terazisi ayağı", "tamponlar (2)",
          "son durak şalteri çubuğu",
          "panel alt profili", "kat kapısı eşikleri",
          "kablo/hortum geçişi: sağ yüzde R1 kuşağının altı (z 150..330) bu iş için boş bırakıldı"):
    yaz(f"  - {s}")

yaz("\n[8] İSKELET — her modül kendi içinde kaynaklı kafes")
for yuz, rr in YUZ_KUSAKLARI.items():
    yaz(f"  {yuz:4s} kuşakları (alt yüz z): " + ", ".join(f"{r}={KUSAK[r]:.0f}" for r in rr))
yaz("  Çaprazlar (yan + arka, zikzak): " + ", ".join(f"{a}-{b}" for a, b in CAPRAZ_PANELLERI)
    + "; ön yüzde çapraz yok (kat kapıları)")
for c in capraz_bilgi:
    if c["yuz"] == "SOL":
        yaz(f"    {c['a']}-{c['b']}: yan çapraz kesim boyu {c['boy']:.0f} mm, açı {c['aci']:.0f}°")
for c in capraz_bilgi:
    if c["yuz"] == "ARKA":
        yaz(f"    {c['a']}-{c['b']}: arka çapraz kesim boyu {c['boy']:.0f} mm, açı {c['aci']:.0f}°")
yaz("\n[8b] KAT KAPILARI (yarı otomatik, menteşeli, dışa açılır) + OTOMATİK KABİN KAPISI")
yaz(f"  Net geçiş {KAPI_NET_W} x {KAPI_NET_H} mm, açıklık x {KAPI_X0:.0f}..{KAPI_X1:.0f} (kabin kapısıyla aynı)")
yaz(f"  Eşik boşluğu (kat eşiği - kabin önü): {KABIN_ON_Y - ESIK_Y1} mm (sınır 35)")
yaz(f"  Kilit: x {KILIT_X[0]:.0f}..{KILIT_X[1]:.0f} (kabinin sağ yanında), kam-makara boşluğu {KAM_BOSLUK} mm (kam geri çekikken)")
yaz(f"  Kanat açılma yarıçapı {kapi_bilgi[0]['R']:.0f} mm; öne taşma (kanat + kol) {KANAT_T + 30} mm → "
    f"taşıma derinliği {TABAN_DERIN + KANAT_T + 30} mm (80'lik kapıdan geçer)")
yaz(f"  Kabin etek sacı {ETEK_H} mm; en alt fazla gidişte altı z={Z0 - ETEK_H - ALT_ASIM:.0f} (taban üstü {TABAN_UST})")
H = hid.hesap(STROK)
pcr, burk_emn = hid.burkulma(STROK + SIL_O["mil_disari_geri"], H["kuvvet_dolu"])
yaz("\n[8c] HİDROLİK — dalgıç silindir + güç ünitesi (çıkış ve iniş invertörle)")
yaz(f"  Piston kuvveti: yüksüz {H['kuvvet_bos']:.0f} kgf, gösteri yüküyle {H['kuvvet_dolu']:.0f} kgf "
    f"→ basınç {H['p_bos']:.0f} / {H['p_dolu']:.0f} bar (Ø{hid.MIL_D:.0f} mil)")
yaz(f"  Debi {H['q']:.2f} L/dk (kabin {hid.KABIN_HIZ / 10:.0f} cm/s) → pompa ~{H['pompa_cc']:.2f} cc/dev; motor gücü ~{H['guc_w']:.0f} W "
    f"→ 0,25 kW; emniyet valfi ~{H['emniyet_bar']:.0f} bar")
yaz(f"  Silindir kapalı boyu {SIL_O['kapali_boy']:.0f} mm (ayak dahil), gömlek {SIL_O['gomlek_boy']:.0f}, mil {SIL_O['mil_boy']:.0f}; "
    f"mil en altta kafadan {SIL_O['mil_disari_geri']:.0f} mm dışarıda")
yaz(f"  Burkulma (kafa kılavuzsuz, K=2): kritik yük {pcr:.0f} kgf, emniyet {burk_emn:.1f}")
yaz(f"  Piston hacmi {H['mil_hacim_l']:.2f} L; tank iç hacmi {UNI_O['tank_ic_l']:.1f} L; ünite tepesi z={UNI_O['tepe']:.0f}")
assert burk_emn >= 2.5, "Mil burkulma emniyeti düşük"
ALT_ONEK = ("DIKME_ALT", "KUSAK_ALT", "CAPRAZ_ALT", "KOSE_PLAKASI_AYAK", "KOSE_PLAKASI_EK_ALT")
UST_ONEK = ("DIKME_UST", "KUSAK_UST", "CAPRAZ_UST", "KOSE_PLAKASI_EK_UST")
for ad, onek in (("Alt kafes", ALT_ONEK), ("Üst kafes", UST_ONEK)):
    ps = [p for p in parcalar if p["tur"] == "GERCEK" and p["ad"].startswith(onek)]
    kb = cq.Compound.makeCompound([p["sekil"] for p in ps]).BoundingBox()
    yaz(f"  {ad}: {len(ps)} parça, {sum(p['sekil'].Volume() for p in ps) * YOGUNLUK:.1f} kg, "
        f"dış ölçü {kb.xlen:.0f} x {kb.ylen:.0f} x {kb.zlen:.0f} mm")

with open(os.path.join(CIKTI, "kontrol_raporu.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rapor))

if hatalar:
    raise SystemExit("ÇAKIŞMA VAR — çıktılar üretilmedi.")

# =====================================================================
# ÇIKTILAR
# =====================================================================
# --- STEP montaj ---
assy = cq.Assembly(name="MAKET_TABAN_DIKME")
gruplar = {}
for p in parcalar:
    if p["tur"] == "ZARF":
        continue                      # hareket zarfları sadece kontrol içindir
    if p["tur"] == "GERCEK":
        assy.add(p["sekil"], name=p["ad"], color=cq.Color(*p["renk"]))
        continue
    g = p["grup"]
    if p["tur"] == "BAGLANTI":
        on_ek = ""
    elif g in ("TEKERLER", "AYAR_AYAKLARI"):
        on_ek = "SATIN_ALMA_"
    elif g == "YER_TUTUCU":
        on_ek = ""
    else:
        on_ek = "HAYALET_"
    gruplar.setdefault((on_ek + g, p["renk_ad"]), []).append(p["sekil"])
renk_sayisi = {}
for (gad, _) in gruplar:
    renk_sayisi[gad] = renk_sayisi.get(gad, 0) + 1
for (gad, rad), sekiller in gruplar.items():
    ad = gad if renk_sayisi[gad] == 1 else f"{gad}_{rad.upper()}"
    assy.add(cq.Compound.makeCompound(sekiller), name=ad, color=cq.Color(*RENK[rad]))
step_yol = os.path.join(CIKTI, "maket_taban_dikme.step")
assy.export(step_yol)

# --- Kesim listesi (Türk Excel: ; ayraç, virgül ondalık) ---
def tr(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


taban_kg = [p for p in parcalar if p["ad"] == "TABAN_SACI"][0]["sekil"].Volume() * YOGUNLUK
dikme_alt_kg = DIKME_ALT_BOY / 1000 * kg_m_model
dikme_ust_kg = DIKME_UST_BOY / 1000 * kg_m_model
satirlar = [
    (f"TABAN_SACI – lazer sac S235 {TABAN_EN}x{TABAN_DERIN}x{TABAN_T}, {len(delikler)} delik (TASLAK)", "", 1, taban_kg),
    ("DIKME_ALT – kutu 40x40x3 (ayak + ek flanşı kaynaklı)", DIKME_ALT_BOY, 4, 4 * dikme_alt_kg),
    ("DIKME_UST – kutu 40x40x3 (ek flanşı kaynaklı)", DIKME_UST_BOY, 4, 4 * dikme_ust_kg),
    (f"KOSE_PLAKASI – lazer sac {KOSE_PL}x{KOSE_PL}x{KOSE_PL_T}, 3xØ11 + 2xØ10", "", 12, 12 * KOSE_PL_KG),
    (f"DESTEK_KULAGI – lazer sac {KULAK_GEN}x{KULAK_TASMA + KULAK_ICERI}x{KULAK_T}", "", 4, 4 * KULAK_KG),
]
# Kuşaklar: modül ve boya göre grupla
kusak_grup = {}
for yuz, rr in YUZ_KUSAKLARI.items():
    boy = KAFES_BOY_X if yuz in ("ON", "ARKA") else KAFES_BOY_Y
    for r in rr:
        anahtar = (modul(r), "ön/arka" if yuz in ("ON", "ARKA") else "yan", boy)
        kusak_grup[anahtar] = kusak_grup.get(anahtar, 0) + 1
for (m, tip, boy), adet in sorted(kusak_grup.items()):
    satirlar.append((f"KUSAK_{m} – kutu 40x20x2 ({tip}, düz kesim, kaynaklı)", boy, adet, adet * boy / 1000 * KUSAK_KG_M))
# Çaprazlar: modül ve kesim boyuna göre grupla (uçlar açılı kesim, düğüme kaynaklı)
capraz_grup = {}
for c in capraz_bilgi:
    anahtar = (modul(c["a"]), round(c["boy"]), round(c["aci"]))
    capraz_grup.setdefault(anahtar, []).append(c)
for (m, boy, aci), cs in sorted(capraz_grup.items()):
    satirlar.append((f"CAPRAZ_{m} – kutu 20x20x2, uçlar açılı kesim (~{aci}°)", boy, len(cs), sum(c["kg"] for c in cs)))
def hacim_kg(onek):
    return sum(p["sekil"].Volume() for p in parcalar if p["ad"].startswith(onek)) * YOGUNLUK


satirlar += [
    (f"SILINDIR_GOMLEK – boru {hid.GOMLEK_D:.0f}x{hid.GOMLEK_T:.0f} (iç Ø{hid.GOMLEK_D - 2 * hid.GOMLEK_T:.0f}), dip ve kafaya kaynaklı",
     round(SIL_O["gomlek_boy"]), 1, hacim_kg("SILINDIR_GOMLEK")),
    (f"PISTON_MILI – krom mil Ø{hid.MIL_D:.0f} h8", round(SIL_O["mil_boy"]), 1, hacim_kg("HAYALET_PISTON_MILI")),
    (f"STROK_SONU_HALKASI – Ø{hid.HALKA_D:.0f}x{hid.HALKA_H:.0f}, iki yağ geçiş düzlüğü (torna)", "", 1,
     hacim_kg("HAYALET_STROK_SONU_HALKASI")),
    (f"SILINDIR_DIP_BLOGU – {hid.DIP_A:.0f}x{hid.DIP_A:.0f}x{hid.DIP_H:.0f}, 1/4\" BSP yan giriş (talaşlı)", "", 1,
     hacim_kg("SILINDIR_DIP_BLOGU")),
    (f"SILINDIR_AYAK_PLAKASI – lazer sac {hid.AYAK_A:.0f}x{hid.AYAK_A:.0f}x{hid.AYAK_T:.0f}, 4xØ9", "", 1,
     hacim_kg("SILINDIR_AYAK_PLAKASI")),
    (f"SILINDIR_KAFA_GOVDESI – Ø{hid.KAFA_D:.0f}x{hid.KAFA_H:.0f}, iç M42x1,5 (torna, gömleğe kaynaklı)", "", 1,
     hacim_kg("SILINDIR_KAFA_GOVDESI")),
    (f"SILINDIR_KAFA_KAPAGI – Ø{hid.KAFA_D:.0f} flanş + M42 boyun, burç ve keçe yuvalı (torna, sökülür)", "", 1,
     hacim_kg("SILINDIR_KAFA_KAPAGI")),
    (f"TANK – {hid.TANK_T:.0f} mm sac {hid.TANK_X:.0f}x{hid.TANK_Y:.0f}x{hid.TANK_Z:.0f}, kaynaklı", "", 1, hacim_kg("TANK") - hacim_kg("TANK_KAPAGI")),
    (f"TANK_KAPAGI – lazer sac {hid.TANK_X + 20:.0f}x{hid.TANK_Y + 20:.0f}x{hid.KAPAK_T:.0f}, motor/pompa delikli", "", 1,
     hacim_kg("TANK_KAPAGI")),
    (f"YAG_TAVASI – {hid.TAVA_T} mm sac {hid.TAVA_X:.0f}x{hid.TAVA_Y:.0f}x{hid.TAVA_Z:.0f} + 4 ayak (tabana M8)", "", 1,
     hacim_kg("YAG_TAVASI") + hacim_kg("TAVA_AYAGI")),
]
kasa_kg = sum(p["sekil"].Volume() for p in parcalar if p["ad"].endswith("_KASA")) * YOGUNLUK
kanat_kg = sum(p["sekil"].Volume() for p in parcalar if p["ad"].endswith("_KANAT")) * YOGUNLUK
satirlar.append((f"KAPI_KASASI – 2 mm bükme sac U {KASA_P}x{KASA_D}: 2 dikme {KAPI_NET_H} + başlık {KASA_X[1] - KASA_X[0]:.0f}",
                 "", len(DURAKLAR), kasa_kg))
satirlar.append((f"KAPI_KANADI – 1,5 mm sac tepsi {KANAT_X[1] - KANAT_X[0]:.0f}x{KAPI_NET_H + 15}x{KANAT_T}, "
                 f"{PENCERE[0]}x{PENCERE[1]} cam yuvalı", "", len(DURAKLAR), kanat_kg))
profil_m = ((DIKME_ALT_BOY + DIKME_UST_BOY) * 4 + sum(adet * boy for (_, _, boy), adet in kusak_grup.items())
            + sum(c["boy"] for c in capraz_bilgi)) / 1000
with open(os.path.join(CIKTI, "kesim_listesi.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Parça", "Boy (mm)", "Adet", "Ağırlık (kg)"])
    for ad, boy, adet, kg in satirlar:
        w.writerow([ad, boy, adet, tr(kg)])
    w.writerow(["TOPLAM", tr(profil_m, 2) + " m profil (40x40, 40x20, 20x20)",
                sum(s[2] for s in satirlar), tr(sum(s[3] for s in satirlar))])

with open(os.path.join(CIKTI, "satin_alma_listesi.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Malzeme", "Adet", "Not"])
    for r in [
        ("Döner teker, tablalı, frenli, Ø100-125, en az 100 kg/adet", 4, "ÖNCE ALIN; tabla delik düzeni ölçülüp çizime işlenecek"),
        ("Ayar ayağı M16, Ø80 pabuç, en az 250 kg/adet", 4, "destek kulağının ucuna"),
        ("Somun M16", 8, "her ayağa alt + üst"),
        ("Altıgen cıvata M10x35 8.8", 12, "dikme ayağı (somun taban altında)"),
        ("Altıgen cıvata M10x35 8.8", 16, "destek kulağı, alttan"),
        ("Altıgen cıvata M10x30 8.8", 12, "ek flanşı, SADECE ÜSTTEN takılır"),
        ("Altıgen cıvata M10x30 8.8", 16, "teker"),
        ("Somun M10 fiberli + pul", 28, "dikme ayağı (12), teker (16)"),
        ("Kaynak somunu M10 (kare, DIN 928)", 16, "taban sacının ÜSTÜNE kaynatılır (kulak cıvataları için)"),
        ("Kaynak somunu M10 (kare, DIN 928)", 12, "alt ek flanşının ALTINA kaynatılır (lokma üstten girer)"),
        ("Yarı otomatik kat kapısı kilidi, kontaklı (üründeki standart kilit)", 3,
         "KİLİT ALINCA ÖLÇÜN; 'kapı kapalı' ve 'kilitli' kontakları emniyet devresine seri, Arduino'dan bağımsız"),
        ("Kabin kilit kamı (geri çekilen, bobinli) + kam konum kontağı", 1, "kam geri çekik değilse kabin hareket etmez"),
        ("Acil açma üçgen anahtarı", 1, "kilitle uyumlu"),
        ("Yaylı menteşe (kendiliğinden kapatır)", 6, "kanat başına 2"),
        ("Kapı kolu", 3, ""),
        ("Kat buton kutusu (çağırma butonu + ışık)", 3, ""),
        ("Alüminyum kat eşiği profili", 3, f"{KASA_X[1] - KASA_X[0]:.0f} mm boy, kasanın altına kadar"),
        ("Akrilik pencere", 3, f"{PENCERE[0] + 10}x{PENCERE[1] + 10} mm"),
        ("Otomatik kabin kapısı: 2 teleskopik kanat + küçük motor + kayış", 1,
         "maket boyunda hazır operatör yok; özel imalat (gerçek operatör gibi hız profili)"),
        ("Elektrik motoru 0,25 kW, 4 kutup, 63 gövde, B14 flanş, trifaze", 1, "invertörden beslenir"),
        ("Dişli pompa ~1 cc/dev, MOTOR OLARAK DA ÇALIŞABİLEN (çift yönlü)", 1,
         "inişte geri döner; en düşük devri ve geri dönüşe uygunluğu tedarikçiden teyit"),
        ("İnvertör 0,4 kW, monofaze giriş, vektör kontrol, DAHİLİ FREN KIYICI + fren direnci", 1,
         "inişte motor jeneratör olur, enerji dirençte yakılır"),
        ("Çan (kampana) + kaplin (63 motor / küçük pompa)", 1, ""),
        ("Valf bloğu: çek valf + oturmalı NC iniş valfi 24 V DC + emniyet valfi + elle acil indirme", 1,
         f"emniyet ayarı ~{hid.hesap(STROK)['emniyet_bar']:.0f} bar"),
        ("Manometre 0-100 bar, Ø63, gliserinli", 1, "öne bakar, fuarda görünür"),
        ("Basınç transmitteri 0-100 bar, 4-20 mA", 1, "Arduino kaydı için"),
        ("Hortum patlama valfi 1/4\", düşük debi (1-3 L/dk ayarlı)", 1, "silindir girişine; asansör tiplerinin altında, tedarikçiden teyit"),
        ("Hidrolik hortum 1/4\" 2SN + iki uçta rakor (pres)", 1,
         f"boy ~{HORTUM_BOY / 1000 + 0.15:.2f} m (modelde {HORTUM_BOY:.0f} mm + pay); kuyuya sağ yüzden R1 altından girer".replace(".", ",", 1)),
        ("Hortum kelepçesi (P tipi) + ayak", 2, "tabana"),
        ("Emiş süzgeci, seviye göstergesi, hava/dolum tapası + TAŞIMA İÇİN KÖR TAPA", 1, ""),
        ("Hidrolik yağ HLP 32", "5 L", ""),
        ("Silindir keçe takımı: bronz burç Ø20x25x20, U-keçe 20x28x5, toz keçesi 20x28x4", 1, "kafa kapağının içinde"),
        ("Hava alma vidası M6", 1, "kafa kapağında"),
        ("Altıgen cıvata M8x25 + somun + pul", 8, "silindir ayağı (4) + yağ tavası (4)"),
        ("Silindirik pim Ø10x20", 16, "ayak (8) + ek flanşı (8); delikler çift halinde raybalanır"),
    ]:
        w.writerow(r)

with open(os.path.join(CIKTI, "taban_delik_tablosu_TASLAK.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["No", "X (mm)", "Y (mm)", "Çap (mm)", "Görev"])
    for i, (x, y, d, g) in enumerate(sorted(delikler, key=lambda t: (t[1], t[0])), 1):
        w.writerow([i, tr(x, 1), tr(y, 1), d, g])

# =====================================================================
# GÖRSELLER
# =====================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Patch, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def bol(T, maks_kenar):
    """Büyük üçgenleri 4'e bölerek küçült (matplotlib derinlik sıralaması düzgün çalışsın)."""
    while True:
        kenar = np.max(np.linalg.norm(T - np.roll(T, 1, axis=1), axis=2), axis=1)
        buyuk = kenar > maks_kenar
        if not buyuk.any():
            return T
        B = T[buyuk]
        m01, m12, m20 = (B[:, 0] + B[:, 1]) / 2, (B[:, 1] + B[:, 2]) / 2, (B[:, 2] + B[:, 0]) / 2
        yeni = np.concatenate([np.stack(s, axis=1) for s in (
            (B[:, 0], m01, m20), (m01, B[:, 1], m12), (m20, m12, B[:, 2]), (m01, m12, m20))])
        T = np.concatenate([T[~buyuk], yeni])


def ucgenler(sekil, renk, maks_kenar):
    V, F = sekil.tessellate(1.0, 0.4)
    if not F:
        return None, None
    V = np.array([(v.x, v.y, v.z) for v in V])
    T = bol(V[np.array(F)], maks_kenar)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    isik = np.array([-0.45, -0.75, 0.5])
    isik /= np.linalg.norm(isik)
    golge = 0.45 + 0.55 * np.abs(n @ isik)
    c = np.clip(np.array(renk[:3])[None, :] * golge[:, None], 0, 1)
    return T, np.hstack([c, np.full((len(T), 1), renk[3])])


LEJANT = [("taban", "Taban sacı"), ("dikme", "Dikme 40x40x3"), ("kusak", "Kuşak 40x20x2"), ("capraz", "Çapraz 20x20x2"),
          ("kose", "Köşe plakası (ayak / ek flanşı)"), ("kasa", "Kat kapısı kasası"), ("kanat", "Kat kapısı kanadı"),
          ("kilit", "Kilit, kam, buton"), ("sil_govde", "Silindir"), ("unite_sac", "Tank / tava"), ("motor", "Motor"),
          ("kulak", "Destek kulağı (fuarda takılır)"), ("civata", "Cıvata / somun"),
          ("kabin", "Hayalet: kabin"), ("ray", "Hayalet: U kılavuz"), ("makara", "Hayalet: zincir makarası"),
          ("tank", "Hayalet: güç ünitesi"), ("yer_tutucu", "Hayalet: kelepçe, şalter çubuğu")]


def sahne(ax, liste, sinir, elev, azim, baslik, maks_kenar, kirp=False, zoom=1.0):
    tum_T, tum_C = [], []
    kutu_sinir = kutu(sinir[0][0], sinir[0][1], sinir[1][0], sinir[1][1], sinir[2][0], sinir[2][1])
    for p in liste:
        s = p["sekil"]
        if kirp:
            if kesisim(s, kutu_sinir) <= 1e-6:
                continue
            s = s.intersect(kutu_sinir)
        T, C = ucgenler(s, p["renk"], maks_kenar)
        if T is not None:
            tum_T.append(T)
            tum_C.append(np.repeat(C[:1], len(T), axis=0) if len(C) != len(T) else C)
    pc = Poly3DCollection(np.concatenate(tum_T), facecolors=np.concatenate(tum_C), edgecolors="none", linewidths=0)
    ax.add_collection3d(pc)
    ax.set_xlim(*sinir[0]); ax.set_ylim(*sinir[1]); ax.set_zlim(*sinir[2])
    ax.set_box_aspect([sinir[i][1] - sinir[i][0] for i in range(3)], zoom=zoom)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(baslik, fontsize=12, fontweight="bold")


def lejant_ve_damga(fig, ncol):
    fig.legend(handles=[Patch(color=RENK[k][:3], label=t) for k, t in LEJANT], loc="lower center",
               bbox_to_anchor=(0.5, 0.035), ncol=ncol, fontsize=8, frameon=False)
    fig.text(0.5, 0.01, "TASLAK YERLEŞİM MODELİ — üretim çizimi değildir", ha="center", color="#b00020",
             fontsize=10, fontweight="bold")


gorunur = [p for p in parcalar if p["tur"] != "ZARF"]

fig = plt.figure(figsize=(9, 13), dpi=130)
ax = fig.add_subplot(111, projection="3d")
sahne(ax, gorunur, ((-60, 960), (-260, 860), (0, Z_TEPE + 20)), 18, -58,
      f"Maket taban + dikmeler — {TABAN_EN}x{TABAN_DERIN}, yükseklik {Z_TEPE} mm", 60, zoom=1.0)
lejant_ve_damga(fig, 3)
fig.subplots_adjust(0, 0.09, 1, 0.99)
fig.savefig(os.path.join(CIKTI, "onizleme.png"))
plt.close(fig)

# Sol ön köşe: üstten ve alttan
bolge = ((-40, 330), (-240, 260), (0, 330))
fig = plt.figure(figsize=(16, 8), dpi=120)
ax1 = fig.add_subplot(121, projection="3d")
sahne(ax1, gorunur, bolge, 30, -52, "Sol ön köşe — ÜSTTEN\nköşe plakası, cıvata başları, kaynak somunları", 12, kirp=True, zoom=1.2)
ax2 = fig.add_subplot(122, projection="3d")
sahne(ax2, gorunur, bolge, -22, -52, "Sol ön köşe — ALTTAN\ndestek kulağı, somun cepleri, teker", 12, kirp=True, zoom=1.2)
lejant_ve_damga(fig, 6)
fig.subplots_adjust(0, 0.1, 1, 0.95, wspace=0)
fig.savefig(os.path.join(CIKTI, "onizleme_taban_kosesi.png"))
plt.close(fig)


# --- Teknik resim: üst görünüş + ön görünüş + yan görünüş ---
def ciz_teknik():
    fig = plt.figure(figsize=(24, 11.5), dpi=110)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1, 0.95])
    a1 = fig.add_subplot(gs[0])
    a2 = fig.add_subplot(gs[1])
    a3 = fig.add_subplot(gs[2])

    # ÜST GÖRÜNÜŞ (plan)
    a1.set_aspect("equal")
    a1.add_patch(FancyBboxPatch((0, 0), TABAN_EN, TABAN_DERIN, boxstyle=f"round,pad=0,rounding_size={TABAN_KOSE_R}",
                                fc="#e9ecef", ec="k", lw=1.6))
    for k, (cx, cy, sx, sy) in TABAN_KOSELERI.items():   # kulaklar (altta)
        x0 = cx if sx > 0 else cx - KULAK_GEN
        y0 = cy - KULAK_TASMA if sy > 0 else cy - KULAK_ICERI
        a1.add_patch(Rectangle((x0, y0), KULAK_GEN, KULAK_TASMA + KULAK_ICERI, fc="none", ec="#e8890c", lw=1.3, ls=(0, (4, 2))))
        ax_, ay_ = kose_nokta(KULAK_AYAK, cx, cy, sx, sy)
        a1.add_patch(Circle((ax_, ay_), 40, fc="none", ec="#555", lw=0.8))
        a1.add_patch(Circle((ax_, ay_), KULAK_AYAK_DELIK / 2, fc="#555"))
    for (tx, ty) in TEKER_MERKEZ:   # tekerler (altta)
        a1.add_patch(Rectangle((tx - TEKER_TABLA[0] / 2, ty - TEKER_TABLA[1] / 2), *TEKER_TABLA, fc="none", ec="#1f5fbf", lw=1.0, ls=":"))
        a1.plot(tx, ty, "+", color="#1f5fbf", ms=7)
    for k, (cx, cy, sx, sy) in DIKME_KOSELERI.items():   # köşe plakaları + dikmeler
        x0 = cx if sx > 0 else cx - KOSE_PL
        y0 = cy if sy > 0 else cy - KOSE_PL
        a1.add_patch(Rectangle((x0, y0), KOSE_PL, KOSE_PL, fc="#c9d6ea", ec="#10407f", lw=1.0))
        dx0 = cx if sx > 0 else cx - PROFIL_A
        dy0 = cy if sy > 0 else cy - PROFIL_A
        a1.add_patch(Rectangle((dx0, dy0), PROFIL_A, PROFIL_A, fc="#2a61b8", ec="k", lw=0.8))
    # Hayaletler
    gri = dict(fc="none", ec="#888", lw=0.9, ls="--")
    a1.add_patch(Rectangle((KABIN_X0, KABIN_ON_Y), KABIN_EN, KABIN_DERIN, fc="#fff3c4", ec="#b8860b", lw=1.0, ls="-."))
    a1.text(KABIN_MX, KABIN_ON_Y + KABIN_DERIN / 2 + 40, f"KABİN {KABIN_EN}x{KABIN_DERIN}\n(yerleşim)", ha="center", fontsize=8, color="#8a6d00")
    # Sırt çantası askı (üst ve alt kiriş, dikmeler) — kesik çizgi
    a1.add_patch(Rectangle((ASKI_X_SOL[0], ASKI_UST_Y[0]), ASKI_X_SAG[1] - ASKI_X_SOL[0], ASKI_ALT_Y[1] - ASKI_UST_Y[0],
                           fc="#e6e6e6", ec="#777", lw=0.8, ls="--"))
    for (xa, xb) in (ASKI_X_SOL, ASKI_X_SAG):
        a1.add_patch(Rectangle((xa, KANAL_Y[0] + 2), xb - xa, KANAL_Y[1] - KANAL_Y[0] - 4, fc="#bbb", ec="#777", lw=0.6))
    a1.text(KABIN_MX - 45, ASKI_UST_Y[0] + 10, "sırt çantası askı", ha="center", fontsize=7, color="#555")
    # U kılavuzlar (sırtı dışta, ağzı içe)
    for xs, xf in ((SOL_KILAVUZ_SIRT, 1), (SAG_KILAVUZ_SIRT, -1)):
        a1.add_patch(Rectangle((min(xs, xs + xf * KILAVUZ_T), Y_K0), KILAVUZ_T, KILAVUZ_H, fc="#555", ec="none"))
        for yy in (Y_K0, Y_K1 - KILAVUZ_T):
            a1.add_patch(Rectangle((min(xs, xs + xf * KILAVUZ_B), yy), KILAVUZ_B, KILAVUZ_T, fc="#555", ec="none"))
        a1.add_patch(Rectangle((min(xs, xs + xf * KILAVUZ_B), Y_K1), KILAVUZ_B, ARKA_KUSAK_Y - Y_K1, **gri))
    a1.text(SOL_KILAVUZ_SIRT - 5, Y_K0 - 22, "U kılavuz", fontsize=7, color="#444", ha="left")
    a1.text(SAG_KILAVUZ_SIRT + 5, Y_K0 - 22, "U kılavuz", fontsize=7, color="#444", ha="right")
    # Silindir, zincir makaraları, zincir kolları, sabit uç traversi
    a1.add_patch(Circle((KABIN_MX, SILINDIR_Y), PISTON_GOVDE_D / 2, fc="#dfe3ea", ec="#555", lw=1))
    for zx in ZINCIR_X:
        a1.add_patch(Rectangle((zx - MAKARA_GEN / 2, SILINDIR_Y - MAKARA_R), MAKARA_GEN, 2 * MAKARA_R, fc="none", ec="#c00", lw=0.9, ls="--"))
        a1.plot([zx, zx], [ZINCIR_ON_Y, ZINCIR_ARKA_Y], "o", color="#222", ms=3)
    a1.add_patch(Rectangle((ZINCIR_X[0] - 25, ZINCIR_ARKA_Y - 12), ZINCIR_X[1] - ZINCIR_X[0] + 50, 24, **gri))
    a1.annotate("silindir + 2 zincir makarası\nzincir sabit uçları (gergili)", (KABIN_MX, SILINDIR_Y),
                (KABIN_MX + 40, TABAN_DERIN + 60), ha="left", fontsize=7, color="#c00",
                arrowprops=dict(arrowstyle="->", color="#c00", lw=0.8))
    a1.add_patch(Circle(SALTER_CUBUK, 6, fc="#999", ec="#555"))
    for tx in TAMPON_X:
        a1.add_patch(Circle((tx, TAMPON_Y), 18, **gri))
    a1.text(TAMPON_X[1] + 22, TAMPON_Y - 30, "tampon", fontsize=7, ha="left", color="#666")
    # Kat kapısı (üstten): kasa, eşik, kanat, açılma yayı, kilit
    from matplotlib.patches import Arc
    a1.add_patch(Rectangle((KASA_X[0], 0), KASA_X[1] - KASA_X[0], KASA_D, fc="#8c4d40", ec="k", lw=0.5, alpha=0.8))
    a1.add_patch(Rectangle((KASA_X[0], KUSAK_D), KASA_X[1] - KASA_X[0], ESIK_Y1 - KUSAK_D, fc="#c0c2c6", ec="k", lw=0.4))
    a1.add_patch(Rectangle((KANAT_X[0], -KANAT_T), KANAT_X[1] - KANAT_X[0], KANAT_T, fc="#eee1b8", ec="k", lw=0.6))
    R = kapi_bilgi[0]["R"]
    a1.add_patch(Arc((KANAT_X[0] - 6, -KANAT_T / 2), 2 * R, 2 * R, theta1=270, theta2=360, ec="#8c4d40", lw=1, ls="--"))
    a1.plot([KANAT_X[0] - 6, KANAT_X[0] - 6], [-KANAT_T / 2, -KANAT_T / 2 - R], color="#8c4d40", lw=1.5)
    a1.text(KANAT_X[0] + 10, -KANAT_T / 2 - R + 15, "kat kapısı açılışı", fontsize=7, color="#8c4d40")
    a1.add_patch(Rectangle((KILIT_X[0], KASA_D), KILIT_W, KILIT_D, fc="#d4a017", ec="k", lw=0.5))
    a1.text(KILIT_X[1] + 4, KASA_D + 10, "kilit", fontsize=7, color="#8a6d00")
    a1.add_patch(Rectangle((UNITE_XC - hid.TAVA_X / 2, UNITE_YC - hid.TAVA_Y / 2), hid.TAVA_X, hid.TAVA_Y,
                           fc="none", ec="#e07b00", lw=0.9, ls=":"))
    a1.add_patch(Rectangle((UNITE_XC - hid.TANK_X / 2, UNITE_YC - hid.TANK_Y / 2), hid.TANK_X, hid.TANK_Y,
                           fc="none", ec="#2e8b57", lw=1.0, ls="--"))
    a1.add_patch(Circle(UNI_O["motor_eksen"], hid.MOTOR_D / 2, fc="none", ec="#2e8b57", lw=0.8))
    a1.text(UNITE_XC, UNITE_YC - 20, "GÜÇ ÜNİTESİ\n5 L tank, 0,25 kW\ntava tabana cıvatalı", ha="center", va="center",
            fontsize=7.5, color="#2e8b57")
    # Delikler
    renkler = {"dikme": "#c1121f", "pim": "#7b2cbf", "teker": "#1f5fbf", "destek": "#2d6a4f",
               "silindir": "#444444", "yağ": "#e07b00"}
    for (x, y, d, g) in delikler:
        anahtar = next(k for k in renkler if g.startswith(k))
        a1.add_patch(Circle((x, y), d / 2, fc=renkler[anahtar], ec="k", lw=0.4))
        if anahtar == "destek":
            a1.add_patch(Rectangle((x - 8.5, y - 8.5), 17, 17, fc="none", ec=renkler[anahtar], lw=0.6))
    # Ölçüler
    def olcu(p1, p2, metin, ofs, yatay=True):
        if yatay:
            y = p1[1] + ofs
            a1.annotate("", (p1[0], y), (p2[0], y), arrowprops=dict(arrowstyle="<->", lw=0.8))
            a1.text((p1[0] + p2[0]) / 2, y + 8, metin, ha="center", fontsize=8)
        else:
            x = p1[0] + ofs
            a1.annotate("", (x, p1[1]), (x, p2[1]), arrowprops=dict(arrowstyle="<->", lw=0.8))
            a1.text(x - 8, (p1[1] + p2[1]) / 2, metin, ha="right", va="center", fontsize=8, rotation=90)
    olcu((0, TABAN_DERIN), (TABAN_EN, TABAN_DERIN), f"{TABAN_EN}", 250)
    olcu((0, TABAN_DERIN), (KUYU_EN, TABAN_DERIN), f"kuyu {KUYU_EN}", 215)
    olcu((KUYU_EN, TABAN_DERIN), (TABAN_EN, TABAN_DERIN), f"ünite {TABAN_EN - KUYU_EN}", 215)
    olcu((0, 0), (0, TABAN_DERIN), f"{TABAN_DERIN}", -70, yatay=False)
    olcu((0, -KULAK_TASMA), (0, 0), f"{KULAK_TASMA}", -70, yatay=False)
    olcu((0, TABAN_DERIN), (0, TABAN_DERIN + KULAK_TASMA), f"{KULAK_TASMA}", -70, yatay=False)
    olcu((KULAK_AYAK[0], KULAK_AYAK[1]), (TABAN_EN - KULAK_AYAK[0], KULAK_AYAK[1]), f"ayak arası {TABAN_EN - 2 * KULAK_AYAK[0]}", -75)
    olcu((0, KULAK_AYAK[1]), (0, TABAN_DERIN - KULAK_AYAK[1]), f"ayak arası {TABAN_DERIN - 2 * KULAK_AYAK[1]}", -110, yatay=False)
    a1.text(TABAN_EN / 2, -KULAK_TASMA - 105, "ÖN (kapı tarafı)", ha="center", fontsize=10, fontweight="bold")
    a1.set_xlim(-130, TABAN_EN + 60)
    a1.set_ylim(-KULAK_TASMA - 130, TABAN_DERIN + KULAK_TASMA + 90)
    a1.set_title("ÜST GÖRÜNÜŞ — taban sacı (mm)", fontsize=12, fontweight="bold")
    a1.legend(handles=[
        Patch(color=renkler["dikme"], label="Ø11 dikme ayağı (M10, somun altta)"),
        Patch(color=renkler["pim"], label="Ø10 pim (çift halinde raybalanır)"),
        Patch(color=renkler["teker"], label="Ø11 teker (TEKER ALINCA ÖLÇÜLECEK)"),
        Patch(color=renkler["destek"], label="Ø11 destek kulağı (üstte M10 kaynak somunu)"),
        Patch(color=renkler["silindir"], label="Ø9 silindir ayağı (M8)"),
        Patch(color=renkler["yağ"], label="Ø9 yağ tavası ayağı (M8)"),
        Patch(fc="none", ec="#e8890c", ls="--", label="Destek kulağı (sac altında, sökülür)"),
        Patch(fc="none", ec="#1f5fbf", ls=":", label="Teker tablası (sac altında)"),
        Patch(fc="#c9d6ea", ec="#10407f", label="Köşe plakası 110x110x10"),
    ], loc="upper center", fontsize=8, framealpha=0.95, bbox_to_anchor=(0.5, -0.04), ncol=2)
    a1.text(TABAN_EN / 2, TABAN_DERIN / 2 - 10, "TASLAK\nLAZERE GÖNDERMEYİN", ha="center", va="center", fontsize=34,
            color="#d00000", alpha=0.22, fontweight="bold", rotation=18)
    a1.tick_params(labelsize=7)
    a1.grid(alpha=0.15)

    # ÖN GÖRÜNÜŞ (X-Z)
    a2.set_aspect("equal")
    a2.axhline(0, color="k", lw=1.5)
    a2.add_patch(Rectangle((0, TEKER_H), TABAN_EN, TABAN_T, fc="#6c757d", ec="k"))
    for (tx, _) in TEKER_MERKEZ[::2]:
        a2.add_patch(Circle((tx, TEKER_D / 2), TEKER_D / 2, fc="#333", ec="k"))
        a2.add_patch(Rectangle((tx - 20, TEKER_D / 2), 40, TEKER_H - TEKER_D / 2, fc="#555", ec="k", lw=0.5))
    for xk in (0, TABAN_EN - KULAK_GEN):
        a2.add_patch(Rectangle((xk, KULAK_Z0), KULAK_GEN, KULAK_T, fc="#e8890c", ec="k", lw=0.5))
        a2.add_patch(Rectangle((xk + KULAK_AYAK[0] - 30, 0), 60, 15, fc="#555"))
    for xd in (0, KUYU_EN - PROFIL_A):
        a2.add_patch(Rectangle((xd, AYAK_UST), PROFIL_A, DIKME_ALT_BOY, fc="#2a61b8", ec="k", lw=0.6))
        a2.add_patch(Rectangle((xd, BOLME_Z + KOSE_PL_T), PROFIL_A, DIKME_UST_BOY, fc="#5b8fdc", ec="k", lw=0.6))
        xp = xd if xd == 0 else KUYU_EN - KOSE_PL
        for z in kose_z.values():
            a2.add_patch(Rectangle((xp, z), KOSE_PL, KOSE_PL_T, fc="#10407f", ec="k", lw=0.4))
    # Arkadaki mekanizma (kılavuzlar, silindir, zincirler) — kabin önde, yarı saydam
    for xs, xf in ((SOL_KILAVUZ_SIRT, 1), (SAG_KILAVUZ_SIRT, -1)):
        a2.add_patch(Rectangle((min(xs, xs + xf * KILAVUZ_B), RAY_ALT), KILAVUZ_B, RAY_UST - RAY_ALT, fc="#999", ec="none", alpha=0.45))
    a2.add_patch(Rectangle((KABIN_MX - PISTON_GOVDE_D / 2, TABAN_UST), PISTON_GOVDE_D, SILINDIR_UST - TABAN_UST, fc="#cfd4dc", ec="#555"))
    a2.plot([KABIN_MX, KABIN_MX], [SILINDIR_UST, MAKARA_Z0 - BASLIK_ALT], color="#555", lw=3)
    for zx in ZINCIR_X:
        a2.plot([zx, zx], [GERGI_UST, MAKARA_Z0], color="#222", lw=1.2)
        for zm, ls in ((MAKARA_Z0, "-"), (MAKARA_Z_MAX, "--")):
            a2.add_patch(Rectangle((zx - MAKARA_GEN / 2, zm - MAKARA_R), MAKARA_GEN, 2 * MAKARA_R, fc="none", ec="#c00", lw=1.2, ls=ls))
    a2.add_patch(Rectangle((ZINCIR_X[0] - 25, TABAN_UST), ZINCIR_X[1] - ZINCIR_X[0] + 50, SABIT_TRAVERS_Z - TABAN_UST, fc="#888"))
    a2.text(ZINCIR_X[1] + 20, MAKARA_Z_MAX, "zincir makaraları\nen üstte", fontsize=7, color="#c00", va="center")
    a2.text(ZINCIR_X[1] + 20, MAKARA_Z0, "zincir makaraları\n1. durakta", fontsize=7, color="#c00", va="center")
    for i, z in enumerate(DURAKLAR):
        a2.add_patch(Rectangle((KABIN_X0, z), KABIN_EN, KABIN_H, fc="#fff3c4" if i == 0 else "none",
                               ec="#b8860b", lw=1.0, ls="-" if i == 0 else "--", alpha=0.85 if i == 0 else 1))
        a2.text(KABIN_MX, z + KABIN_H / 2, f"{i + 1}. durak", ha="center", va="center", fontsize=9, color="#8a6d00")
    a2.add_patch(Rectangle((ASKI_X_SOL[0], z_aski_alt), ASKI_X_SAG[1] - ASKI_X_SOL[0], 40, fc="#999", ec="none", alpha=0.6))
    a2.add_patch(Rectangle((ASKI_X_SOL[0], z_tavan + 20), ASKI_X_SAG[1] - ASKI_X_SOL[0], 40, fc="#999", ec="none", alpha=0.6))
    ux0 = UNITE_XC - hid.TANK_X / 2
    a2.add_patch(Rectangle((UNITE_XC - hid.TAVA_X / 2, TAVA_Z), hid.TAVA_X, hid.TAVA_Z, fc="#bcd3ea", ec="#1f5fbf", lw=0.6))
    a2.add_patch(Rectangle((ux0, UNI_O["zt0"]), hid.TANK_X, hid.TANK_Z, fc="#6f9fd0", ec="#1f5fbf"))
    a2.add_patch(Rectangle((ux0 - 10, UNI_O["zt1"]), hid.TANK_X + 20, hid.KAPAK_T, fc="#1f5fbf", ec="k", lw=0.4))
    a2.add_patch(Rectangle((UNITE_XC - hid.CAN_D / 2, UNI_O["zk1"]), hid.CAN_D, hid.CAN_H, fc="#8fb89a", ec="#2e8b57"))
    a2.add_patch(Rectangle((UNITE_XC - hid.MOTOR_D / 2, UNI_O["zk1"] + hid.CAN_H), hid.MOTOR_D, hid.MOTOR_H,
                           fc="#a7d3b3", ec="#2e8b57"))
    a2.text(UNITE_XC, UNI_O["tepe"] + 15, "0,25 kW", ha="center", fontsize=7, color="#2e8b57")
    a2.add_patch(Rectangle((PANO_X0, PANO_Z0), hid.PANO_X, hid.PANO_Z, fc="#dcdee0", ec="k", lw=0.6))
    a2.add_patch(Circle((PANO_X0 + 45, PANO_Z0 + hid.PANO_Z - 50), 20, fc="#d91a1a", ec="k", lw=0.5))
    a2.text(PANO_X0 + hid.PANO_X / 2, PANO_Z0 + 90, "PANO\n+ invertör", ha="center", fontsize=7.5)
    # Ön yüz kuşakları (önde) ve kat kapısı açıklıkları
    for r in YUZ_KUSAKLARI["ON"]:
        a2.add_patch(Rectangle((PROFIL_A, KUSAK[r]), KAFES_BOY_X, KUSAK_H, fc="#3a7fd5", ec="#10407f", lw=0.5, alpha=0.85))
        a2.text(KUYU_EN + 4, KUSAK[r] + KUSAK_H / 2, r, fontsize=6.5, va="center", color="#10407f")
    for s in DURAKLAR:   # kat kapıları: kasa, kanat, pencere, kilit, buton
        a2.add_patch(Rectangle((KASA_X[0], s), KASA_X[1] - KASA_X[0], KAPI_NET_H + KASA_P, fc="#8c4d40", ec="k", lw=0.5))
        a2.add_patch(Rectangle((KANAT_X[0], s - 5), KANAT_X[1] - KANAT_X[0], KAPI_NET_H + 15, fc="#eee1b8", ec="k", lw=0.6))
        px = (KANAT_X[0] + KANAT_X[1]) / 2 - 20
        a2.add_patch(Rectangle((px - PENCERE[0] / 2, s + 80), PENCERE[0], PENCERE[1], fc="#9fcbef", ec="k", lw=0.4))
        a2.add_patch(Rectangle((KILIT_X[0], s + KILIT_Z_OFS), KILIT_W, KILIT_H, fc="none", ec="#d4a017", lw=1.0, ls="--"))
        a2.add_patch(Rectangle((KILIT_X[1] - 20, s + 150), 40, 60, fc="#d4a017", ec="k", lw=0.4))
    a2.text(KILIT_X[1] + 22, DURAKLAR[0] + 180, "buton", fontsize=6.5, color="#8a6d00")
    a2.text(KILIT_X[0], DURAKLAR[0] + KILIT_Z_OFS + KILIT_H + 8, "kilit (arkada)", fontsize=6.5, color="#8a6d00")
    # Kot çizgileri
    kotlar = [(0, "zemin 0"), (TABAN_UST, f"taban üstü {TABAN_UST}"), (DURAKLAR[0], f"1. durak {DURAKLAR[0]}"),
              (DURAKLAR[1], f"2. durak {DURAKLAR[1]}"), (BOLME_Z, f"BÖLME {BOLME_Z}"),
              (DURAKLAR[2], f"3. durak {DURAKLAR[2]}"), (Z_TEPE, f"tepe {Z_TEPE}")]
    for z, t in kotlar:
        renk = "#d00000" if "BÖLME" in t else "#333"
        a2.plot([-40, TABAN_EN + 30], [z, z], color=renk, lw=0.6 if "BÖLME" not in t else 1.4, ls=":" if "BÖLME" not in t else "--")
        a2.text(TABAN_EN + 40, z, t, va="center", fontsize=8.5, color=renk, fontweight="bold" if "BÖLME" in t else None)
    a2.annotate("", (-60, 0), (-60, BOLME_Z), arrowprops=dict(arrowstyle="<->", color="#d00000"))
    a2.text(-75, BOLME_Z / 2, f"alt modül {BOLME_Z}\n(kapı {KAPI_H}'den geçer)", rotation=90, ha="right", va="center", fontsize=8, color="#d00000")
    a2.annotate("", (-60, BOLME_Z), (-60, Z_TEPE), arrowprops=dict(arrowstyle="<->", color="#10407f"))
    a2.text(-75, (BOLME_Z + Z_TEPE) / 2, f"üst modül {Z_TEPE - BOLME_Z}", rotation=90, ha="right", va="center", fontsize=8, color="#10407f")
    a2.set_xlim(-190, TABAN_EN + 330)
    a2.set_ylim(-60, Z_TEPE + 80)
    a2.set_title("ÖN GÖRÜNÜŞ — kuşaklar, kapılar, yükseklik (mm)", fontsize=12, fontweight="bold")
    a2.tick_params(labelsize=7)
    a2.grid(alpha=0.12)

    # YAN GÖRÜNÜŞ (sol yüz, Y-Z): kuşaklar + zikzak çaprazlar
    from matplotlib.patches import Polygon
    a3.set_aspect("equal")
    a3.axhline(0, color="k", lw=1.5)
    a3.add_patch(Rectangle((0, TEKER_H), TABAN_DERIN, TABAN_T, fc="#6c757d", ec="k"))
    for y0 in (-KULAK_TASMA, TABAN_DERIN - KULAK_ICERI):
        a3.add_patch(Rectangle((y0, KULAK_Z0), KULAK_TASMA + KULAK_ICERI, KULAK_T, fc="#e8890c", ec="k", lw=0.5))
    for ya in (KULAK_AYAK[1], TABAN_DERIN - KULAK_AYAK[1]):
        a3.add_patch(Rectangle((ya - 30, 0), 60, 15, fc="#555"))
        a3.plot([ya, ya], [15, KULAK_Z0], color="#555", lw=2)
    # arkadaki mekanizma (soluk)
    a3.add_patch(Rectangle((Y_K0, RAY_ALT), KILAVUZ_H, RAY_UST - RAY_ALT, fc="#999", ec="none", alpha=0.35))
    a3.add_patch(Rectangle((SILINDIR_Y - PISTON_GOVDE_D / 2, TABAN_UST), PISTON_GOVDE_D, SILINDIR_UST - TABAN_UST,
                           fc="#cfd4dc", ec="#555", alpha=0.8))
    for zm, ls in ((MAKARA_Z0, "-"), (MAKARA_Z_MAX, "--")):
        a3.add_patch(Circle((SILINDIR_Y, zm), MAKARA_R, fc="none", ec="#c00", lw=1.1, ls=ls))
    a3.plot([ZINCIR_ON_Y, ZINCIR_ON_Y], [KANCA_Z0, MAKARA_Z0], color="#222", lw=1)
    a3.plot([ZINCIR_ARKA_Y, ZINCIR_ARKA_Y], [GERGI_UST, MAKARA_Z0], color="#222", lw=1)
    for i, z in enumerate(DURAKLAR):
        a3.add_patch(Rectangle((KABIN_ON_Y, z), KABIN_DERIN, KABIN_H, fc="#fff3c4" if i == 0 else "none",
                               ec="#b8860b", lw=1.0, ls="-" if i == 0 else "--", alpha=0.85 if i == 0 else 1))
    a3.add_patch(Rectangle((ASKI_UST_Y[0], z_aski_alt), KANAL_Y[1] - ASKI_UST_Y[0], z_aski_ust - z_aski_alt,
                           fc="#bbb", ec="#777", alpha=0.5, lw=0.6))
    a3.text(ASKI_UST_Y[0] + 5, z_aski_ust + 15, "askı", fontsize=7, color="#555")
    # dikmeler, köşe plakaları
    for y0 in (0, TABAN_DERIN - PROFIL_A):
        a3.add_patch(Rectangle((y0, AYAK_UST), PROFIL_A, DIKME_ALT_BOY, fc="#2a61b8", ec="k", lw=0.6))
        a3.add_patch(Rectangle((y0, BOLME_Z + KOSE_PL_T), PROFIL_A, DIKME_UST_BOY, fc="#5b8fdc", ec="k", lw=0.6))
        yp = 0 if y0 == 0 else TABAN_DERIN - KOSE_PL
        for z in kose_z.values():
            a3.add_patch(Rectangle((yp, z), KOSE_PL, KOSE_PL_T, fc="#10407f", ec="k", lw=0.4))
    # yan kuşaklar + çaprazlar
    for r in YUZ_KUSAKLARI["SOL"]:
        a3.add_patch(Rectangle((PROFIL_A, KUSAK[r]), KAFES_BOY_Y, KUSAK_H, fc="#3a7fd5", ec="#10407f", lw=0.5))
        a3.text(TABAN_DERIN + 8, KUSAK[r] + KUSAK_H / 2, f"{r}  {KUSAK[r]:.0f}", fontsize=7, va="center", color="#10407f")
    for c in capraz_bilgi:
        if c["yuz"] != "SOL":
            continue
        du, dz = c["u1"] - c["u0"], c["zb"] - c["za"]
        L = math.hypot(du, dz)
        nu, nz = -dz / L * CAPRAZ_A / 2, du / L * CAPRAZ_A / 2
        eu, ez = du / L * 60, dz / L * 60
        p0 = (c["u0"] - eu, c["za"] - ez)
        p1 = (c["u1"] + eu, c["zb"] + ez)
        band = Polygon([(p0[0] + nu, p0[1] + nz), (p1[0] + nu, p1[1] + nz), (p1[0] - nu, p1[1] - nz), (p0[0] - nu, p0[1] - nz)],
                       closed=True, fc="#73a7e8", ec="#10407f", lw=0.5)
        a3.add_patch(band)
        band.set_clip_path(Rectangle((PROFIL_A, c["za"]), KAFES_BOY_Y, c["zb"] - c["za"], transform=a3.transData))
        a3.text((c["u0"] + c["u1"]) / 2 + 25, (c["za"] + c["zb"]) / 2, f"{c['boy']:.0f}", fontsize=7, color="#10407f",
                rotation=math.degrees(math.atan2(dz, du)), ha="center", va="center",
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    a3.plot([-40, TABAN_DERIN + 40], [BOLME_Z, BOLME_Z], color="#d00000", lw=1.2, ls="--")
    a3.text(TABAN_DERIN / 2, BOLME_Z + 12, "bölme", ha="center", fontsize=7, color="#d00000")
    a3.text(0, -45, "ÖN", fontsize=9, fontweight="bold")
    a3.text(TABAN_DERIN, -45, "ARKA", fontsize=9, fontweight="bold", ha="right")
    a3.set_xlim(-KULAK_TASMA - 30, TABAN_DERIN + KULAK_TASMA + 120)
    a3.set_ylim(-60, Z_TEPE + 80)
    a3.set_title("YAN GÖRÜNÜŞ (sol) — kuşak + çapraz", fontsize=12, fontweight="bold")
    a3.tick_params(labelsize=7)
    a3.grid(alpha=0.12)

    fig.suptitle("Mini hidrolik asansör maketi — taban, kaynaklı kafes, kat kapıları  |  "
                 "TASLAK YERLEŞİM (kılavuz, silindir, tank ölçüleri gelince kesinleşir)",
                 fontsize=13, fontweight="bold", color="#222")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(CIKTI, "teknik_resim_TASLAK.png"), bbox_inches="tight")
    plt.close(fig)


ciz_teknik()


# --- Ek yeri: birleşik ve ayrılmış hâli (sol ön köşe, 1,75 m) ---
def acik_renk(r, oran=0.5):
    return tuple(c + (1 - c) * oran for c in r[:3]) + (r[3],)


def ek_yeri_gorseli():
    birlesik, ayrik = [], []
    for p in parcalar:
        if p["tur"] not in ("GERCEK", "BAGLANTI"):
            continue
        q = dict(p)
        if p["ad"].startswith(UST_ONEK):
            q["renk"] = acik_renk(p["renk"])            # üst modül açık renk
        birlesik.append(q)
        s = p["sekil"]
        if p["ad"].startswith("CIVATA_EK"):
            s = s.translate(Vector(0, 0, 300))             # cıvatalar sökülmüş
        elif p["ad"].startswith(UST_ONEK):
            s = s.translate(Vector(0, 0, 150))             # üst kafes kaldırılmış
        ayrik.append(dict(q, sekil=s))
    bolge = ((-20, 240), (-20, 240), (1620, 2140))
    fig = plt.figure(figsize=(16, 9), dpi=120)
    ax1 = fig.add_subplot(121, projection="3d")
    sahne(ax1, birlesik, bolge, 20, -48, "BİRLEŞİK\niki plaka üst üste, 3 cıvata + 2 pim", 10, kirp=True, zoom=1.1)
    ax2 = fig.add_subplot(122, projection="3d")
    sahne(ax2, ayrik, bolge, 20, -48, "AYRILMIŞ\n3 cıvata üstten sökülür, üst kafes dik kaldırılır", 10, kirp=True, zoom=1.1)
    fig.text(0.5, 0.06, "Koyu mavi: ALT kafes (alt plaka + kaynak somunları + pimler burada kalır)   |   "
             "Açık mavi: ÜST kafes (üst plaka)   |   Siyah: M10 cıvata   |   Mor: Ø10 pim",
             ha="center", fontsize=10)
    fig.text(0.5, 0.025, "Her köşede aynı: toplam 12 cıvata. Ayırmadan önce kabin en alta indirilir, "
             "U kılavuzların üst konsol cıvataları sökülür.", ha="center", fontsize=10, color="#b00020")
    fig.subplots_adjust(0, 0.1, 1, 0.95, wspace=0)
    fig.savefig(os.path.join(CIKTI, "onizleme_ek_yeri.png"))
    plt.close(fig)


ek_yeri_gorseli()


def kat_kapisi_gorseli():
    s = DURAKLAR[0]
    bolge = ((KASA_X[0] - 40, KILIT_X[1] + 40), (-70, 150), (s - 60, s + KAPI_NET_H + KASA_P + 50))
    fig = plt.figure(figsize=(16, 8.5), dpi=120)
    ax1 = fig.add_subplot(121, projection="3d")
    sahne(ax1, gorunur, bolge, 14, -62, "1. DURAK KAT KAPISI — DIŞARIDAN\nkasa, dar camlı kanat, kol, buton kutusu", 12,
          kirp=True, zoom=1.05)
    ax2 = fig.add_subplot(122, projection="3d")
    ic_liste = [p for p in gorunur if p["ad"] not in ("HAYALET_KABIN", "HAYALET_TASIYICI_KOL_2")]
    sahne(ax2, ic_liste, bolge, 16, 58, "KUYUNUN İÇİNDEN (kabin kutusu gizli) — kilit (sarı), kam, kabin kapısı\n"
          "kam durakta ileri çıkıp kilit makarasına basar, kilit açılır", 12, kirp=True, zoom=1.05)
    fig.text(0.5, 0.03, "Kabin durakta değilken kilit kapalıdır; kapı açıkken ya da kilitli değilken emniyet devresi "
             "motoru ve iniş valfini keser (Arduino'dan bağımsız).", ha="center", fontsize=10, color="#b00020")
    fig.subplots_adjust(0, 0.07, 1, 0.93, wspace=0)
    fig.savefig(os.path.join(CIKTI, "onizleme_kat_kapisi.png"))
    plt.close(fig)


kat_kapisi_gorseli()


def unite_gorseli():
    bolge = ((KUYU_EN - 120, TABAN_EN + 30), (-20, 520), (TABAN_UST - 10, PANO_Z0 + hid.PANO_Z + 30))
    fig = plt.figure(figsize=(16, 9), dpi=120)
    ax1 = fig.add_subplot(121, projection="3d")
    sahne(ax1, gorunur, bolge, 16, -40, "GÜÇ ÜNİTESİ + PANO — önden\nIEC 71 motor 0,25 kW, valf bloğu, manometre, pano (invertör)",
          14, kirp=True, zoom=1.05)
    ax2 = fig.add_subplot(122, projection="3d")
    sahne(ax2, gorunur, bolge, 22, -130, "ARKADAN / KUYU TARAFINDAN\nbasınç hortumu kuyuya R1 altından girer, kablolar panodan",
          14, kirp=True, zoom=1.05)
    fig.text(0.5, 0.03, f"Hortum 1/4\" 2SN, boy ≈ {HORTUM_BOY / 1000:.2f} m (valf bloğundan silindir girişine) | ".replace("0.", "0,") +
             "Çıkış ve iniş invertörle; inişte pompa geri döner, enerji fren direncinde yanar", ha="center", fontsize=10)
    fig.subplots_adjust(0, 0.07, 1, 0.93, wspace=0)
    fig.savefig(os.path.join(CIKTI, "onizleme_unite.png"))
    plt.close(fig)


unite_gorseli()

yaz("\n[9] ÇIKTILAR")
for f in sorted(os.listdir(CIKTI)):
    yaz(f"  {f}  ({os.path.getsize(os.path.join(CIKTI, f)) / 1024:.0f} KB)")
with open(os.path.join(CIKTI, "kontrol_raporu.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rapor))
