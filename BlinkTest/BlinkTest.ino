// BlinkTest - kartin calistigini dogrulayan test
// DESEN: 3 hizli cakma + 1.2 saniye mola. (Fabrika cikisi yavas
// yanip sonmeden kolayca ayirt edilsin diye boyle secildi.)

const int LED = LED_BUILTIN;   // kartin uzerindeki dahili isik
unsigned long tur = 0;         // kacinci tur

void setup() {
  pinMode(LED, OUTPUT);
  Serial.begin(9600);
  delay(300);
  Serial.println("=== BlinkTest basladi (3 cakma + mola) ===");
}

void loop() {
  tur++;
  Serial.print("Tur ");
  Serial.print(tur);
  Serial.println(" - 3 cakma");

  for (int i = 1; i <= 3; i++) {
    digitalWrite(LED, HIGH);
    delay(150);
    digitalWrite(LED, LOW);
    delay(150);
  }

  Serial.print("Tur ");
  Serial.print(tur);
  Serial.println(" - mola");
  delay(1200);
}
