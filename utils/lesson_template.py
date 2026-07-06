"""Yangi dars uchun shablon tana generatorlari (spec 6.3 — matnlar aynan)."""

EQUIPMENT_BASE = ["Kompyuter sinfi", "Proyektor yoki interaktiv doska", "Tarqatma materiallar"]


def objective_for(title: str, grade: int) -> str:
    return (f"O'quvchilarga «{title}» mavzusini amaliy misollar orqali tushuntirish, "
            f"{grade}-sinf dasturiga mos nazariy bilim va amaliy ko'nikmalarni shakllantirish.")


def theory_for(title: str) -> list[str]:
    return [
        f"Dars «{title}» mavzusiga bag'ishlanadi. Kirish qismida o'tgan dars takrorlanadi va yangi mavzu kundalik hayotdagi misollar bilan bog'lab boshlanadi.",
        "Asosiy tushunchalar doskada yoki taqdimotda bosqichma-bosqich ochib beriladi: ta'rif, asosiy xossalar va qo'llanish sohalari. Har bir tushuncha kamida bitta jonli misol bilan mustahkamlanadi.",
        "Namoyish qismida o'qituvchi mavzuga oid amaliy jarayonni proyektor orqali ko'rsatadi, o'quvchilar esa asosiy qadamlarni daftarga qayd etib boradi.",
        "Yakunida savol-javob o'tkaziladi: o'quvchilar mavzu bo'yicha 2–3 nazorat savoliga og'zaki javob beradi va tushunmagan joylari aniqlanadi.",
    ]


def practice_for(title: str) -> list[str]:
    return [
        f"«{title}» mavzusi bo'yicha o'qituvchi ko'rsatgan amallarni kompyuterda mustaqil takrorlash.",
        "Juftlikda ishlash: tarqatma materialdagi topshiriqni bajarish va natijani sinfdoshi bilan solishtirish.",
        "Mustaqil topshiriq: mavzuga oid kichik masalani yechish va natijani o'qituvchiga ko'rsatish.",
    ]


def homework_for(title: str) -> str:
    return (f"«{title}» mavzusi bo'yicha daftardagi konspektni o'qib kelish va mavzuga oid "
            f"3 ta misolni mustaqil bajarish. Qo'shimcha: mavzu yuzasidan bitta savol tayyorlab kelish.")


def outcomes_for(title: str) -> list[str]:
    return [
        f"«{title}» mavzusidagi asosiy tushunchalarni ta'riflay oladi",
        "Mavzuga oid amaliy topshiriqni mustaqil bajara oladi",
        "Olingan bilimni kundalik misollar bilan bog'lay oladi",
    ]
