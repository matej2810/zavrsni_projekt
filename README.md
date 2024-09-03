# Završni projekt studenata treće godine prijediplomskog studija Matematika i računarstvo na Fakultetu primijenjene matematike i informatike u Osijeku (Matej Jurec i Hrvoje Stranput)

## **Opis projekta: Pametna teretana s primjenom IoT tehnologija**

### **Uvod**

Projekt "Pametna teretana" razvijen je s ciljem modernizacije upravljanja teretanom pomoću IoT tehnologija. Projekt se sastoji od dva glavna modula: upravljanje korisnicima i praćenje pristupa teretani putem RFID kartica. Sustav koristi kombinaciju hardverskih komponenti (Raspberry Pi, Arduino Wemos D1) i softverskih komponenti (Python, Flask, MySQL) kako bi omogućio siguran i efikasan rad teretane.

### **1. Modul za upravljanje korisnicima i teretanom (Raspberry Pi)**

#### **Hardver**
- **Raspberry Pi:** Središnji uređaj sustava, na kojem se izvršava GUI aplikacija za upravljanje korisnicima i teretanom.
- **Ekran osjetljiv na dodir:** Koristi se za interakciju s grafičkim korisničkim sučeljem (GUI).
- **RFID čitač (MFRC522):** Služi za očitavanje RFID kartica prilikom dodavanja korisnika u bazu podataka

#### **Softver**
- **Operativni sustav:** Raspberry Pi OS.
- **Programski jezik:** Python.
- **Tkinter:** Za izradu grafičkog korisničkog sučelja.
- **Pymysql:** Za interakciju s MySQL bazom podataka.
- **mfrc522:** Knjižnica za rad s RFID čitačem.
- **Threading:** Omogućuje kontinuirano očitavanje RFID kartica bez blokiranja GUI-a.

#### **Opis funkcionalnosti**

1. **Inicijalizacija sustava:**  
   Raspberry Pi inicijalizira potrebne komponente i pokreće GUI aplikaciju koja omogućava upravljanje korisnicima. Aplikacija se povezuje s MySQL bazom podataka gdje se pohranjuju podaci o korisnicima teretane.

2. **Prijava korisnika:**  
   Operateri (admin) se prijavljuju u sustav pomoću korisničkog imena i lozinke. Aplikacija provjerava vjerodajnice u bazi podataka i omogućava pristup ako su vjerodajnice točne.
```python
def login(username, password):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    if result:
        return True
    return False
```

3. **Dodavanje članova:**  
   Operater može dodati nove članove unosom imena, skeniranjem RFID kartice i odabirom uloge (član ili osoblje). Informacije se pohranjuju u bazu podataka.
```python
def add_member(name, role):
    id, text = reader.read()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO members (name, role, rfid) VALUES (%s, %s, %s)", (name, role, id))
    connection.commit()
```

4. **Kontinuirano očitavanje RFID kartica:**  
   RFID čitač neprestano sluša dolazne kartice. Kada se kartica skenira, ID kartice automatski se popunjava u odgovarajuće polje u aplikaciji.

```python
def read_rfid():
    while True:
        id, text = reader.read()
        # Ažuriraj GUI s očitanim ID-om
        update_gui_with_rfid(id)
threading.Thread(target=read_r
```

5. **Upravljanje korisnicima:**  
   Operater može pregledavati popis svih članova, resetirati broj njihovih ulazaka ili uklanjati članove iz sustava.
```python
def manage_members():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    # Prikaz članova u GUI aplikaciji
    display_members_in_gui(members)
```

6. **Odjava:**  
   Operateri se mogu odjaviti iz sustava, što ih vraća na ekran za prijavu.

### **2. Modul za praćenje ulaska i izlaska korisnika (Arduino Wemos D1)**

#### **Hardver**
- **Arduino Wemos D1 (ESP8266):** Mikrokontroler koji služi za bežičnu komunikaciju i upravljanje RFID čitačem.
- **RFID čitač:** Očitava RFID kartice korisnika pri ulasku u teretanu.
- **LED lampice:**  
  - **Crvena:** Kada korisnik nema pristup (kartica nije u bazi podataka, korisnik premašio maksimalni broj dnevnih ulazaka).
  - **Zelena:** Korisnik ima pristup.

#### **Softver**
- **Programski jezik:** Arduino IDE
- **ESP8266WiFi:** Omogućava povezivanje mikrokontrolera na Wi-Fi mrežu.

#### **Opis funkcionalnosti**

