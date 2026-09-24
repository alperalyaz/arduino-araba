// MotorTest - motorlari TEK TEK, DUSUK HIZDA, kisa sure calistirir.
//
// !!! TEKERLEKLER HAVADA OLACAK !!!
// Arabayi bir kitabin ya da kutunun ustune koy, tekerlekler bosta donsun.
// Yere koyma - kacar.
//
// Mesafe sensoru bu kodda KULLANILMIYOR. Sadece motorlar.

// --- L298N baglantilari (KABLO-HARITASI.md ile ayni) ---
const int ENA = 11;   // sol motor hiz
const int IN1 = 10;   // sol motor yon
const int IN2 = 9;    // sol motor yon
const int IN3 = 8;    // sag motor yon
const int IN4 = 7;    // sag motor yon
const int ENB = 6;    // sag motor hiz

// --- Guvenlik sinirlari ---
const int HIZ      = 140;   // 0-255 arasi. 140 = yaklasik yarim gaz.
const int MAX_HIZ  = 200;   // Bunun ustune ASLA cikilmayacak.
const int SURE     = 1500;  // her hareket 1.5 saniye
const int MOLA     = 1000;  // hareketler arasi 1 saniye duraklama

void setup() {
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT); pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  hepsiniDurdur();

  Serial.begin(9600);
  delay(300);
  Serial.println("=====================================");
  Serial.println("  MOTOR TESTI");
  Serial.println("  TEKERLEKLER HAVADA OLMALI!");
  Serial.println("=====================================");
  Serial.print("Hiz ayari: "); Serial.print(HIZ);
  Serial.print(" / 255  (guvenlik tavani: "); Serial.print(MAX_HIZ); Serial.println(")");
  Serial.println();
  Serial.println("5 saniye sonra basliyor...");
  for (int i = 5; i >= 1; i--) { Serial.print(i); Serial.println("..."); delay(1000); }
}

void loop() {
  adim("SOL motor - ILERI");
  solMotor(HIZ, true);   delay(SURE);  hepsiniDurdur(); delay(MOLA);

  adim("SOL motor - GERI");
  solMotor(HIZ, false);  delay(SURE);  hepsiniDurdur(); delay(MOLA);

  adim("SAG motor - ILERI");
  sagMotor(HIZ, true);   delay(SURE);  hepsiniDurdur(); delay(MOLA);

  adim("SAG motor - GERI");
  sagMotor(HIZ, false);  delay(SURE);  hepsiniDurdur(); delay(MOLA);

  adim("IKISI BIRDEN - ILERI");
  solMotor(HIZ, true); sagMotor(HIZ, true);
  delay(SURE);  hepsiniDurdur(); delay(MOLA);

  Serial.println();
  Serial.println(">>> Tur bitti. 5 saniye mola. <<<");
  Serial.println("Bir sey ters gittiyse USB'yi cek ya da anahtari kapat.");
  Serial.println();
  delay(5000);
}

// ---------- yardimci fonksiyonlar ----------

void adim(const char* mesaj) {
  Serial.print("-> ");
  Serial.println(mesaj);
}

int guvenliHiz(int h) {
  if (h > MAX_HIZ) return MAX_HIZ;   // tavani asamaz
  if (h < 0)       return 0;
  return h;
}

void solMotor(int hiz, bool ileri) {
  digitalWrite(IN1, ileri ? HIGH : LOW);
  digitalWrite(IN2, ileri ? LOW  : HIGH);
  analogWrite(ENA, guvenliHiz(hiz));
}

void sagMotor(int hiz, bool ileri) {
  digitalWrite(IN3, ileri ? HIGH : LOW);
  digitalWrite(IN4, ileri ? LOW  : HIGH);
  analogWrite(ENB, guvenliHiz(hiz));
}

void hepsiniDurdur() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}
