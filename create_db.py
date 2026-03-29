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
conn.commit()
conn.close()
print('Created Word_Image table with sample data')