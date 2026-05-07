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
        target_language: str = "Urdu",
        arabic_dialect: str = "MSA"
    ):
        if not text:
            return ""

        source_language = source_language.strip()
        target_language = target_language.strip()
        arabic_dialect = arabic_dialect.strip()
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
            "we will call you back": "ہم آپ کو دوبارہ کال کریں گے۔",
            "my phone number is masked_phone and my account number is masked_account_number": "میرا فون نمبر [MASKED_PHONE] ہے اور میرا اکاؤنٹ نمبر [MASKED_ACCOUNT_NUMBER] ہے۔"
        }

        english_to_arabic_msa = {
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
            "we will call you back": "سوف نتصل بك مرة أخرى.",
            "my phone number is masked_phone and my account number is masked_account_number": "رقم هاتفي هو [MASKED_PHONE] ورقم حسابي هو [MASKED_ACCOUNT_NUMBER]."
        }

        english_to_arabic_gulf = {
            "i want to check my account balance": "أبغى أتأكد من رصيد حسابي.",
            "i want to check my balance": "أبغى أتأكد من رصيدي.",
            "hello": "هلا.",
            "hello how are you": "هلا، شلونك؟",
            "hello how can i help you": "هلا، كيف أقدر أساعدك؟",
            "please wait for a moment": "لو سمحت انتظر لحظة.",
            "what is your name": "وش اسمك؟",
            "thank you": "يعطيك العافية.",
            "i need help": "أحتاج مساعدة.",
            "can you repeat that": "ممكن تعيد الكلام؟",
            "my phone number is masked_phone and my account number is masked_account_number": "رقم جوالي [MASKED_PHONE] ورقم حسابي [MASKED_ACCOUNT_NUMBER]."
        }

        english_to_arabic_egyptian = {
            "i want to check my account balance": "عايز أتأكد من رصيد حسابي.",
            "i want to check my balance": "عايز أتأكد من رصيدي.",
            "hello": "أهلاً.",
            "hello how are you": "أهلاً، إزيك؟",
            "hello how can i help you": "أهلاً، أقدر أساعدك إزاي؟",
            "please wait for a moment": "من فضلك استنى لحظة.",
            "what is your name": "اسمك إيه؟",
            "thank you": "شكراً.",
            "i need help": "محتاج مساعدة.",
            "can you repeat that": "ممكن تعيد الكلام؟",
            "my phone number is masked_phone and my account number is masked_account_number": "رقم تليفوني [MASKED_PHONE] ورقم حسابي [MASKED_ACCOUNT_NUMBER]."
        }

        english_to_arabic_levantine = {
            "i want to check my account balance": "بدي أتأكد من رصيد حسابي.",
            "i want to check my balance": "بدي أتأكد من رصيدي.",
            "hello": "مرحبا.",
            "hello how are you": "مرحبا، كيفك؟",
            "hello how can i help you": "مرحبا، كيف فيني ساعدك؟",
            "please wait for a moment": "لو سمحت استنى شوي.",
            "what is your name": "شو اسمك؟",
            "thank you": "شكراً.",
            "i need help": "بدي مساعدة.",
            "can you repeat that": "ممكن تعيد الكلام؟",
            "my phone number is masked_phone and my account number is masked_account_number": "رقم تلفوني [MASKED_PHONE] ورقم حسابي [MASKED_ACCOUNT_NUMBER]."
        }

        arabic_to_urdu = {
            "أريد أن أتحقق من رصيد حسابي": "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں۔",
            "أريد أن أتحقق من رصيدي": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "أبغى أتأكد من رصيدي": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "عايز أتأكد من رصيدي": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "بدي أتأكد من رصيدي": "میں اپنا بیلنس چیک کرنا چاہتا ہوں۔",
            "مرحبا": "السلام علیکم۔",
            "مرحباً": "السلام علیکم۔",
            "هلا": "السلام علیکم۔",
            "أهلاً": "السلام علیکم۔",
            "كيف حالك": "آپ کیسے ہیں؟",
            "شلونك": "آپ کیسے ہیں؟",
            "إزيك": "آپ کیسے ہیں؟",
            "كيفك": "آپ کیسے ہیں؟",
            "كيف يمكنني مساعدتك": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "كيف أقدر أساعدك": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "أقدر أساعدك إزاي": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "كيف فيني ساعدك": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
            "شكرا": "شکریہ۔",
            "شكراً لك": "آپ کا شکریہ۔",
            "يعطيك العافية": "آپ کا شکریہ۔",
            "أحتاج إلى مساعدة": "مجھے مدد چاہیے۔"
        }

        arabic_to_english = {
            "أريد أن أتحقق من رصيد حسابي": "I want to check my account balance.",
            "أريد أن أتحقق من رصيدي": "I want to check my balance.",
            "أبغى أتأكد من رصيدي": "I want to check my balance.",
            "عايز أتأكد من رصيدي": "I want to check my balance.",
            "بدي أتأكد من رصيدي": "I want to check my balance.",
            "مرحبا": "Hello.",
            "مرحباً": "Hello.",
            "هلا": "Hello.",
            "أهلاً": "Hello.",
            "كيف حالك": "How are you?",
            "شلونك": "How are you?",
            "إزيك": "How are you?",
            "كيفك": "How are you?",
            "كيف يمكنني مساعدتك": "How can I help you?",
            "كيف أقدر أساعدك": "How can I help you?",
            "أقدر أساعدك إزاي": "How can I help you?",
            "كيف فيني ساعدك": "How can I help you?",
            "شكرا": "Thank you.",
            "شكراً لك": "Thank you.",
            "يعطيك العافية": "Thank you.",
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

        urdu_to_arabic_msa = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "أريد أن أتحقق من رصيد حسابي.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "أريد أن أتحقق من رصيدي.",
            "السلام علیکم": "مرحباً.",
            "آپ کیسے ہیں": "كيف حالك؟",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "كيف يمكنني مساعدتك؟",
            "شکریہ": "شكراً لك.",
            "مجھے مدد چاہیے": "أحتاج إلى مساعدة."
        }

        urdu_to_arabic_gulf = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "أبغى أتأكد من رصيد حسابي.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "أبغى أتأكد من رصيدي.",
            "السلام علیکم": "هلا.",
            "آپ کیسے ہیں": "شلونك؟",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "كيف أقدر أساعدك؟",
            "شکریہ": "يعطيك العافية.",
            "مجھے مدد چاہیے": "أحتاج مساعدة."
        }

        urdu_to_arabic_egyptian = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "عايز أتأكد من رصيد حسابي.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "عايز أتأكد من رصيدي.",
            "السلام علیکم": "أهلاً.",
            "آپ کیسے ہیں": "إزيك؟",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "أقدر أساعدك إزاي؟",
            "شکریہ": "شكراً.",
            "مجھے مدد چاہیے": "محتاج مساعدة."
        }

        urdu_to_arabic_levantine = {
            "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں": "بدي أتأكد من رصيد حسابي.",
            "میں اپنا بیلنس چیک کرنا چاہتا ہوں": "بدي أتأكد من رصيدي.",
            "السلام علیکم": "مرحبا.",
            "آپ کیسے ہیں": "كيفك؟",
            "میں آپ کی کیسے مدد کر سکتا ہوں": "كيف فيني ساعدك؟",
            "شکریہ": "شكراً.",
            "مجھے مدد چاہیے": "بدي مساعدة."
        }

        def select_arabic_dictionary(msa, gulf, egyptian, levantine):
            if arabic_dialect == "Gulf Arabic":
                return gulf
            if arabic_dialect == "Egyptian Arabic":
                return egyptian
            if arabic_dialect == "Levantine Arabic":
                return levantine
            return msa

        english_to_arabic = select_arabic_dictionary(
            english_to_arabic_msa,
            english_to_arabic_gulf,
            english_to_arabic_egyptian,
            english_to_arabic_levantine
        )

        urdu_to_arabic = select_arabic_dictionary(
            urdu_to_arabic_msa,
            urdu_to_arabic_gulf,
            urdu_to_arabic_egyptian,
            urdu_to_arabic_levantine
        )

        if source_language == "English" and target_language == "Urdu":
            return english_to_urdu.get(
                text_clean,
                f"[Demo Urdu Translation] {text}"
            )

        if source_language == "English" and target_language == "Arabic":
            return english_to_arabic.get(
                text_clean,
                f"[Demo Arabic Translation - {arabic_dialect}] {text}"
            )

        if source_language == "Arabic" and target_language == "Urdu":
            return arabic_to_urdu.get(
                text.strip().replace("؟", "").replace(".", ""),
                f"[Demo Arabic to Urdu Translation - {arabic_dialect}] {text}"
            )

        if source_language == "Arabic" and target_language == "English":
            return arabic_to_english.get(
                text.strip().replace("؟", "").replace(".", ""),
                f"[Demo Arabic to English Translation - {arabic_dialect}] {text}"
            )

        if source_language == "Urdu" and target_language == "English":
            return urdu_to_english.get(
                text.strip().replace("۔", ""),
                f"[Demo Urdu to English Translation] {text}"
            )

        if source_language == "Urdu" and target_language == "Arabic":
            return urdu_to_arabic.get(
                text.strip().replace("۔", ""),
                f"[Demo Urdu to Arabic Translation - {arabic_dialect}] {text}"
            )

        return f"[Demo Translation from {source_language} to {target_language}] {text}"