# FARUK'UN ARABASI - KABLO HARITASI  (v2, duzeltilmis)
23 Eylul 2026

## !!! KABLO TAKMADAN ONCE YAPILACAKLAR !!!

1. [TAMAM - 23 Eylul 2026] ENA/ENB jumper kapaklari CIKARILDI.
   Kart modeli: HW-095 (standart kirmizi L298N).
   Kapaklarin altindan cikan 2'ser pimden:
     - +5V klemensiyle SUREKLILIK VEREN (oten) pim  = +5V   -> kablo TAKMA
     - SUREKLILIK VERMEYEN (otmeyen) pim            = ENA / ENB -> KABLO BURAYA
   Kullanicinin elindeki duruma gore: OTMEYEN = ALTTAKI pim.
   Kablo takarken bu olcum 10 saniyede TEKRARLANACAK (kart cevrilirse ust/alt degisir).
2. "5V" jumper'i (kartin orta-sol kisminda, 102 yazan parcanin yaninda)
   YERINDE KALACAK. Cikarilirsa motorlar hic donmez.
3. Sokmeden once FOTOGRAF cek ve her kabloyu BANTLA ETIKETLE.
4. Her takma/sokme isleminde: kirmizi anahtar KAPALI + USB CIKIK.

## ARDUINO PIN HARITASI

### Motor surucu (L298N) - 6 kablo, ARDISIK
| L298N ustundeki yazi | Arduino deligi | Ne ise yarar    |
|----------------------|----------------|-----------------|
| ENA                  | 11             | Sol motor HIZ   |
| IN1                  | 10             | Sol motor YON   |
| IN2                  | 9              | Sol motor YON   |
| IN3                  | 8              | Sag motor YON   |
| IN4                  | 7              | Sag motor YON   |
| ENB                  | 6              | Sag motor HIZ   |

11-10-9-8-7-6 sirayla iniyor. Serit kablo duz gider.

NEDEN 10 ve 9 DEGIL de 11 ve 6?  Servo motor kullanilirsa Arduino'nun
ic sayaci 9 ve 10'un hiz ayarini KAPATIYOR. O zaman motorlar yavas
gitmek yerine TAM GAZ kalkar. 11 ve 6 bundan etkilenmiyor.

### Mesafe sensoru (HC-SR04) - 4 kablo
| Sensor ustundeki yazi | Arduino deligi |
|-----------------------|----------------|
| VCC                   | 5V             |
| Trig                  | 4              |
| Echo                  | 2              |
| GND                   | GND            |

### Cizgi sensorleri (HW-870) - EN SON ASAMA
| Sensor | VCC | GND | DO  |
|--------|-----|-----|-----|
| Sol    | 5V  | GND | A0  |
| Sag    | 5V  | GND | A1  |

## GUC BAGLANTISI

### Test asamasinda (tekerlekler havada)
- Arduino: USB'den beslenir
- Pil (+) -> SIGORTA (2-3 A) -> L298N "+12V" klemensi
- Pil (-) -> L298N "GND" klemensi
- L298N "GND" -> Arduino "GND"      <-- ILK BAGLANAN, SON SOKULEN
- L298N "+5V" -> HICBIR SEY

### Araba yerde giderken (USB cikik)
- Pil (+) -> SIGORTA -> hem L298N "+12V" hem Arduino "VIN"
- Pil (-) -> L298N "GND" ve Arduino "GND"

## MUTLAK KURALLAR
- Arduino "5V" pini ile L298N "+5V" klemensi ASLA BIRLESTIRILMEZ.
  (Arduino "VIN" pinine pil gerilimi vermek ise SERBEST ve dogru.)
- Pil (+) hattinda SIGORTA olmadan pil takilmaz.
- Motor hizi kodda en fazla 200 (255 degil). Ilk testler 120-150.
- Kirmizi = arti, Siyah = eksi. Istisnasiz.

## MOTORLAR
- Sol motorun 2 kablosu  -> OUT1 / OUT2
- Sag motorun 2 kablosu  -> OUT3 / OUT4
- Kutup yonu onemsiz; ters donerse duzeltiriz

## PIN YETMEZLIGI - EK MALZEME GEREKLI
Arduino'da 1 tane 5V deligi, 3 tane GND deligi var.
Ihtiyac: 5V'a 3 cihaz, GND'ye 4 cihaz. SIGMIYOR.
=> Breadboard (deneme tahtasi) veya vidali dagitim klemensi gerekli.

## BOSTA KALAN PINLER
D3, D5, D12, D13(dahili LED), A2, A3, A4, A5
D0 ve D1 KULLANILMAZ - seri port oradan konusuyor
Servo gerekirse -> D3 veya D12
