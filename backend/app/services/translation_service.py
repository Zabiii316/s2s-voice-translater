from __future__ import annotations

import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranslationResult:
    translated_text: str
    provider: str
    segments: List[str]


class TranslationService:
    """
    Full-sentence translation service.

    Translation order:
    1. OpenAI translation for unrestricted sentences.
    2. Large offline multilingual phrasebook if OpenAI is unavailable.
    """

    SUPPORTED_LANGUAGES = {
        "English",
        "Urdu",
        "Arabic",
    }

    SUPPORTED_DIALECTS = {
        "MSA",
        "Gulf Arabic",
        "Egyptian Arabic",
        "Levantine Arabic",
    }

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()

        self.model = os.getenv(
            "OPENAI_TRANSLATION_MODEL",
            "gpt-4o-mini",
        ).strip()

        self.max_chars = int(
            os.getenv("TRANSLATION_MAX_CHARS", "6000")
        )

        self._client: Optional[Any] = None

        if self.api_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    timeout=30.0,
                    max_retries=2,
                )

            except Exception:
                logger.exception(
                    "Could not initialize the OpenAI client"
                )

        self._phrasebook = self._build_phrasebook()
        self._lookup = self._build_lookup()

    @property
    def ai_enabled(self) -> bool:
        return self._client is not None

    @staticmethod
    def _build_phrasebook() -> List[Dict[str, Any]]:
        """
        Offline phrases.

        Arabic may be:
        - One MSA sentence
        - A dictionary containing dialect versions
        """

        return [
            {
                "English": "Hello.",
                "Urdu": "السلام علیکم۔",
                "Arabic": {
                    "MSA": "مرحباً.",
                    "Gulf Arabic": "هلا.",
                    "Egyptian Arabic": "أهلاً.",
                    "Levantine Arabic": "مرحبا.",
                },
            },
            {
                "English": "Hello, how are you?",
                "Urdu": "السلام علیکم، آپ کیسے ہیں؟",
                "Arabic": {
                    "MSA": "مرحباً، كيف حالك؟",
                    "Gulf Arabic": "هلا، شلونك؟",
                    "Egyptian Arabic": "أهلاً، إزيك؟",
                    "Levantine Arabic": "مرحبا، كيفك؟",
                },
            },
            {
                "English": "I am fine, thank you.",
                "Urdu": "میں ٹھیک ہوں، شکریہ۔",
                "Arabic": {
                    "MSA": "أنا بخير، شكراً لك.",
                    "Gulf Arabic": "أنا بخير، يعطيك العافية.",
                    "Egyptian Arabic": "أنا كويس، شكراً.",
                    "Levantine Arabic": "أنا منيح، شكراً.",
                },
            },
            {
                "English": "How can I help you?",
                "Urdu": "میں آپ کی کیسے مدد کر سکتا ہوں؟",
                "Arabic": {
                    "MSA": "كيف يمكنني مساعدتك؟",
                    "Gulf Arabic": "كيف أقدر أساعدك؟",
                    "Egyptian Arabic": "أقدر أساعدك إزاي؟",
                    "Levantine Arabic": "كيف فيني ساعدك؟",
                },
            },
            {
                "English": "I need help.",
                "Urdu": "مجھے مدد چاہیے۔",
                "Arabic": {
                    "MSA": "أحتاج إلى مساعدة.",
                    "Gulf Arabic": "أحتاج مساعدة.",
                    "Egyptian Arabic": "محتاج مساعدة.",
                    "Levantine Arabic": "بدي مساعدة.",
                },
            },
            {
                "English": "Thank you very much.",
                "Urdu": "آپ کا بہت شکریہ۔",
                "Arabic": {
                    "MSA": "شكراً جزيلاً لك.",
                    "Gulf Arabic": "مشكور وايد.",
                    "Egyptian Arabic": "شكراً جداً.",
                    "Levantine Arabic": "شكراً كتير.",
                },
            },
            {
                "English": "You are welcome.",
                "Urdu": "خوش آمدید۔",
                "Arabic": {
                    "MSA": "على الرحب والسعة.",
                    "Gulf Arabic": "العفو.",
                    "Egyptian Arabic": "العفو.",
                    "Levantine Arabic": "أهلاً وسهلاً.",
                },
            },
            {
                "English": "Yes.",
                "Urdu": "جی ہاں۔",
                "Arabic": "نعم.",
            },
            {
                "English": "No.",
                "Urdu": "نہیں۔",
                "Arabic": "لا.",
            },
            {
                "English": "Please wait for a moment.",
                "Urdu": "براہ کرم ایک لمحہ انتظار کریں۔",
                "Arabic": {
                    "MSA": "يرجى الانتظار لحظة.",
                    "Gulf Arabic": "لو سمحت انتظر شوي.",
                    "Egyptian Arabic": "من فضلك استنى لحظة.",
                    "Levantine Arabic": "لو سمحت استنى شوي.",
                },
            },
            {
                "English": "Please hold the line.",
                "Urdu": "براہ کرم لائن پر رہیں۔",
                "Arabic": {
                    "MSA": "يرجى البقاء على الخط.",
                    "Gulf Arabic": "خلك على الخط لو سمحت.",
                    "Egyptian Arabic": "خليك على الخط من فضلك.",
                    "Levantine Arabic": "خليك عالخط لو سمحت.",
                },
            },
            {
                "English": "Please speak slowly.",
                "Urdu": "براہ کرم آہستہ بولیں۔",
                "Arabic": {
                    "MSA": "يرجى التحدث ببطء.",
                    "Gulf Arabic": "تكلم شوي شوي لو سمحت.",
                    "Egyptian Arabic": "اتكلم بالراحة من فضلك.",
                    "Levantine Arabic": "احكي شوي شوي لو سمحت.",
                },
            },
            {
                "English": "Can you repeat that?",
                "Urdu": "کیا آپ یہ دوبارہ کہہ سکتے ہیں؟",
                "Arabic": {
                    "MSA": "هل يمكنك تكرار ذلك؟",
                    "Gulf Arabic": "ممكن تعيد الكلام؟",
                    "Egyptian Arabic": "ممكن تعيد الكلام؟",
                    "Levantine Arabic": "ممكن تعيد الحكي؟",
                },
            },
            {
                "English": "I do not understand.",
                "Urdu": "میں سمجھا نہیں۔",
                "Arabic": {
                    "MSA": "أنا لا أفهم.",
                    "Gulf Arabic": "أنا ما فهمت.",
                    "Egyptian Arabic": "أنا مش فاهم.",
                    "Levantine Arabic": "أنا ما فهمت.",
                },
            },
            {
                "English": "What is your name?",
                "Urdu": "آپ کا نام کیا ہے؟",
                "Arabic": {
                    "MSA": "ما اسمك؟",
                    "Gulf Arabic": "وش اسمك؟",
                    "Egyptian Arabic": "اسمك إيه؟",
                    "Levantine Arabic": "شو اسمك؟",
                },
            },
            {
                "English": "May I have your phone number?",
                "Urdu": "کیا مجھے آپ کا فون نمبر مل سکتا ہے؟",
                "Arabic": {
                    "MSA": "هل يمكنني الحصول على رقم هاتفك؟",
                    "Gulf Arabic": "ممكن رقم جوالك؟",
                    "Egyptian Arabic": "ممكن رقم تليفونك؟",
                    "Levantine Arabic": "ممكن رقم تلفونك؟",
                },
            },
            {
                "English": "My phone number is [MASKED_PHONE].",
                "Urdu": "میرا فون نمبر [MASKED_PHONE] ہے۔",
                "Arabic": "رقم هاتفي هو [MASKED_PHONE].",
            },
            {
                "English": "My account number is [MASKED_ACCOUNT_NUMBER].",
                "Urdu": "میرا اکاؤنٹ نمبر [MASKED_ACCOUNT_NUMBER] ہے۔",
                "Arabic": "رقم حسابي هو [MASKED_ACCOUNT_NUMBER].",
            },
            {
                "English": "Please verify your identity.",
                "Urdu": "براہ کرم اپنی شناخت کی تصدیق کریں۔",
                "Arabic": "يرجى التحقق من هويتك.",
            },
            {
                "English": "Your information is secure.",
                "Urdu": "آپ کی معلومات محفوظ ہیں۔",
                "Arabic": "معلوماتك آمنة.",
            },
            {
                "English": "I want to check my account balance.",
                "Urdu": "میں اپنے اکاؤنٹ کا بیلنس چیک کرنا چاہتا ہوں۔",
                "Arabic": {
                    "MSA": "أريد التحقق من رصيد حسابي.",
                    "Gulf Arabic": "أبغى أتأكد من رصيد حسابي.",
                    "Egyptian Arabic": "عايز أتأكد من رصيد حسابي.",
                    "Levantine Arabic": "بدي أتأكد من رصيد حسابي.",
                },
            },
            {
                "English": "My account is blocked.",
                "Urdu": "میرا اکاؤنٹ بلاک ہو گیا ہے۔",
                "Arabic": "حسابي محظور.",
            },
            {
                "English": "I forgot my password.",
                "Urdu": "میں اپنا پاس ورڈ بھول گیا ہوں۔",
                "Arabic": "لقد نسيت كلمة المرور.",
            },
            {
                "English": "I want to reset my password.",
                "Urdu": "میں اپنا پاس ورڈ ری سیٹ کرنا چاہتا ہوں۔",
                "Arabic": "أريد إعادة تعيين كلمة المرور.",
            },
            {
                "English": "My card has been lost.",
                "Urdu": "میرا کارڈ گم ہو گیا ہے۔",
                "Arabic": "لقد فقدت بطاقتي.",
            },
            {
                "English": "My card is not working.",
                "Urdu": "میرا کارڈ کام نہیں کر رہا۔",
                "Arabic": "بطاقتي لا تعمل.",
            },
            {
                "English": "I want to block my card.",
                "Urdu": "میں اپنا کارڈ بلاک کرنا چاہتا ہوں۔",
                "Arabic": "أريد إيقاف بطاقتي.",
            },
            {
                "English": "I want to transfer money.",
                "Urdu": "میں رقم منتقل کرنا چاہتا ہوں۔",
                "Arabic": "أريد تحويل المال.",
            },
            {
                "English": "The transaction failed.",
                "Urdu": "لین دین ناکام ہو گیا۔",
                "Arabic": "فشلت المعاملة.",
            },
            {
                "English": "The payment is pending.",
                "Urdu": "ادائیگی زیر التوا ہے۔",
                "Arabic": "الدفع قيد الانتظار.",
            },
            {
                "English": "I was charged twice.",
                "Urdu": "مجھ سے دو بار رقم وصول کی گئی۔",
                "Arabic": "تم خصم المبلغ مني مرتين.",
            },
            {
                "English": "I want a refund.",
                "Urdu": "میں رقم کی واپسی چاہتا ہوں۔",
                "Arabic": "أريد استرداد المبلغ.",
            },
            {
                "English": "When will I receive the refund?",
                "Urdu": "مجھے رقم کی واپسی کب ملے گی؟",
                "Arabic": "متى سأستلم المبلغ المسترد؟",
            },
            {
                "English": "Your request has been received.",
                "Urdu": "آپ کی درخواست موصول ہو گئی ہے۔",
                "Arabic": "تم استلام طلبك.",
            },
            {
                "English": "Your request is being processed.",
                "Urdu": "آپ کی درخواست پر کارروائی ہو رہی ہے۔",
                "Arabic": "طلبك قيد المعالجة.",
            },
            {
                "English": "We will call you back.",
                "Urdu": "ہم آپ کو دوبارہ کال کریں گے۔",
                "Arabic": "سوف نتصل بك مرة أخرى.",
            },
            {
                "English": "I want to speak to a supervisor.",
                "Urdu": "میں سپروائزر سے بات کرنا چاہتا ہوں۔",
                "Arabic": "أريد التحدث إلى المشرف.",
            },
            {
                "English": "I want to make a complaint.",
                "Urdu": "میں شکایت درج کرنا چاہتا ہوں۔",
                "Arabic": "أريد تقديم شكوى.",
            },
            {
                "English": "The problem has been resolved.",
                "Urdu": "مسئلہ حل ہو گیا ہے۔",
                "Arabic": "تم حل المشكلة.",
            },
            {
                "English": "What are your working hours?",
                "Urdu": "آپ کے کام کے اوقات کیا ہیں؟",
                "Arabic": "ما ساعات العمل لديكم؟",
            },
            {
                "English": "Where is your office?",
                "Urdu": "آپ کا دفتر کہاں ہے؟",
                "Arabic": "أين يقع مكتبكم؟",
            },
            {
                "English": "I want to book an appointment.",
                "Urdu": "میں ملاقات کا وقت لینا چاہتا ہوں۔",
                "Arabic": "أريد حجز موعد.",
            },
            {
                "English": "I want to cancel my appointment.",
                "Urdu": "میں اپنی ملاقات منسوخ کرنا چاہتا ہوں۔",
                "Arabic": "أريد إلغاء موعدي.",
            },
            {
                "English": "What time is my appointment?",
                "Urdu": "میری ملاقات کس وقت ہے؟",
                "Arabic": "في أي وقت موعدي؟",
            },
            {
                "English": "This is an emergency.",
                "Urdu": "یہ ایک ہنگامی صورتحال ہے۔",
                "Arabic": "هذه حالة طارئة.",
            },
            {
                "English": "I need a doctor.",
                "Urdu": "مجھے ڈاکٹر چاہیے۔",
                "Arabic": "أحتاج إلى طبيب.",
            },
            {
                "English": "I am in pain.",
                "Urdu": "مجھے درد ہو رہا ہے۔",
                "Arabic": "أنا أشعر بالألم.",
            },
            {
                "English": "Where is the nearest hospital?",
                "Urdu": "قریب ترین ہسپتال کہاں ہے؟",
                "Arabic": "أين أقرب مستشفى؟",
            },
            {
                "English": "I want to confirm my booking.",
                "Urdu": "میں اپنی بکنگ کی تصدیق کرنا چاہتا ہوں۔",
                "Arabic": "أريد تأكيد حجزي.",
            },
            {
                "English": "My flight is delayed.",
                "Urdu": "میری پرواز تاخیر کا شکار ہے۔",
                "Arabic": "رحلتي متأخرة.",
            },
            {
                "English": "My baggage is missing.",
                "Urdu": "میرا سامان گم ہے۔",
                "Arabic": "أمتعتي مفقودة.",
            },
            {
                "English": "Where is the boarding gate?",
                "Urdu": "بورڈنگ گیٹ کہاں ہے؟",
                "Arabic": "أين بوابة الصعود؟",
            },
            {
                "English": "How much does this cost?",
                "Urdu": "اس کی قیمت کتنی ہے؟",
                "Arabic": "كم سعر هذا؟",
            },
            {
                "English": "I want to place an order.",
                "Urdu": "میں آرڈر دینا چاہتا ہوں۔",
                "Arabic": "أريد تقديم طلب.",
            },
            {
                "English": "Where is my order?",
                "Urdu": "میرا آرڈر کہاں ہے؟",
                "Arabic": "أين طلبي؟",
            },
            {
                "English": "My order has not arrived.",
                "Urdu": "میرا آرڈر ابھی تک نہیں پہنچا۔",
                "Arabic": "لم يصل طلبي بعد.",
            },
            {
                "English": "I want to change the delivery address.",
                "Urdu": "میں ڈیلیوری کا پتہ تبدیل کرنا چاہتا ہوں۔",
                "Arabic": "أريد تغيير عنوان التوصيل.",
            },
            {
                "English": "The internet is not working.",
                "Urdu": "انٹرنیٹ کام نہیں کر رہا۔",
                "Arabic": "الإنترنت لا يعمل.",
            },
            {
                "English": "The connection is very slow.",
                "Urdu": "کنکشن بہت سست ہے۔",
                "Arabic": "الاتصال بطيء جداً.",
            },
            {
                "English": "Please send me an email.",
                "Urdu": "براہ کرم مجھے ای میل بھیجیں۔",
                "Arabic": "يرجى إرسال بريد إلكتروني لي.",
            },
            {
                "English": "Please send me the details.",
                "Urdu": "براہ کرم مجھے تفصیلات بھیجیں۔",
                "Arabic": "يرجى إرسال التفاصيل لي.",
            },
            {
                "English": "I will contact you later.",
                "Urdu": "میں آپ سے بعد میں رابطہ کروں گا۔",
                "Arabic": "سأتواصل معك لاحقاً.",
            },
            {
                "English": "Is there anything else I can help you with?",
                "Urdu": "کیا میں کسی اور چیز میں آپ کی مدد کر سکتا ہوں؟",
                "Arabic": "هل هناك أي شيء آخر يمكنني مساعدتك فيه؟",
            },
            {
                "English": "Have a nice day.",
                "Urdu": "آپ کا دن اچھا گزرے۔",
                "Arabic": "أتمنى لك يوماً سعيداً.",
            },
            {
                "English": "Goodbye.",
                "Urdu": "خدا حافظ۔",
                "Arabic": {
                    "MSA": "إلى اللقاء.",
                    "Gulf Arabic": "مع السلامة.",
                    "Egyptian Arabic": "مع السلامة.",
                    "Levantine Arabic": "مع السلامة.",
                },
            },
        ]

    def _build_lookup(
        self,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:

        lookup: Dict[str, Dict[str, Dict[str, Any]]] = {
            "English": {},
            "Urdu": {},
            "Arabic": {},
        }

        for entry in self._phrasebook:
            for language in self.SUPPORTED_LANGUAGES:
                value = entry[language]

                if isinstance(value, dict):
                    variants = value.values()
                else:
                    variants = [value]

                for variant in variants:
                    normalized = self._normalize_for_lookup(
                        variant
                    )

                    lookup[language][normalized] = entry

        return lookup

    @staticmethod
    def _strip_arabic_diacritics(
        text: str,
    ) -> str:

        return re.sub(
            r"[\u0610-\u061A\u064B-\u065F"
            r"\u0670\u06D6-\u06ED]",
            "",
            text,
        )

    def _normalize_for_lookup(
        self,
        text: str,
    ) -> str:

        text = unicodedata.normalize(
            "NFKC",
            text or "",
        )

        text = self._strip_arabic_diacritics(text)
        text = text.casefold()

        text = (
            text.replace("أ", "ا")
            .replace("إ", "ا")
            .replace("آ", "ا")
            .replace("ى", "ي")
            .replace("ۀ", "ہ")
        )

        text = re.sub(
            r"[^\w\s\u0600-\u06FF\[\]]",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def normalize_language(
        self,
        language: str,
    ) -> str:

        aliases = {
            "en": "English",
            "english": "English",
            "ur": "Urdu",
            "urdu": "Urdu",
            "ar": "Arabic",
            "arabic": "Arabic",
        }

        normalized = aliases.get(
            (language or "").strip().casefold()
        )

        if not normalized:
            raise ValueError(
                f"Unsupported language: {language}"
            )

        return normalized

    def normalize_dialect(
        self,
        dialect: str,
    ) -> str:

        value = (dialect or "MSA").strip()

        if value in self.SUPPORTED_DIALECTS:
            return value

        return "MSA"

    def clean_input(
        self,
        text: str,
    ) -> str:

        text = unicodedata.normalize(
            "NFKC",
            text or "",
        )

        text = (
            text.replace("\u200e", "")
            .replace("\u200f", "")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if len(text) > self.max_chars:
            raise ValueError(
                f"Text is longer than the "
                f"{self.max_chars}-character limit"
            )

        return text

    def split_sentences(
        self,
        text: str,
    ) -> List[str]:

        text = self.clean_input(text)

        if not text:
            return []

        parts = re.split(
            r"(?<=[.!?؟۔])\s+|[\r\n]+",
            text,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    @staticmethod
    def _target_value(
        entry: Dict[str, Any],
        target_language: str,
        dialect: str,
    ) -> str:

        value = entry[target_language]

        if isinstance(value, dict):
            return (
                value.get(dialect)
                or value.get("MSA")
                or next(iter(value.values()))
            )

        return value

    def _find_offline_entry(
        self,
        text: str,
        source_language: str,
    ) -> Optional[Dict[str, Any]]:

        normalized = self._normalize_for_lookup(text)

        exact = self._lookup[
            source_language
        ].get(normalized)

        if exact:
            return exact

        best_entry: Optional[
            Dict[str, Any]
        ] = None

        best_score = 0.0

        for candidate, entry in self._lookup[
            source_language
        ].items():

            length_difference = abs(
                len(candidate) - len(normalized)
            )

            maximum_difference = max(
                8,
                len(normalized) * 0.25,
            )

            if length_difference > maximum_difference:
                continue

            score = SequenceMatcher(
                None,
                normalized,
                candidate,
            ).ratio()

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= 0.90:
            return best_entry

        return None

    def _translate_offline(
        self,
        text: str,
        source_language: str,
        target_language: str,
        dialect: str,
    ) -> TranslationResult:

        translated_segments: List[str] = []
        unsupported_segments: List[str] = []

        source_segments = self.split_sentences(text)

        for segment in source_segments:
            entry = self._find_offline_entry(
                segment,
                source_language,
            )

            if entry:
                translated_segments.append(
                    self._target_value(
                        entry,
                        target_language,
                        dialect,
                    )
                )

            else:
                unsupported_segments.append(segment)

        if unsupported_segments:
            supported_text = " ".join(
                translated_segments
            ).strip()

            missing_text = " | ".join(
                unsupported_segments
            )

            message = ""

            if supported_text:
                message += supported_text + "\n"

            message += (
                "[Offline phrase not found. "
                "Add OPENAI_API_KEY for unrestricted "
                f"translation: {missing_text}]"
            )

            return TranslationResult(
                translated_text=message.strip(),
                provider="offline_phrasebook_partial",
                segments=source_segments,
            )

        return TranslationResult(
            translated_text=" ".join(
                translated_segments
            ).strip(),
            provider="offline_phrasebook",
            segments=source_segments,
        )

    def _instructions(
        self,
        source_language: str,
        target_language: str,
        dialect: str,
    ) -> str:

        dialect_instruction = ""

        if target_language == "Arabic":
            dialect_instruction = (
                f"Write the Arabic translation in "
                f"{dialect}. For MSA, use natural "
                "Modern Standard Arabic."
            )

        elif source_language == "Arabic":
            dialect_instruction = (
                f"The speaker may use {dialect}. "
                "Understand dialectal vocabulary correctly."
            )

        return (
            "You are a professional live call interpreter. "
            f"Translate from {source_language} "
            f"to {target_language}. "
            "Translate every sentence completely and "
            "in the same order. "
            "Do not summarize, shorten, answer, explain, "
            "add labels, or omit repeated information. "
            "Preserve names, numbers, dates, currencies, "
            "product names, and placeholders such as "
            "[MASKED_PHONE] and "
            "[MASKED_ACCOUNT_NUMBER] exactly. "
            "Return only the translated text. "
            + dialect_instruction
        )

    async def _translate_with_ai(
        self,
        text: str,
        source_language: str,
        target_language: str,
        dialect: str,
    ) -> Optional[str]:

        if not self._client:
            return None

        instructions = self._instructions(
            source_language,
            target_language,
            dialect,
        )

        try:
            response = await self._client.responses.create(
                model=self.model,
                instructions=instructions,
                input=text,
                max_output_tokens=2000,
            )

            output = (
                response.output_text or ""
            ).strip()

            if output:
                return output

        except (AttributeError, TypeError):
            logger.warning(
                "Responses API unavailable. "
                "Trying Chat Completions."
            )

        except Exception:
            logger.exception(
                "OpenAI Responses translation failed"
            )

        try:
            completion = (
                await self._client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": instructions,
                        },
                        {
                            "role": "user",
                            "content": text,
                        },
                    ],
                )
            )

            output = (
                completion
                .choices[0]
                .message
                .content
                or ""
            ).strip()

            return output or None

        except Exception:
            logger.exception(
                "OpenAI Chat Completions translation failed"
            )

            return None

    async def translate_async(
        self,
        text: str,
        source_language: str = "English",
        target_language: str = "Urdu",
        arabic_dialect: str = "MSA",
    ) -> TranslationResult:

        source = self.normalize_language(
            source_language
        )

        target = self.normalize_language(
            target_language
        )

        dialect = self.normalize_dialect(
            arabic_dialect
        )

        clean_text = self.clean_input(text)

        if not clean_text:
            return TranslationResult(
                translated_text="",
                provider="none",
                segments=[],
            )

        if source == target:
            return TranslationResult(
                translated_text=clean_text,
                provider="identity",
                segments=self.split_sentences(
                    clean_text
                ),
            )

        ai_translation = (
            await self._translate_with_ai(
                clean_text,
                source,
                target,
                dialect,
            )
        )

        if ai_translation:
            return TranslationResult(
                translated_text=ai_translation,
                provider="openai",
                segments=self.split_sentences(
                    clean_text
                ),
            )

        return self._translate_offline(
            clean_text,
            source,
            target,
            dialect,
        )