import sqlite3

conn = sqlite3.connect('BilingualTrainer.db')
cur = conn.cursor()

# Check total translations
cur.execute('SELECT COUNT(*) FROM Translation')
print(f'Total translations: {cur.fetchone()[0]}')

print('\n--- Sample Spanish Flashcards ---')
cur.execute('''
SELECT w.english_word, t.translated_word, w.image_file 
FROM Word_Image w 
JOIN Translation t ON w.id = t.word_id 
WHERE t.language_code = 'es' 
LIMIT 10
''')
for row in cur.fetchall():
    print(f'{row[0]:12s} -> {row[1]:15s} ({row[2]})')

print('\n--- Sample French Flashcards ---')
cur.execute('''
SELECT w.english_word, t.translated_word, w.image_file 
FROM Word_Image w 
JOIN Translation t ON w.id = t.word_id 
WHERE t.language_code = 'fr' 
LIMIT 10
''')
for row in cur.fetchall():
    print(f'{row[0]:12s} -> {row[1]:15s} ({row[2]})')

conn.close()
