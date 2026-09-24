# Faruk'un Arduino Arabası

Yıllar önce bir robotik kodlama setiyle yapılmış "çarpmayan araba" projesinin
yeniden canlandırılması. Orijinal kod kayıp (karttan geri alınamıyor), her şey sıfırdan yazılıyor.

## Donanım

| Parça | Model | Durum |
|---|---|---|
| Kart | Arduino Uno R3 klonu (EDUBOTICS), CH340 USB | ✅ Çalışıyor |
| Motor sürücü | L298N, **HW-095** | ✅ Hazır, jumper'ları ayarlandı |
| Mesafe sensörü | HC-SR04 (çok modlu klon, fabrika modu standart) | ✅ Çalışıyor, test edildi |
| Motorlar | 2× sarı TT redüktörlü, tekerlekli | ⏳ Test edilmedi |
| Çizgi sensörü | 2× HW-870 (TCRT5000), 4 pinli | ⏳ Bağlanmadı |
| Pil | 2× 18650, yeni, tam şarjlı | ✅ Hazır |
| Gövde | Lazer kesim ahşap, marka NCT, ön bilyeli teker | — |

**Port:** COM3 &nbsp;•&nbsp; **FQBN:** `arduino:avr:uno` &nbsp;•&nbsp; "old bootloader" gerekmiyor

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| [KABLO-HARITASI.md](KABLO-HARITASI.md) | **Ana referans.** Hangi kablo nereye. |
| [KAYRA.md](KAYRA.md) | Uygulayacak kişi için adım adım talimat |
| `BlinkTest/` | Kart canlı mı — en temel test |
| `MesafeTest/` | HC-SR04 ölçüm testi (pil gerekmez) |
| `MotorTest/` | Motorları tek tek döndürür (pil gerekir) |
| `CizgiTest/` | HW-870 testi (henüz kullanılmadı) |
| `ardiuno-claude.cmd` | Masaüstü kısayolunun çalıştırdığı dosya |

## Komutlar

Derle ve yükle:

```bash
"C:\Program Files\Arduino CLI\arduino-cli.exe" compile --fqbn arduino:avr:uno --upload -p COM3 C:\ardiuno\MesafeTest
```

Kart bağlı mı:

```bash
"C:\Program Files\Arduino CLI\arduino-cli.exe" board list
```

**Seri port okuma:** `arduino-cli monitor` kullanma — interaktif, oturumu kilitler.
Bunun yerine PowerShell `System.IO.Ports.SerialPort` + `ReadExisting()` döngüsü kullan,
`finally` içinde mutlaka `Close()`/`Dispose()`.

## Bilinen tuzaklar

- **L298N'in ENA/ENB jumper kapakları** çıkarılmış olmalı. Takılıyken Arduino pini bağlanırsa pin yanar.
- **"5V" jumper'ı takılı kalmalı.** Çıkarılırsa motorlar hiç dönmez.
- **Arduino 5V pini ile L298N +5V klemensi asla birleştirilmez.** (Arduino VIN'e pil gerilimi vermek serbest.)
- **Servo kullanılırsa** Timer1'i alır, D9 ve D10'un hız ayarı ölür. ENA/ENB bu yüzden D11 ve D6'da.
- **D0 ve D1 kullanılmaz** — seri port oradan konuşuyor.
- **Blink testinde 1 saniyelik desen kullanma** — fabrika çıkışı deseniyle aynı, sahte başarı üretir.
- Arduino'da **1 adet 5V, 3 adet GND** deliği var. Üç sensör birden bağlanacaksa
  **breadboard veya sensör shield** gerekli.

## Sıradaki

1. Motor testi (kablolama + pil) — `MotorTest/`
2. Çarpmayan araba (mesafe + motor birlikte)
3. Çizgi takibi (shield/breadboard geldikten sonra)
