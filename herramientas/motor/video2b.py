"""Video 2 v2: scenes timed to the exact spoken word (ElevenLabs Scribe timestamps).
Every scene shows its header at t=0, and each element appears ~0.25 s before its word is spoken.
usage: video2b.py timing.json out.mp4 [first last]"""
import sys
import video2 as V
from video2 import *  # noqa

LEAD = 0.25
CUR = [0.0]


def at(t_abs):
    """absolute narration time -> time relative to current paragraph, slightly early"""
    return max(0.0, t_abs - CUR[0] - LEAD)


def b_title(s):
    it = [El(house_icon(360), RX, 540, 0.1, kind="pop", dur=0.6), kicker("EXPLICADO FÁCIL", L, 330, 0.0)]
    it += lines_els(["¿Por qué no", "puedo comprar", "una casa?"], L, 440, 0.05, size=104, step=0.12)
    return it, "VIVIENDA", None


def b_intro(s):
    it = [kicker("SI TIENES ENTRE 20 Y 40 AÑOS…", L, 280, 0.0)]
    it += [El(T("te has hecho esta pregunta", 50, SOFT, FS), L, 360, at(6.48), anchor="l", kind="left")]
    it += [El(T("Trabajas.", 96, WHITE), L, 480, at(8.96), anchor="l", kind="left")]
    it += [El(T("Ahorras.", 96, WHITE), L, 600, at(10.0), anchor="l", kind="left")]
    it += [El(T("Y comprar sigue pareciendo imposible.", 52, SOFT, FS), L, 720, at(11.72), anchor="l", kind="left")]
    it += [El(T("No es una sensación: los datos lo confirman", 52, YEL, FXB), L, 840, at(14.24), anchor="l", kind="left")]
    it += [El(house_icon(300, col=SOFT), 1560, 520, 0.1, kind="pop")]
    return it, "INTRODUCCIÓN", None


def b_price(s):
    it = [kicker("1 · EL PRECIO", L, 280, 0.0, YEL), El(house_icon(320, col=AMB), 1620, 520, 0.1, kind="pop")]
    it += [El(T("Según el INE, la vivienda subió en un año…", 48, SOFT, FS), L, 370, at(25.6), anchor="l", kind="left")]
    it += [Counter(L, 540, 0, 12.2, at(29.84), dec=1, pre="+", suf=" %", size=260, anchor="l", dur=0.9)]
    it += [El(T("Más de una década subiendo", 52, WHITE, FXB), L, 740, at(36.37), anchor="l", kind="left")]
    return it, "1 · EL PRECIO", "Fuente: INE, Índice de Precios de Vivienda, 2.º trimestre de 2026"


def b_wages(s):
    it = [kicker("2 · TU NÓMINA", L, 230, 0.0, YEL)]
    # quick yearly comparison while he talks about salaries (40.7-47)
    it += [Bars((L, 270, 1180, 560), [("Vivienda", 12.2, "+12,2 %", AMB), ("Sueldos", 5, "≈ +5 %", CYAN)], at(40.72), stagger=4.4, title="Subida en el último año")]
    it += [El(T("Desde 2013:", 50, YEL, FXB), L, 640, at(53.28), anchor="l", kind="left")]
    it += [El(T("vivienda +108 %", 50, AMB, FXB), L + 330, 640, at(55.28), anchor="l", kind="left")]
    it += [El(T("sueldos +30 %", 50, CYAN, FXB), L + 820, 640, at(57.92), anchor="l", kind="left")]
    it += [El(T("100.000 €  →  208.000 €", 52, YEL, FXB), L, 760, at(61.6), anchor="l", kind="left")]
    it += [El(T("Un piso de entonces, hoy", 32, SOFT, FM), L, 820, at(61.6) + 0.2, anchor="l", kind="left")]
    it += [El(T("20.000 €  →  26.000 €", 52, CYAN, FXB), L, 900, at(66.24), anchor="l", kind="left")]
    it += [El(T("Un sueldo de entonces, hoy", 32, SOFT, FM), L, 960, at(66.24) + 0.2, anchor="l", kind="left")]
    it += [El(T("La casa corre.", 70, AMB, FXB), 1560, 700, at(70.2), kind="pop")]
    it += [El(T("Tu sueldo camina.", 70, CYAN, FXB), 1560, 820, at(71.36), kind="pop")]
    return it, "2 · LOS SUELDOS", "Fuentes: INE (precios de vivienda y costes laborales) · informe de CCOO 2013–2026"


