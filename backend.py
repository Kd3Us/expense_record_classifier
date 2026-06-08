import os
import base64
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class ExpenseAgent:
    """Agent de vision qui extrait les champs d'une note de frais."""

    MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    EXPECTED_FIELDS = [
        "type_document", "fournisseur", "date", "montant_ttc",
        "tva", "devise", "description", "confiance"
    ]

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY manquante dans le .env")

        self.client = Groq(api_key=api_key)

        base_dir = os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(base_dir, "context.txt"), "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

        with open(os.path.join(base_dir, "prompt.txt"), "r", encoding="utf-8") as f:
            self.user_prompt = f.read().strip()

    def extract_from_bytes(self, image_bytes: bytes, media_type: str) -> dict:
        """
        Envoie l'image au modèle de vision et retourne un dict avec les champs extraits.

        Args:
            image_bytes: contenu brut de l'image
            media_type: type MIME (ex: "image/jpeg")

        Returns:
            dict avec les 8 champs attendus, None si un champ est absent
        """
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model=self.MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)

        for field in self.EXPECTED_FIELDS:
            if field not in data:
                data[field] = None

        return data


if __name__ == "__main__":
    import sys
    import pprint

    if len(sys.argv) < 2:
        print("Usage: python backend.py <chemin_vers_image>")
        sys.exit(1)

    image_path = sys.argv[1]

    ext = image_path.rsplit(".", 1)[-1].lower()
    media_type_map = {
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "png":  "image/png",
        "webp": "image/webp"
    }
    media_type = media_type_map.get(ext)
    if not media_type:
        print(f"Extension non supportée : {ext}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    agent = ExpenseAgent()
    result = agent.extract_from_bytes(image_bytes, media_type)

    print("\n--- Résultat extraction ---")
    pprint.pprint(result)