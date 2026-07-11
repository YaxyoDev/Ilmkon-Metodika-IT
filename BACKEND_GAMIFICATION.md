# Gamifikatsiya — backend uchun talablar

> **Holat (2026-07-11):** 1, 2, 3, 5-bandlar bajarildi ✅ — ball tarixi, o‘quvchi
> jurnal endpointi, avto-nishonlar (`star`, `streak`) va davriy reyting. Endpointlar
> `API_ENDPOINTS.md` 7-bo‘limida hujjatlangan. **4-band (server-side achievements)**
> hali qilinmadi — frontenddagi 11 ta yutuq ta’rifi (`ACHIEVEMENTS` id + shartlari)
> shu repoda yo‘q; ular berilsa qo‘shiladi.

Frontendda reyting sahifasi gamifikatsiya qilindi: unvonlar (Yangi → Bronza →
Kumush → Oltin → Platina → Olmos → Afsona), yutuqlar paneli va animatsiyali
o‘quvchi profili (`StudentProfileModal`). Hozircha **hammasi client-side**
hisoblanadi: unvon — `points` dan, yutuqlar — `points`, `badges` va sinf
jurnali (`GET /api/journal?classId=`) dan. Bu ishlaydi, lekin quyidagi
imkoniyatlar uchun backend kerak.

---

## 1. Ball tarixi (points history) — eng muhimi

Hozir o‘quvchi **qachon va nima uchun** ball olgani hech qayerda saqlanmaydi
(`POST /students/{id}/points` va jurnal qayta hisoblash faqat yakuniy sonni
o‘zgartiradi). Profilda "so‘nggi yutuqlar lentasi"ni ko‘rsatish uchun har bir
ball o‘zgarishini log qilish kerak.

### Yangi endpoint

```
GET /api/students/{id}/points-history?limit=20
```

**Javob 200:**
```json
[
  {
    "id": "pe-1",
    "studentId": "s-5a-1",
    "date": "2026-05-12",
    "delta": 15,
    "source": "journal",          // "journal" | "reward"
    "reason": "Darsda «5» baho",  // reward bo'lsa o'qituvchi tanlagan sabab
    "badgeId": null               // shu event bilan berilgan nishon (bo'lsa)
  }
]
```

- `PUT /api/journal/cell` katak qayta yozilganda eski event o‘chirilib/tuzatilib
  yangisi yoziladi (yakuniy ball bilan mos bo‘lishi shart).
- `POST /students/{id}/points` ham event yozadi (`source: "reward"`).

**Frontendda ishlatilishi:** profil modalida "Ballar tarixi" timeline
(sana + sabab + `+15` chip) qo‘shiladi.

---

## 2. O‘quvchining to‘liq jurnal tarixi

Hozir frontend statistikani `GET /api/journal?classId=` orqali olib,
`studentId` bo‘yicha filtrlaydi. Ikkita muammo:

1. O‘quvchi **boshqa sinfga o‘tkazilsa** (`PATCH /students/{id}` bilan
   `classId` o‘zgarsa) — eski sinfdagi yozuvlari yangi so‘rovga kirmaydi,
   statistika (davomat %, «5» soni, seriya) noldan boshlanadi.
2. Bitta o‘quvchi uchun butun sinf jurnali yuklanadi — ortiqcha trafik.

### Yangi endpoint

```
GET /api/students/{id}/journal
```

**Javob 200:** `JournalEntry[]` — o‘quvchining **barcha** (sinfidan qat'i
nazar) yozuvlari, sana bo‘yicha o‘sish tartibida.

**Frontendda ishlatilishi:** `StudentProfileModal` dagi
`api.getJournal(student.classId)` shu endpointga almashtiriladi
(filtrlash ham olib tashlanadi).

---

## 3. Nishonlarni avtomatik berish

Hozir nishonlar faqat o‘qituvchi qo‘li bilan beriladi. Quyidagi qoidalar
jurnal saqlanganda (`PUT /api/journal/cell`) serverda avtomatik tekshirilsin:

| Nishon | Shart |
|---|---|
| `star` (Yulduzcha) | Birinchi marta «5» baho olganda |
| `streak` (Faol ishtirokchi) | 5 dars ketma-ket `keldi` bo‘lganda |
| `speed` (Tezkor) | (qo‘lda qoladi — o‘qituvchi beradi) |

Avtomatik berilgan nishon `points-history` da ham ko‘rinishi kerak
(`badgeId` maydoni), shunda frontend "Yangi nishon!" animatsiyasini
ko‘rsata oladi.

---

## 4. Yutuqlarni serverda saqlash (achievements)

Frontenddagi 11 ta yutuq (`src/utils/gamification.ts` → `ACHIEVEMENTS`)
har ochilishda qayta hisoblanadi, shuning uchun:

- yutuq **qachon** ochilgani noma'lum (timestamp yo‘q);
- "yangi yutuq ochildi" bildirishnomasini ko‘rsatib bo‘lmaydi;
- top-3 yutug‘i vaqtinchalik (reytingdan tushsa yo‘qoladi).

### Taklif

```
GET /api/students/{id}/achievements
```

**Javob 200:**
```json
[ { "id": "five-stars", "unlockedAt": "2026-05-12" } ]
```

Server jurnal/ball o‘zgarganda shartlarni tekshirib, ochilgan yutuqni
`unlockedAt` bilan saqlaydi (bir marta ochilgan yutuq qaytib yopilmaydi).
Yutuq ta'riflari (nom, tavsif, shart) frontendda qolaveradi — server faqat
`id` + `unlockedAt` saqlasa yetarli.

---

## 5. Davriy reyting (haftalik / oylik / chorak)

Hozir faqat umumiy ball bo‘yicha reyting bor — yangi o‘quvchi hech qachon
eskilarga yeta olmaydi, bu motivatsiyani pasaytiradi. 1-band (points history)
qilinsa, davr kesimida reyting hisoblash oson bo‘ladi:

```
GET /api/leaderboard?period=week|month|quarter|all&classId=...
```

**Javob 200:**
```json
[ { "studentId": "s-5a-1", "points": 42, "position": 1 } ]
```

`points` — tanlangan davrdagi `delta` lar yig‘indisi. Frontendda reyting
sahifasiga davr tanlagichi (tab) qo‘shiladi.

---

## Muhimlik tartibi

1. **Points history** (1-band) — timeline + davriy reyting uchun poydevor
2. **Student journal endpoint** (2-band) — statistika to‘g‘riligi uchun
3. **Avto-nishonlar** (3-band)
4. **Davriy reyting** (5-band)
5. **Server-side achievements** (4-band)

Bularsiz ham frontend to‘liq ishlaydi — mavjud API yetarli, faqat yuqoridagi
cheklovlar bilan.