def b_effort(s):
    it = [kicker("3 · EL ESFUERZO", L, 260, 0.0, YEL)]
    it += [El(T("¿Qué significa en tu día a día?", 52, WHITE, FXB), L, 350, 0.05, anchor="l", kind="left")]
    it += [El(T("Para comprar una vivienda media hacen falta", 40, SOFT, FS), L, 440, at(78.32), anchor="l", kind="left")]
    it += [Counter(L, 590, 0, 8.4, at(80.8), dec=1, size=230, anchor="l", dur=0.9)]
    it += [El(T("años de sueldo íntegro", 58, WHITE, FXB), L, 760, at(81.84), anchor="l", kind="left")]
    it += [El(T("La cifra más alta desde 2011", 44, SOFT, FS), L, 850, at(87.04), anchor="l", kind="left")]
    it += [El(T("Primera cuota de la hipoteca", 40, SOFT, FS), 1500, 430, at(90.72))]
    it += [Counter(1500, 590, 0, 38, at(93.44), pre="≈ ", suf=" %", size=200, c1=(255, 255, 255), c2=CYAN, dur=0.9)]
    it += [El(T("de lo que gana un hogar", 40, SOFT, FS), 1500, 740, at(94.56))]
    return it, "3 · EL ESFUERZO", "Fuente: Banco de España, indicadores de accesibilidad a la vivienda"


def b_rent(s):
    it = [kicker("4 · EL ALQUILER", L, 260, 0.0, YEL)]
    it += [El(T("«Vale, pues alquilo»", 64, WHITE, FXB), L, 360, 0.05, anchor="l", kind="left")]
    it += [El(T("También está en máximos", 48, AMB, FXB), L, 450, at(101.12), anchor="l", kind="left")]
    it += [Counter(L, 600, 0, 15.1, at(105.52), dec=1, suf=" €/m²", size=160, anchor="l", dur=0.9)]
    it += [El(T("al mes de media en España (idealista)", 38, SOFT, FS), L, 720, at(106.4), anchor="l", kind="left")]
    it += [El(T("Más de 1.200 € al mes por 80 m²", 52, WHITE, FXB), L, 810, at(108.24), anchor="l", kind="left")]
    it += [Bars((1080, 330, 1820, 760), [("Madrid", 21.6, "21,6 €", AMB), ("Baleares", 20.2, "20,2 €", AMB), ("España", 15.1, "15,1 €", CYAN)], at(112.32), title="€/m² al mes, septiembre", stagger=0.3)]
    return it, "4 · EL ALQUILER", "Fuente: idealista, informe de precios de alquiler, septiembre de 2026"


def b_youth(s):
    it = [kicker("5 · LOS JÓVENES", L, 260, 0.0, YEL)]
    it += [El(T("Quien peor lo tiene", 60, WHITE, FXB), L, 350, 0.05, anchor="l", kind="left")]
    it += [Waffle(1520, 540, 15, 0.2, cell=50)]
    it += [Counter(L, 520, 0, 14.5, at(121.44), dec=1, suf=" %", size=200, anchor="l", dur=0.9)]
    it += [El(T("de los jóvenes de 16 a 29 años", 44, SOFT, FS), L, 650, at(123.2), anchor="l", kind="left")]
    it += [El(T("vive fuera de casa de sus padres", 50, WHITE, FXB), L, 720, at(126.16), anchor="l", kind="left")]
    it += [El(T("Nos vamos con casi 30 años", 44, SOFT, FS), L, 820, at(131.04), anchor="l", kind="left")]
    it += [El(T("Alquilar solo: casi el 100 % del sueldo", 44, AMB, FXB), L, 900, at(138.0), anchor="l", kind="left")]
    return it, "5 · LOS JÓVENES", "Fuente: Consejo de la Juventud de España, Observatorio de Emancipación"


def b_supply(s):
    it, chip, src = V.sc_supply([0.0, at(151.04) + LEAD, at(151.04) + LEAD])
    # replace the delayed headline: show question first, then the answer on "oferta"
    it = [kicker("6 · ¿POR QUÉ PASA?", L, 330, 0.0)] + [e for e in it[1:]]
    for e in it:
        if isinstance(e, El) and e.t0 < 0.5 and e.anchor == "l" and e is not it[0]:
            e.t0 = at(149.28)
    return it, chip, src


