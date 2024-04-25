int led = 13; // LED pin
int sensor = 3; // sensor pin
int val; // numeric variable
volatile int pulseCount = 0; // This variable will increase by one every time a pulse from the sensor is detected
volatile int pulseCountInternal = 0; // This variable will increase by one every time a pulse from the sensor is detected
int rpm = 0; // Display of RPMs
float velocity = 0.00; // Velocity in km/h
float distance = 0.00; // Distance in km since board was last reset.
int countFlag = LOW;

unsigned long lastTime; // Last time update

void setup()
{
  pinMode(led, OUTPUT); // set LED pin as output
  pinMode(sensor, INPUT); // set sensor pin as input
  Serial.begin(9600);
  lastTime = millis(); // Initialize the lastTime variable
}

void loop()
{
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command == "reset") {
      distance = 0.00; // Reset distance counter
      Serial.println("Distance counter reset.");
    }
  }

  int pulseCount = countRotations();
  
  if (millis() - lastTime >= 5000) { // Update every five seconds
    rpm = (pulseCount * 12); // Calculate RPM (assumes one pulse per revolution)
    velocity = (pulseCount * 13.5 * 3600 / 5 / 100 / 1000); // Calculate velocity 
    distance += (pulseCount * 13.5 / 100 / 1000); // Calculate distance
    
    printDisplay(); // Print the statistics out
    pulseCountInternal = 0; // Reset pulse counter
    lastTime = millis(); // Update lastTime
  }
}

int countRotations() {
  val = digitalRead(sensor); // Read the sensor
  if(val == LOW && countFlag == HIGH) // when magnetic field is detected, turn led on
  {
    digitalWrite(led, HIGH);
    pulseCountInternal++;
    countFlag = LOW;
  }
  if(val == HIGH) {
    countFlag = HIGH;
    digitalWrite(led, LOW);
  }

  return pulseCountInternal;
}

void printDisplay() {
  Serial.print("{\"rpm\": ");
  Serial.print(rpm);
  
  // Print velocity
  Serial.print(", \"velocity\": ");
  Serial.print(velocity, 2);

  // Print distance
  Serial.print(", \"distance\": ");
  Serial.print(distance, 2);
  Serial.println("}");
}
