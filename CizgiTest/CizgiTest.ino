// CizgiTest - HW-870 (TCRT5000) cizgi sensorunu test eder.
// Tek sensor. Pil gerekmez, USB yeter.
//
// Baglanti:  VCC->5V   GND->GND   DO->A0   AO->A1
//
// Sensoru zemine 5-10 mm mesafede tut. Uzakta hicbir sey goremez.
// Not: pin 2 ve 4'e (mesafe sensoru) bu kod HIC DOKUNMAZ.

const int DO_PIN = A0;   // sensorun kendi karari (var/yok)
const int AO_PIN = A1;   // ham olcum (0-1023)

unsigned long olcumNo = 0;

void setup() {
  pinMode(DO_PIN, INPUT);
  // AO_PIN analog okunacak, pinMode gerekmez

  Serial.begin(9600);
  delay(300);
  Serial.println("==========================================");
  Serial.println("  CIZGI SENSORU TESTI (HW-870)");
  Serial.println("==========================================");
  Serial.println("Sensoru zemine 5-10 mm yaklastir.");
  Serial.println();
  Serial.println("SUNU YAP:");
  Serial.println("  1) Once BEYAZ bir kagit uzerinde tut, sayilari oku");
  Serial.println("  2) Sonra SIYAH bant uzerinde tut, sayilari oku");
  Serial.println("  3) Iki durumun sayilarini bana soyle");
  Serial.println("------------------------------------------");
  delay(1500);
}

void loop() {
  olcumNo++;

  int ham = analogRead(AO_PIN);       // 0 - 1023 arasi
  int karar = digitalRead(DO_PIN);    // 0 veya 1

  Serial.print(olcumNo);
  Serial.print(" | HAM: ");
  if (ham < 1000) Serial.print(" ");
  if (ham < 100)  Serial.print(" ");
  if (ham < 10)   Serial.print(" ");
  Serial.print(ham);

  Serial.print("  | KARAR: ");
  Serial.print(karar);
  Serial.print(karar == 0 ? " (DUSUK)" : " (YUKSEK)");

  // Ham degeri gozle takip etmek icin cubuk
  Serial.print("  ");
  int cubuk = ham / 25;              // 1023 / 25 = ~40 cubuk
  for (int i = 0; i < cubuk; i++) Serial.print('#');

  Serial.println();
  delay(400);
}