def b_deficit(s):
    it = [kicker("ESPAÑA, 2025 · BANCO DE ESPAÑA", L, 250, 0.0, YEL)]
    it += [Bars((L, 290, 1080, 640), [("Hogares", 240, "240.000", AMB), ("Viviendas", 92, "92.000", CYAN)], at(159.28), stagger=5.2, title="Hogares nuevos y viviendas terminadas")]
    it += [El(T("Ni la mitad", 60, YEL, FXB), L, 720, at(166.4), anchor="l", kind="left")]
    it += [kicker("FALTAN (2021–2025)", 1500, 300, at(170.72), YEL, anchor="c")]
    it += [Counter(1500, 420, 0, 750000, at(174.4), size=150, dur=1.0)]
    it += [El(T("viviendas", 52, WHITE, FXB), 1500, 530, at(175.92))]
    provs = [("Madrid", 180.64), ("Barcelona", 181.36), ("Valencia", 182.24), ("Alicante", 183.04), ("Málaga", 184.0), ("Murcia", 184.72)]
    for i, (p, tw) in enumerate(provs):
        x = 1500 - 270 + (i % 3) * 270
        y = 680 + (i // 3) * 90
        pill = Image.new("RGBA", (250, 70), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle([0, 0, 249, 69], radius=35, fill=(255, 255, 255, 18), outline=(255, 255, 255, 60), width=2)
        pd.text((125, 35), p, font=F(FB, 34), fill=WHITE + (255,), anchor="mm")
        it.append(El(pill, x, y, at(tw), kind="pop"))
    it.append(El(T("La mitad del déficit, en 6 provincias", 34, SOFT, FS), 1500, 880, at(177.2)))
    return it, "6 · POR QUÉ PASA", "Fuente: Banco de España (estimación de déficit 2021–2025)"


def b_causes(s):
    it = [kicker("7 · ¿POR QUÉ NO SE CONSTRUYE MÁS?", 960, 250, 0.0, YEL, anchor="c")]
    cards = [("Falta suelo", "listo para edificar", ic_land, 189.92), ("Trámites", "urbanísticos lentos", ic_doc, 192.24),
             ("Falta mano", "de obra", ic_worker, 194.64), ("Turísticos", "e inversores", ic_suitcase, 202.24)]
    for i, (a, b, ic, tw) in enumerate(cards):
        it.append(El(card_icon(a, b, ic), 330 + i * 420, 560, at(tw), kind="pop"))
    return it, "7 · LAS CAUSAS", "Fuente: Banco de España, Informe Anual"


def b_measures(s):
    it = [kicker("8 · ¿QUÉ SE ESTÁ HACIENDO?", L, 260, 0.0, YEL)]
    it += [El(T("Decreto de vivienda · octubre 2026", 40, SOFT, FS), L, 330, at(211.44), anchor="l", kind="left")]
    items = [("Alquiler: subida máxima del 2 % hasta 2027", 216.48), ("Límites a los pisos turísticos", 223.2),
             ("Freno a grandes compradores y fondos", 225.52), ("Más dinero para vivienda pública", 230.24),
             ("Plan Estatal: 7.000 M€ hasta 2030", 233.14)]
    for i, (txt, tw) in enumerate(items):
        row = Image.new("RGBA", (1500, 90), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        rd.ellipse([0, 15, 60, 75], fill=GREEN + (255,))
        rd.line([16, 45, 27, 57, 46, 32], fill=INK + (255,), width=7)
        rd.text((90, 45), txt, font=F(FXB, 48), fill=WHITE + (255,), anchor="lm")
        it.append(El(row, L, 420 + i * 110, at(tw), anchor="l", kind="left"))
    return it, "8 · QUÉ SE HACE", "Fuentes: BOE (decreto de 7/10/2026), Civio, Ministerio de Vivienda"


def b_outlook(s):
    it = [El(T("¿Bajarán los precios?", 100, WHITE, FXB), 960, 400, 0.0, kind="pop")]
    it += [El(T("A corto plazo, la mayoría de expertos cree que no", 50, SOFT, FS), 960, 540, at(240.34))]
    it += [El(T("Mientras falten casas, la presión seguirá", 44, SOFT, FS), 960, 620, at(243.75))]
    it += [El(A.pill_word("construir más", F(FBK, 110)), 960, 790, at(247.6), kind="pop")]
    return it, "9 · ¿Y AHORA?", None


def b_summary(s):
    it = [kicker("RESUMEN", L, 260, 0.0, YEL)]
    pts = [("La vivienda sube más rápido que los sueldos", 252.13), ("Comprar exige más de 8 años de salario", 255.51),
           ("El alquiler está en máximos", 258.87), ("En el fondo: faltan casas", 261.23)]
    for i, (txt, tw) in enumerate(pts):
        row = Image.new("RGBA", (1600, 100), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        rd.rounded_rectangle([0, 18, 64, 82], radius=18, fill=YEL + (255,))
        rd.text((32, 50), str(i + 1), font=F(FBK, 40), fill=INK + (255,), anchor="mm")
        rd.text((96, 50), txt, font=F(FXB, 56), fill=WHITE + (255,), anchor="lm")
        it.append(El(row, L, 400 + i * 130, at(tw), anchor="l", kind="left"))
    return it, "RESUMEN", None


def b_cta(s):
    it, chip, src = V.sc_cta([0.0, at(267.01) + LEAD, at(271.5) + LEAD])
    return it, chip, src


V.SCENES[:] = [b_title, b_intro, b_price, b_wages, b_effort, b_rent, b_youth, b_supply, b_deficit, b_causes, b_measures, b_outlook, b_summary, b_cta]

# wrap scene builders so `at()` knows the paragraph start
_orig = list(V.SCENES)
import json as _json
_tm = _json.load(open(sys.argv[1]))
_starts = [p[0] for p in _tm["pars"]]
_starts[0] = 0.0


def _wrap(fn, i):
    def g(s):
        CUR[0] = _starts[i]
        return fn(s)
    return g


V.SCENES[:] = [_wrap(f, i) for i, f in enumerate(_orig)]

if __name__ == "__main__":
    V.main()
