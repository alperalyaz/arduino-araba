# KAYRA — YAPILACAKLAR

## 0. Değişmez kurallar

- Kablo takarken/sökerken: **USB çıkık, pil bağlı değil.**
- Test sırasında araba **kitabın üstünde**, tekerlekler havada.
- Kırmızı = artı. Siyah = eksi.
- Duman, koku veya ısınma → pili çıkar, USB'yi çek.

## 1. Kabloları bağla

Önce ortak şase:

```
L298N "GND" klemensi  →  Arduino GND
```

Sonra altı komut kablosu:

| L298N | Arduino |
|---|---|
| ENA | 11 |
| IN1 | 10 |
| IN2 | 9  |
| IN3 | 8  |
| IN4 | 7  |
| ENB | 6  |

ENA ve ENB'de iki pim var. Multimetreyi süreklilik kademesine al.
Bir probu L298N "+5V" klemensine koy. Ötmeyen pime kabloyu tak.

Sonra motorlar:

```
Sol motor  →  OUT1 / OUT2
Sağ motor  →  OUT3 / OUT4
```

Mesafe sensörü zaten bağlı. Dokunma. (Trig→4, Echo→2, Vcc→5V, Gnd→GND)

## 2. Pili henüz bağlama

## 3. USB'yi tak, kodu yükle

```bash
"C:\Program Files\Arduino CLI\arduino-cli.exe" compile --fqbn arduino:avr:uno --upload -p COM3 C:\ardiuno\MotorTest
```

## 4. Ekranı oku

Motorlar dönmeyecek (pil yok). Ekranda şu akmalı:

```
-> SOL motor - ILERI
-> SOL motor - GERI
-> SAG motor - ILERI
-> SAG motor - GERI
-> IKISI BIRDEN - ILERI
```

Akmıyorsa dur. Kabloyu kontrol et.

## 5. Pili bağla

```
Pil (+)  →  L298N "+12V"
Pil (-)  →  L298N "GND"
```

L298N "+5V" klemensine hiçbir şey bağlama.

## 6. İzle

- Ekranda "SOL" yazarken sol teker dönüyor mu?
- "ILERI" yazarken ileri yönde mi dönüyor?
- Ters dönen varsa **kabloyu değiştirme**, not al. Kodda düzeltilecek.

## 7. Raporla

Şunları yaz:
- Hangi motor, hangi komutta, hangi yöne döndü
- Dönmeyen motor var mı
- Isınan parça var mı

## Sorun çıkarsa

| Belirti | Bak |
|---|---|
| Hiçbir motor dönmüyor | L298N "5V" jumper'ı takılı mı |
| Ekranda yazı yok | USB kablosu, COM3 |
| Tek motor dönmüyor | O motorun OUT klemens vidaları sıkı mı |
| Hız ayarı çalışmıyor, hep tam gaz | ENA/ENB kapakları çıkmış mı |