1. **Povezivanje na Wi-Fi:**  
   Mikrokontroler se povezuje na lokalnu Wi-Fi mrežu pomoću zadanog SSID-a i lozinke.  
   *(Pokušali smo napraviti da se spaja na hotspot od Raspberryja što smo i uspjeli, ali je nemoguće napraviti da Flask server bude u toj novoj mreži odnosno hotspotu. Kada bi se napravio hotspot da samo proširi mrežu, onda je veliki upitnik hoće li to funkcionirati na faksu. Zato je napravljeno univerzalno rješenje koje radi apsolutno svuda - Raspberry i Arduino spojeni su na hotspot od mobitela te sva međusobna komunikacija radi odlično na taj način.)*
```cpp
#include <ESP8266WiFi.h>

const char* ssid = "your_SSID";
const char* password = "your_PASSWORD";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
}
```

2. **Komunikacija sa serverom:**  
   Kada se RFID kartica očita, mikrokontroler šalje HTTP zahtjev serveru (Flask serveru na Raspberry Pi-u) kako bi provjerio može li korisnik ući u teretanu, te ovisno o odgovoru sa servera pali zelenu ili crvenu LED lampicu.
```cpp
void checkAccess(String rfid) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("http://your_raspberry_ip:5000/check_access?rfid=" + rfid);
    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println(payload);
      if (payload == "allowed") {
        digitalWrite(GREEN_LED, HIGH);
        digitalWrite(RED_LED, LOW);
      } else {
        digitalWrite(GREEN_LED, LOW);
        digitalWrite(RED_LED, HIGH);
      }
    }

    http.end();
  }
}
```

### **3. Server za provjeru RFID kartica (Flask aplikacija)**

#### **Softver**
- **Flask:** Python web framework
- **Pymysql (MariaDB):** Koristi se za povezivanje s MySQL bazom podataka.

#### **Opis funkcionalnosti**

1. **Inicijalizacija aplikacije:**  
   Flask aplikacija pokreće se na Raspberry Pi-u, a server sluša dolazne zahtjeve na specifičnoj IP adresi i portu.
```python
from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

def init_db():
    return pymysql.connect(host='localhost',
                           user='user',
                           password='password',
                           database='gym_db')
db = init_db()
```
2. **Provjera RFID kartica:**  
   Kada Wemos D1 pošalje UID RFID kartice, Flask aplikacija provjerava bazu podataka kako bi utvrdila status korisnika.  
   - **Ako je korisnik član:** Provjerava se broj ulazaka:
     - Ako broj ulazaka nije premašio dnevni limit (3 ulaza), sustav ažurira broj ulazaka i dozvoljava ulaz.
     - Ako je korisnik član osoblja, ulaz je uvijek dozvoljen.
   - **Ako uvjeti nisu zadovoljeni:** Pristup se odbija.

3. **Slanje odgovora:**  
   Flask aplikacija vraća JSON odgovor mikrokontroleru koji zatim kontrolira crvene i zelene LED lampice i pali ih ovisno o odgovoru.
```python
@app.route('/check_access', methods=['GET'])
def check_access():
    rfid = request.args.get('rfid')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members WHERE rfid=%s", (rfid,))
    member = cursor.fetchone()

    if member:
        # Provjera broja ulazaka
        if member['role'] == 'staff' or member['entries'] < 3:
            cursor.execute("UPDATE members SET entries = entries + 1 WHERE rfid=%s", (rfid,))
            db.commit()
            return jsonify({"status": "allowed"})
        else:
            return jsonify({"status": "denied"})
    return jsonify({"status": "denied"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```
### **Zaključak**

Nakon puno truda kako bi se sve komponente spojile i međusobno radile u skladu, nastao je ovaj projekt. Projekt pruža puno mogućnosti raznih proširenja, npr. spajanja na motor koji onda otvara prava vrata ili na relej. GUI aplikacija je jako lagana i intuitivna za korištenje, ali mogu se dodati i još neke napredne stvari koje nisu bile u opisu našeg projekta, a to je praćenje je li korisnik platio mjesečnu članarinu, ili npr. kada se unese novi korisnik da se on zadrži u bazi podataka idućih mjesec dana, a zatim se gleda je li produžio članstvo te u odnosu na to ostaje ili se miče iz baze. Mogućnosti su razne, ali ovaj projekt je zagrebao površinu beskonačnih mogućnosti IoT tehnologije koja svakim danom sve više napreduje.

**Izradili:** Matej Jurec i Hrvoje Stranput  
**Mentor:** Dr. sc. Juraj Benić, mag.ing.

**Osijek, 2024.**
