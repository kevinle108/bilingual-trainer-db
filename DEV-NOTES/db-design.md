
tables:

table: Word_Image
columns: id, english_word, image_file
example: 1, "bird", "bird.png"

table: Translation
columns: id, word_id (FK to Word_Image.id), language_code, translated_word
example: 1, 2, "es", "pájaro"

Relationship:
- One Word_Image can have many Translations (one per language)
- Query example: Get Spanish flashcard for 'bird'
  SELECT w.english_word, w.image_file, t.translated_word, t.language_code
  FROM Word_Image w
  JOIN Translation t ON w.id = t.word_id
  WHERE w.english_word = 'bird' AND t.language_code = 'es'

