# 💳 Мөнгөн дэвтэр — Зарлагын бүртгэл

Самсунг утсан дээр Termux + Flask ашиглан ажиллах санхүүгийн бүртгэлийн апп.

---

## ⚡ Суулгах заавар (Termux дээр)

```bash
# 1. Termux шинэчлэх
pkg update && pkg upgrade -y

# 2. Python суулгах
pkg install python -y

# 3. Pip шинэчлэх
pip install --upgrade pip

# 4. Энэ хавтас руу орох
cd expense_tracker

# 5. Flask суулгах
pip install flask

# 6. Апп ажиллуулах
python app.py
```

## 📱 Ашиглах

1. `python app.py` гэж ажиллуулна
2. Самсунг утасны **Chrome / Samsung Internet** браузер нээнэ
3. `http://localhost:5000` хаяг руу орно
4. Боллоо! 🎉

## ✨ Боломжууд

- ➕ Зарлага / орлого бүртгэх (9 ангилал)
- 📊 Сарын тайлан — орлого, зарлага, үлдэгдэл
- 🎯 Ангилал тус бүрт зарлагын дээд хэмжээ тавих
- 💡 Автомат санхүүгийн зөвлөгөө
- 📅 Жилийн харьцуулалт + график
- 📥 CSV татаж авах (Excel-д нээнэ)
- 🌙 Dark mode UI

## 📁 Файлууд

```
expense_tracker/
├── app.py          # Flask backend + API
├── data.db         # SQLite database (автоматаар үүснэ)
├── requirements.txt
└── templates/
    └── index.html  # UI
```

## 🔄 Дараагийн хувилбарт нэмж болох зүйлс

- Зураг авч чек таних (OCR)
- PDF тайлан
- Банкны SMS автомат унших
- Нөөцлөх / сэргээх
