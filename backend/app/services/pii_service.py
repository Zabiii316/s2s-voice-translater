import re


class PIIService:
    def mask_text(self, text: str) -> dict:
        if not text:
            return {
                "original_text": "",
                "masked_text": "",
                "detected_pii": [],
                "pii_found": False
            }

        masked_text = text
        detected_pii = []

        patterns = {
            "email": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
            "account_number": r"\b(?:my\s+)?(?:account|acct|acc|حساب|اکاؤنٹ)\s*(?:number|no|#|نمبر)?\s*(?:is|ہے|:|-)?\s*[A-Za-z0-9\-]{5,20}\b",
            "national_id": r"\b\d{5}[-\s]?\d{7}[-\s]?\d\b",
            "credit_card": r"\b(?:\d[ -]*?){13,19}\b",
            "phone": r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
        }

        replacement_map = {
            "email": "[MASKED_EMAIL]",
            "account_number": "[MASKED_ACCOUNT_NUMBER]",
            "national_id": "[MASKED_NATIONAL_ID]",
            "credit_card": "[MASKED_PAYMENT_NUMBER]",
            "phone": "[MASKED_PHONE]"
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, masked_text, flags=re.IGNORECASE)

            if matches:
                detected_pii.append(pii_type)
                masked_text = re.sub(
                    pattern,
                    replacement_map[pii_type],
                    masked_text,
                    flags=re.IGNORECASE
                )

        return {
            "original_text": text,
            "masked_text": masked_text,
            "detected_pii": detected_pii,
            "pii_found": len(detected_pii) > 0
        }