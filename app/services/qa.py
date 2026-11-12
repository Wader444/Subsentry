"""Q&A — answers ONLY from the user's own subscription records.

The refusal sentence below is exact and must stay verbatim: the agent
never invents answers outside the stored records.
"""
import logging

from sqlalchemy.orm import Session

from app import repositories
from app.llm import generate
from app.models import User
from app.services.proposals import propose

logger = logging.getLogger(__name__)

REFUSAL = (
    "I can only answer from your subscription records — ask me what you're "
    "paying for that you don't use, or how much your subscriptions cost in total."
)


def ask(db: Session, user: User, question: str, client=None):
    subs = repositories.list_subscriptions(db, user.id)
    lowered = (question or "").lower()
    answer: str

    if not subs:
        answer = "You have no subscriptions saved yet."
    elif any(word in lowered for word in ("don't use", "not use", "unused", "wast")):
        if client is not None:
            proposal = propose(db, user, client)
            flagged = proposal["flagged"]
            monthly = proposal["monthly_saving_usd"]
            annual = proposal["annual_saving_usd"]
        else:
            from app.scoring import should_flag, waste_score

            flagged = []
            for sub in subs:
                price = sub.price_monthly_usd or 0.0
                days = sub.last_used_days_ago or 0
                if should_flag(price, days):
                    flagged.append({
                        "merchant": sub.merchant,
                        "price_monthly_usd": price,
                        "last_used_days_ago": days,
                        "waste_score": waste_score(price, days),
                    })
            monthly = round(sum(f["price_monthly_usd"] for f in flagged), 2)
            annual = round(monthly * 12, 2)
        if not flagged:
            answer = "You're using all of your subscriptions — nothing looks wasted."
        else:
            names = ", ".join(
                f"{f['merchant']} (${f['price_monthly_usd']:.2f}/month)"
                for f in flagged
            )
            answer = (
                f"You're paying for {len(flagged)} subscription(s) you don't use: "
                f"{names}. Cancelling them would save ${monthly:.2f}/month "
                f"(${annual:.2f}/year)."
            )
    elif any(word in lowered for word in ("how many", "total", "how much", "cost")):
        total = round(sum(sub.price_monthly_usd or 0.0 for sub in subs), 2)
        active = [sub for sub in subs if sub.status == "ACTIVE"]
        answer = (
            f"You have {len(subs)} subscription(s) saved "
            f"({len(active)} active), costing ${total:.2f}/month in total."
        )
    else:
        answer = REFUSAL

    if answer != REFUSAL:
        # LLM may rephrase wording only; template provider returns it unchanged.
        answer = generate(answer)
    repositories.log_audit(
        db, user.id, "ASK", None, None, f"q={question!r}",
    )
    return {"question": question, "answer": answer}
