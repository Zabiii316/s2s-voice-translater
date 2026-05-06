import re


class TranslationService:
    def clean_text(self, text: str) -> str:
        text = text.strip().lower()
        text = re.sub(r"[^\w\s\u0600-\u06FF]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def translate(
        self,
        text: str,
        source_language: str = "English",
        target_language: str = "Urdu"
    ):
        if not text:
            return ""

        source_language = source_language.strip()
        target_language = target_language.strip()
        text_clean = self.clean_text(text)

        english_to_urdu = {
            "i want to check my account balance": "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں۔",
            "i want to check my balance": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "hello": "السلام علیکم۔",
            "hello how are you": "السلام علیکم، آپ کیسے ہیں؟",
            "hello how can i help you": "السلام علیکم، میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "please wait for a moment": "براہ کرم ایک لمحہ انتظار کریں۔",
            "what is your name": "آپ کا نام کیا ہے؟",
            "thank you": "شکریہ۔",
            "i need help": "مجھے مدد چاہیے۔",
            "can you repeat that": "کیا آپ وہ دوبارہ کہہ سکتے ہیں؟",
            "your request has been received": "آپ کی درخواست موصول ہو گئی ہے۔",
            "we will call you back": "ہم آپ کو دوبارہ کال کریں گے۔"
        }

        english_to_arabic = {
            "i want to check my account balance": "أريد أن أتحقق من رصيد حسابي.",
            "i want to check my balance": "أريد أن أتحقق من رصيدي.",
            "hello": "مرحباً.",
            "hello how are you": "مرحباً، كيف حالك؟",
            "hello how can i help you": "مرحباً، كيف يمكنني مساعدتك؟",
            "please wait for a moment": "يرجى الانتظار لحظة.",
            "what is your name": "ما اسمك؟",
            "thank you": "شكراً لك.",
            "i need help": "أحتاج إلى مساعدة.",
            "can you repeat that": "هل يمكنك تكرار ذلك؟",
            "your request has been received": "تم استلام طلبك.",
            "we will call you back": "سوف نتصل بك مرة أخرى."
        }

        arabic_to_urdu = {
            "أريد أن أتحقق من رصيد حسابي": "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں۔",
            "أريد أن أتحقق من رصيدي": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "مرحبا": "السلام علیکم۔",
            "مرحباً": "السلام علیکم۔",
            "كيف حالك": "آپ کیسے ہیں؟",
            "كيف يمكنني مساعدتك": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "شكرا": "شکریہ۔",
            "شكراً لك": "آپ کا شکریہ۔",
            "أحتاج إلى مساعدة": "مجھے مدد چاہیے۔"
        }

        arabic_to_english = {
            "أريد أن أتحقق من رصيد حسابي": "I want to check my account balance.",
            "أريد أن أتحقق من رصيدي": "I want to check my balance.",
            "مرحبا": "Hello.",
            "مرحباً": "Hello.",
            "كيف حالك": "How are you?",
            "كيف يمكنني مساعدتك": "How can I help you?",
            "شكرا": "Thank you.",
            "شكراً لك": "Thank you.",
            "أحتاج إلى مساعدة": "I need help."
        }

        urdu_to_english = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "I want to check my account balance.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "I want to check my balance.",
            "السلام علیکم": "Hello.",
            "آپ کیسے ہیں": "How are you?",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "How can I help you?",
            "شکریہ": "Thank you.",
            "مجھے مدد چاہیے": "I need help."
        }

        urdu_to_arabic = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "أريد أن أتحقق من رصيد حسابي.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "أريد أن أتحقق من رصيدي.",
            "السلام علیکم": "مرحباً.",
            "آپ کیسے ہیں": "كيف حالك؟",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "كيف يمكنني مساعدتك؟",
            "شکریہ": "شكراً لك.",
            "مجھے مدد چاہیے": "أحتاج إلى مساعدة."
        }

        # English → Urdu
        if source_language == "English" and target_language == "Urdu":
            return english_to_urdu.get(
                text_clean,
                f"[Demo Urdu Translation] {text}"
            )

        # English → Arabic
        if source_language == "English" and target_language == "Arabic":
            return english_to_arabic.get(
                text_clean,
                f"[Demo Arabic Translation] {text}"
            )

        # Arabic → Urdu
        if source_language == "Arabic" and target_language == "Urdu":
            return arabic_to_urdu.get(
                text.strip(),
                f"[Demo Arabic to Urdu Translation] {text}"
            )

        # Arabic → English
        if source_language == "Arabic" and target_language == "English":
            return arabic_to_english.get(
                text.strip(),
                f"[Demo Arabic to English Translation] {text}"
            )

        # Urdu → English
        if source_language == "Urdu" and target_language == "English":
            return urdu_to_english.get(
                text.strip().replace("۔", ""),
                f"[Demo Urdu to English Translation] {text}"
            )

        # Urdu → Arabic
        if source_language == "Urdu" and target_language == "Arabic":
            return urdu_to_arabic.get(
                text.strip().replace("۔", ""),
                f"[Demo Urdu to Arabic Translation] {text}"
            )

        return f"[Demo Translation from {source_language} to {target_language}] {text}"