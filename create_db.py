import sqlite3

conn = sqlite3.connect('BilingualTrainer.db')
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS Word_Image (
  id INTEGER PRIMARY KEY,
  english_word TEXT NOT NULL,
  image_file TEXT NOT NULL
);
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Translation (
  id INTEGER PRIMARY KEY,
  word_id INTEGER NOT NULL,
  language_code TEXT NOT NULL,
  translated_word TEXT NOT NULL,
  FOREIGN KEY (word_id) REFERENCES Word_Image(id)
);
''')

# Sample rows - all available images from image-library folder
cur.executemany('INSERT INTO Word_Image (english_word, image_file) VALUES (?, ?)', [
    ("banana", "banana_0.png"),
    ("bird", "bird.png"),
    ("bread", "bread.png"),
    ("bunny", "bunny_0.png"),
    ("carrot", "carrot.png"),
    ("cat", "cat_0.png"),
    ("computer", "computer.png"),
    ("dog", "dog_0.png"),
    ("duck", "duck.jpg"),
    ("egg", "egg.png"),
    ("elephant", "elephant.jpg"),
    ("fish", "fish.png"),
    ("frog", "frog.jpg"),
    ("grapes", "grapes.jpg"),
    ("horse", "horse.jpg"),
    ("lion", "lion.jpg"),
    ("milk", "milk.png"),
    ("orange", "orange.jpg"),
    ("paper", "paper.png"),
    ("phone", "phone.png"),
    ("pizza", "pizza.png"),
    ("slide", "slide.png"),
    ("strawberry", "strawberry.jpg"),
    ("swing", "swing.png"),
    ("watermelon", "watermelon.jpg")
])

# Sample translations - Spanish (es), French (fr), and Vietnamese (vi)
cur.executemany('INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)', [
    (1, "es", "plátano"),
    (1, "fr", "banane"),
    (1, "vi", "chuối"),
    (2, "es", "pájaro"),
    (2, "fr", "oiseau"),
    (2, "vi", "chim"),
    (3, "es", "pan"),
    (3, "fr", "pain"),
    (3, "vi", "bánh mì"),
    (4, "es", "conejo"),
    (4, "fr", "lapin"),
    (4, "vi", "thỏ"),
    (5, "es", "zanahoria"),
    (5, "fr", "carotte"),
    (5, "vi", "cà rốt"),
    (6, "es", "gato"),
    (6, "fr", "chat"),
    (6, "vi", "mèo"),
    (7, "es", "computadora"),
    (7, "fr", "ordinateur"),
    (7, "vi", "máy tính"),
    (8, "es", "perro"),
    (8, "fr", "chien"),
    (8, "vi", "chó"),
    (9, "es", "pato"),
    (9, "fr", "canard"),
    (9, "vi", "vịt"),
    (10, "es", "huevo"),
    (10, "fr", "œuf"),
    (10, "vi", "trứng"),
    (11, "es", "elefante"),
    (11, "fr", "éléphant"),
    (11, "vi", "voi"),
    (12, "es", "pez"),
    (12, "fr", "poisson"),
    (12, "vi", "cá"),
    (13, "es", "rana"),
    (13, "fr", "grenouille"),
    (13, "vi", "ếch"),
    (14, "es", "uvas"),
    (14, "fr", "raisins"),
    (14, "vi", "nho"),
    (15, "es", "caballo"),
    (15, "fr", "cheval"),
    (15, "vi", "ngựa"),
    (16, "es", "león"),
    (16, "fr", "lion"),
    (16, "vi", "sư tử"),
    (17, "es", "leche"),
    (17, "fr", "lait"),
    (17, "vi", "sữa"),
    (18, "es", "naranja"),
    (18, "fr", "orange"),
    (18, "vi", "cam"),
    (19, "es", "papel"),
    (19, "fr", "papier"),
    (19, "vi", "giấy"),
    (20, "es", "teléfono"),
    (20, "fr", "téléphone"),
    (20, "vi", "điện thoại"),
    (21, "es", "pizza"),
    (21, "fr", "pizza"),
    (21, "vi", "pizza"),
    (22, "es", "tobogán"),
    (22, "fr", "toboggan"),
    (22, "vi", "cầu trượt"),
    (23, "es", "fresa"),
    (23, "fr", "fraise"),
    (23, "vi", "dâu"),
    (24, "es", "columpio"),
    (24, "fr", "balançoire"),
    (24, "vi", "xích đu"),
    (25, "es", "sandía"),
    (25, "fr", "pastèque"),
    (25, "vi", "dưa hấu")
])

conn.commit()
conn.close()
print('Created Word_Image and Translation tables with sample data')