# AI Flashcard Generator - User Guide

## 🎯 Overview
The AI Flashcard Generator allows you to create custom vocabulary sets on any topic using artificial intelligence. Simply specify a theme, language, and count, and the AI will generate relevant flashcards with optional images!

## ✨ Features

### 🤖 AI-Powered Generation
- **Custom Topics**: Generate flashcards on any theme (animals, food, travel, etc.)
- **Multiple Languages**: Support for Vietnamese, Spanish, and French
- **Smart Vocabulary**: AI selects appropriate words for your skill level
- **Context Hints**: Optional learning hints and mnemonics

### 🖼️ Automatic Image Fetching
- **Wikimedia Commons Integration**: Automatically fetches relevant images
- **Free Service**: No API keys required
- **Educational Content**: Curated from Commons' image library
- **Offline Mode**: Works without images too

### 💾 Database Integration
- **Automatic Saving**: Generated cards are saved to your database
- **Duplicate Detection**: Won't create duplicate entries
- **Immediate Access**: View cards instantly in Flashcards or Chatbot modes

## 🚀 How to Use

### 1. Access the Generator
From the home page, click the **"✨ AI Flashcard Generator"** button

### 2. Fill in the Form

**Theme or Topic** (Required)
- Examples: "animals", "kitchen items", "travel vocabulary", "business terms"
- Be specific for better results

**Target Language** (Required)
- Choose from Vietnamese, Spanish, or French
- This is the language you want to learn

**Number of Cards** (Required)
- Enter a number between 3 and 30
- Recommended: 10-15 cards per topic for best learning

**Additional Details** (Optional)
- Add specific requirements like:
  - "Focus on beginner vocabulary"
  - "Include common phrases"
  - "Avoid technical terms"
  - "Include food-related verbs"

**Fetch Images** (Optional)
- Check this box to automatically download images from Wikimedia Commons
- Makes flashcards more visual and memorable
- Note: May take a bit longer (about 1-2 seconds per image)

### 3. Generate!
- Click **"✨ Generate Flashcards with AI"**
- Wait 10-30 seconds while the AI works
- See success message with count

### 4. View Your Cards
- Click **"View Flashcards"** to see them immediately
- Or return to home and select the language

## 📝 Examples

### Example 1: Basic Animals
```
Theme: farm animals
Language: Vietnamese
Count: 10
Fetch Images: ✓
```
**Result**: 10 flashcards with common farm animals (cow, pig, chicken, etc.) with images

### Example 2: Travel Phrases
```
Theme: airport and travel
Language: Spanish
Count: 15
Description: Include common phrases travelers need
Fetch Images: ✗
```
**Result**: 15 useful travel phrases (text-only)

### Example 3: Kitchen Vocabulary
```
Theme: kitchen utensils and cooking
Language: French
Count: 12
Description: Focus on beginner level, common household items
Fetch Images: ✓
```
**Result**: 12 kitchen-related words with images

## 🎨 What Gets Generated

Each flashcard includes:
- **English word/phrase**: The vocabulary you're learning
- **Translation**: In your target language
- **Image** (if enabled): Visual representation from Wikimedia Commons
- **Hint** (sometimes): Learning tips or mnemonics from the AI

## 🔧 Technical Details

### How It Works
1. **AI Generation**: Uses LangChain + GPT-4o-mini to generate vocabulary
2. **Image Search**: Queries Wikimedia Commons API for relevant images
3. **Image Download**: Saves images to `/image-library/` folder
4. **Database Insert**: Adds words and translations to your SQLite database
5. **Duplicate Check**: Skips words that already exist

### API Calls
- **1 AI call**: To generate all flashcards at once
- **N image calls**: One per word (if images enabled)
- **Rate limiting**: 0.5 second delay between image requests (be polite!)

### Storage
- **Database**: Words stored in `Word_Image` and `Translation` tables
- **Images**: Saved in `image-library/` folder with timestamped names
- **Format**: Images are typically JPG or PNG (512px width)

## ⚙️ Configuration

### Requirements
- GitHub Token with access to GitHub Models API
- Internet connection for image fetching
- At least 100MB free space for images (if generating many cards)

### Limits
- **Minimum cards**: 3
- **Maximum cards**: 30
- **Supported languages**: Vietnamese, Spanish, French
- **Image timeout**: 10 seconds per image

## 🐛 Troubleshooting

### "AI service not configured"
**Problem**: GitHub token not set
**Solution**: Make sure `.env` has `GITHUB_TOKEN=your_token_here`

### "Failed to generate flashcards"
**Problem**: AI returned invalid format
**Solution**: Try again with a clearer, simpler theme

### No images downloaded
**Problem**: Wikimedia Commons didn't have matching images
**Solution**: Normal! Not all words have images. The flashcard is still created.

### Duplicate cards not created
**Problem**: Words already exist in database
**Solution**: This is intentional! Prevents duplicates. Try a different theme.

### Generation is slow
**Problem**: Fetching images takes time
**Solution**: 
- Uncheck "Fetch Images" for faster generation
- Or reduce the card count

## 💡 Tips for Best Results

### 🎯 Be Specific with Themes
- ❌ Bad: "words"
- ✅ Good: "common household furniture"

### 📊 Choose Appropriate Counts
- **Beginner**: 5-10 cards per session
- **Intermediate**: 10-15 cards
- **Advanced**: 15-20 cards

### 🖼️ When to Use Images
- **Use images** for: Concrete nouns (objects, animals, food)
- **Skip images** for: Abstract concepts, verbs, phrases

### 📝 Use Additional Details
Add details like:
- "For children ages 6-8"
- "Business professional context"
- "Colloquial expressions preferred"
- "Include pronunciation hints"

## 🎓 Learning Workflow

1. **Generate** flashcards on a topic
2. **Study** with flashcards view
3. **Practice** with AI chatbot
4. **Repeat** with new topics

## 🚀 Coming Soon

Future enhancements planned:
- Bulk import from CSV
- Custom image upload
- Pronunciation audio
- Spaced repetition scheduling
- Export to Anki format

## 📞 Need Help?

If you encounter issues:
1. Check console logs for detailed errors
2. Verify your GitHub token is valid
3. Try with a smaller card count
4. Disable image fetching to isolate the issue

---

Happy learning! 🎉
