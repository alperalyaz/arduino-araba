// MesafeTest - HC-SR04 mesafe sensorunu tek basina test eder.
// Motorlar CALISMAZ. Tekerlekler donmez. Sadece olcum yapar.
// Karti USB'den beslemek yeterli, pil gerekmez.

// ##################################################################
// ###  BURAYI DEGISTIRECEGIZ - sensorun kablolari hangi           ###
// ###  numarali deliklere takiliysa o numaralari yaz.             ###
// ##################################################################
const int TRIG = 4;    // sensorun Trig (tetik) bacagi
const int ECHO = 2;    // sensorun Echo (yanki) bacagi
// ##################################################################

unsigned long olcumNo = 0;
int cevapsiz = 0;      // ust uste kac olcumde cevap gelmedi

void setup() {
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  digitalWrite(TRIG, LOW);

  Serial.begin(9600);
  delay(300);
  Serial.println("=== Mesafe testi basladi ===");
  Serial.print("Trig pini: ");  Serial.print(TRIG);
  Serial.print(" | Echo pini: "); Serial.println(ECHO);
  Serial.println("Elini sensorun onunde gezdir, sayi degismeli.");
  Serial.println("----------------------------------------");
}

void loop() {
  olcumNo++;

  // 1) Sensore "olc" komutu: 10 mikrosaniyelik kisa bir durtme
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // 2) Yankinin donmesini bekle. 30 ms icinde donmezse pes et.
  //    (30 ms ~ 5 metre. Daha uzagi bu sensor zaten goremez.)
  unsigned long sure = pulseIn(ECHO, HIGH, 30000UL);

  Serial.print(olcumNo);
  Serial.print(" -> ");

  if (sure == 0) {
    // Hic yanki gelmedi
    cevapsiz++;
    Serial.print("CEVAP YOK");
    if (cevapsiz == 5) {
      Serial.print("   <<< 5 kez ust uste cevap yok.");
      Serial.print(" Ya pin numaralari yanlis, ya sensorun onu tamamen acik,");
      Serial.print(" ya da kablo gevsek.");
    }
    Serial.println();
  } else {
    cevapsiz = 0;
    // Ses saniyede ~343 metre gider. Giden+donen yol oldugu icin ikiye bolunur.
    // Kisayol: mikrosaniye / 58 = santimetre
    float cm = sure / 58.0;

    Serial.print(cm, 1);
    Serial.print(" cm");
    Serial.print("   (ham sure: ");
    Serial.print(sure);
    Serial.print(" mikrosaniye)");

    // Gozle takip kolay olsun diye kaba bir cubuk grafik
    Serial.print("  ");
    int cubuk = (int)(cm / 2);
    if (cubuk > 40) cubuk = 40;
    for (int i = 0; i < cubuk; i++) Serial.print('#');

    Serial.println();
  }

  delay(300);   // saniyede ~3 olcum
}
