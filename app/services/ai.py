from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """Ты — остроумный ведущий рейтинга общественных туалетов.
Пишешь короткие, смешные, слегка абсурдные комментарии на русском языке.
Стиль — как будто это серьёзная премия, но про туалеты.
Без пошлостей, но с иронией. Максимум 3-4 предложения."""


class AIService:

    async def comment_toilet_of_month(
        self,
        address: str,
        name: str | None,
        avg_score: float,
        month: int,
        year: int,
        scores: dict,
    ) -> str:
        """Шуточный комментарий для туалета месяца."""
        month_names = {
            1: "январь", 2: "февраль", 3: "март", 4: "апрель",
            5: "май", 6: "июнь", 7: "июль", 8: "август",
            9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
        }

        title = name or address
        prompt = (
            f"Туалет месяца ({month_names[month]} {year}): «{title}».\n"
            f"Средний балл: {avg_score} из 90.\n"
            f"Оценки: чистота {scores.get('cleanliness')}/25, "
            f"расходники {scores.get('supplies')}/20, "
            f"запах {scores.get('smell')}/20, "
            f"оборудование {scores.get('equipment')}/15, "
            f"приватность {scores.get('privacy')}/5, "
            f"вайб {scores.get('vibe')}/5.\n"
            f"Напиши торжественный шуточный комментарий для объявления победителя."
        )
        return await self._ask(prompt)

    async def comment_top(self, criterion: str, toilets: list[dict]) -> str:
        """Шуточный комментарий для публикации топа."""
        criterion_names = {
            "cleanliness": "чистота",
            "supplies": "расходники",
            "smell": "запах",
            "equipment": "оборудование",
            "privacy": "приватность",
            "vibe": "вайб",
            "total": "общий балл",
        }
        criterion_label = criterion_names.get(criterion, criterion)

        top_lines = "\n".join(
            f"{i+1}. {t['toilet'].name or t['toilet'].address} — {t['avg_score']}"
            for i, t in enumerate(toilets[:3])
        )
        prompt = (
            f"Топ туалетов по критерию «{criterion_label}»:\n{top_lines}\n\n"
            f"Напиши короткий шуточный комментарий к этому топу."
        )
        return await self._ask(prompt)

    async def comment_custom(self, prompt: str) -> str:
        """Свободный запрос — для любых будущих приколов."""
        return await self._ask(prompt)

    async def _ask(self, user_prompt: str) -> str:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
