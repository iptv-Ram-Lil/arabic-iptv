#!/usr/bin/env python3
"""Build an automatically updated, country-first world IPTV M3U.

Source: https://iptv-org.github.io/iptv/index.m3u
Output: arabic-tv.m3u (keeps the existing TV playlist URL unchanged)
Requires only Python's standard library.

To populate Favorites, add exact tvg-id values to FAVORITE_IDS or exact
channel names to FAVORITE_NAMES. Favorites are duplicated intentionally:
channels remain in their country group too.
"""

from collections import defaultdict
from pathlib import Path
import re
import time
import urllib.request

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT = Path("arabic-tv.m3u")

# Fixed priority: Syria, MBC, Arabic news, Arabic sports/beIN,
# remaining Arab countries, then foreign countries (one group per country).
ARAB_COUNTRIES = [
    ("SY", "سوريا"), ("LB", "لبنان"), ("IQ", "العراق"),
    ("PS", "فلسطين"), ("JO", "الأردن"), ("EG", "مصر"),
    ("SA", "السعودية"), ("AE", "الإمارات"), ("KW", "الكويت"),
    ("QA", "قطر"), ("BH", "البحرين"), ("OM", "عُمان"),
    ("YE", "اليمن"), ("SD", "السودان"), ("LY", "ليبيا"),
    ("TN", "تونس"), ("DZ", "الجزائر"), ("MA", "المغرب"),
    ("MR", "موريتانيا"), ("SO", "الصومال"), ("DJ", "جيبوتي"),
    ("KM", "جزر القمر"),
]
ARAB_CODES = {code for code, _ in ARAB_COUNTRIES}
FOREIGN_NAMES = {
    'AC': 'جزيرة أسينشيون',
    'AD': 'أندورا',
    'AE': 'الإمارات العربية المتحدة',
    'AF': 'أفغانستان',
    'AG': 'أنتيغوا وبربودا',
    'AI': 'أنغويلا',
    'AL': 'ألبانيا',
    'AM': 'أرمينيا',
    'AO': 'أنغولا',
    'AQ': 'أنتاركتيكا',
    'AR': 'الأرجنتين',
    'AS': 'ساموا الأمريكية',
    'AT': 'النمسا',
    'AU': 'أستراليا',
    'AW': 'أروبا',
    'AX': 'جزر آلاند',
    'AZ': 'أذربيجان',
    'BA': 'البوسنة والهرسك',
    'BB': 'بربادوس',
    'BD': 'بنغلاديش',
    'BE': 'بلجيكا',
    'BF': 'بوركينا فاسو',
    'BG': 'بلغاريا',
    'BH': 'البحرين',
    'BI': 'بوروندي',
    'BJ': 'بنين',
    'BL': 'سان بارتليمي',
    'BM': 'برمودا',
    'BN': 'بروناي',
    'BO': 'بوليفيا',
    'BQ': 'هولندا الكاريبية',
    'BR': 'البرازيل',
    'BS': 'جزر البهاما',
    'BT': 'بوتان',
    'BV': 'جزيرة بوفيه',
    'BW': 'بوتسوانا',
    'BY': 'بيلاروس',
    'BZ': 'بليز',
    'CA': 'كندا',
    'CC': 'جزر كوكوس (كيلينغ)',
    'CD': 'الكونغو - كينشاسا',
    'CF': 'جمهورية أفريقيا الوسطى',
    'CG': 'الكونغو - برازافيل',
    'CH': 'سويسرا',
    'CI': 'ساحل العاج',
    'CK': 'جزر كوك',
    'CL': 'تشيلي',
    'CM': 'الكاميرون',
    'CN': 'الصين',
    'CO': 'كولومبيا',
    'CP': 'جزيرة كليبيرتون',
    'CR': 'كوستاريكا',
    'CU': 'كوبا',
    'CV': 'الرأس الأخضر',
    'CW': 'كوراساو',
    'CX': 'جزيرة كريسماس',
    'CY': 'قبرص',
    'CZ': 'التشيك',
    'DE': 'ألمانيا',
    'DG': 'دييغو غارسيا',
    'DJ': 'جيبوتي',
    'DK': 'الدانمرك',
    'DM': 'دومينيكا',
    'DO': 'جمهورية الدومينيكان',
    'DZ': 'الجزائر',
    'EA': 'سيوتا وميليلا',
    'EC': 'الإكوادور',
    'EE': 'إستونيا',
    'EG': 'مصر',
    'EH': 'الصحراء الغربية',
    'ER': 'إريتريا',
    'ES': 'إسبانيا',
    'ET': 'إثيوبيا',
    'EU': 'الاتحاد الأوروبي',
    'EZ': 'منطقة اليورو',
    'FI': 'فنلندا',
    'FJ': 'فيجي',
    'FK': 'جزر فوكلاند',
    'FM': 'ميكرونيزيا',
    'FO': 'جزر فارو',
    'FR': 'فرنسا',
    'GA': 'الغابون',
    'GB': 'المملكة المتحدة',
    'GD': 'غرينادا',
    'GE': 'جورجيا',
    'GF': 'غويانا الفرنسية',
    'GG': 'غيرنزي',
    'GH': 'غانا',
    'GI': 'جبل طارق',
    'GL': 'غرينلاند',
    'GM': 'غامبيا',
    'GN': 'غينيا',
    'GP': 'غوادلوب',
    'GQ': 'غينيا الاستوائية',
    'GR': 'اليونان',
    'GS': 'جورجيا الجنوبية وجزر ساندويتش الجنوبية',
    'GT': 'غواتيمالا',
    'GU': 'غوام',
    'GW': 'غينيا بيساو',
    'GY': 'غيانا',
    'HK': 'هونغ كونغ الصينية (منطقة إدارية خاصة)',
    'HM': 'جزيرة هيرد وجزر ماكدونالد',
    'HN': 'هندوراس',
    'HR': 'كرواتيا',
    'HT': 'هايتي',
    'HU': 'هنغاريا',
    'IC': 'جزر الكناري',
    'ID': 'إندونيسيا',
    'IE': 'أيرلندا',
    'IL': 'إسرائيل',
    'IM': 'جزيرة مان',
    'IN': 'الهند',
    'IO': 'الإقليم البريطاني في المحيط الهندي',
    'IQ': 'العراق',
    'IR': 'إيران',
    'IS': 'آيسلندا',
    'IT': 'إيطاليا',
    'JE': 'جيرسي',
    'JM': 'جامايكا',
    'JO': 'الأردن',
    'JP': 'اليابان',
    'KE': 'كينيا',
    'KG': 'قيرغيزستان',
    'KH': 'كمبوديا',
    'KI': 'كيريباتي',
    'KM': 'جزر القمر',
    'KN': 'سانت كيتس ونيفيس',
    'KP': 'كوريا الشمالية',
    'KR': 'كوريا الجنوبية',
    'KW': 'الكويت',
    'KY': 'جزر كايمان',
    'KZ': 'كازاخستان',
    'LA': 'لاوس',
    'LB': 'لبنان',
    'LC': 'سانت لوسيا',
    'LI': 'ليختنشتاين',
    'LK': 'سريلانكا',
    'LR': 'ليبيريا',
    'LS': 'ليسوتو',
    'LT': 'ليتوانيا',
    'LU': 'لوكسمبورغ',
    'LV': 'لاتفيا',
    'LY': 'ليبيا',
    'MA': 'المغرب',
    'MC': 'موناكو',
    'MD': 'مولدوفا',
    'ME': 'الجبل الأسود',
    'MF': 'سان مارتن',
    'MG': 'مدغشقر',
    'MH': 'جزر مارشال',
    'MK': 'مقدونيا الشمالية',
    'ML': 'مالي',
    'MM': 'ميانمار (بورما)',
    'MN': 'منغوليا',
    'MO': 'منطقة ماكاو الإدارية الخاصة',
    'MP': 'جزر ماريانا الشمالية',
    'MQ': 'جزر المارتينيك',
    'MR': 'موريتانيا',
    'MS': 'مونتسرات',
    'MT': 'مالطا',
    'MU': 'موريشيوس',
    'MV': 'جزر المالديف',
    'MW': 'ملاوي',
    'MX': 'المكسيك',
    'MY': 'ماليزيا',
    'MZ': 'موزمبيق',
    'NA': 'ناميبيا',
    'NC': 'كاليدونيا الجديدة',
    'NE': 'النيجر',
    'NF': 'جزيرة نورفولك',
    'NG': 'نيجيريا',
    'NI': 'نيكاراغوا',
    'NL': 'هولندا',
    'NO': 'النرويج',
    'NP': 'نيبال',
    'NR': 'ناورو',
    'NU': 'نيوي',
    'NZ': 'نيوزيلندا',
    'OM': 'عُمان',
    'PA': 'بنما',
    'PE': 'بيرو',
    'PF': 'بولينيزيا الفرنسية',
    'PG': 'بابوا غينيا الجديدة',
    'PH': 'الفلبين',
    'PK': 'باكستان',
    'PL': 'بولندا',
    'PM': 'سان بيير ومكويلون',
    'PN': 'جزر بيتكيرن',
    'PR': 'بورتوريكو',
    'PS': 'الأراضي الفلسطينية',
    'PT': 'البرتغال',
    'PW': 'بالاو',
    'PY': 'باراغواي',
    'QA': 'قطر',
    'QO': 'أوقيانوسيا النائية',
    'RE': 'روينيون',
    'RO': 'رومانيا',
    'RS': 'صربيا',
    'RU': 'روسيا',
    'RW': 'رواندا',
    'SA': 'المملكة العربية السعودية',
    'SB': 'جزر سليمان',
    'SC': 'سيشل',
    'SD': 'السودان',
    'SE': 'السويد',
    'SG': 'سنغافورة',
    'SH': 'سانت هيلينا',
    'SI': 'سلوفينيا',
    'SJ': 'سفالبارد وجان ماين',
    'SK': 'سلوفاكيا',
    'SL': 'سيراليون',
    'SM': 'سان مارينو',
    'SN': 'السنغال',
    'SO': 'الصومال',
    'SR': 'سورينام',
    'SS': 'جنوب السودان',
    'ST': 'ساو تومي وبرينسيبي',
    'SV': 'السلفادور',
    'SX': 'سانت مارتن',
    'SY': 'سوريا',
    'SZ': 'إسواتيني',
    'TA': 'تريستان دا كونا',
    'TC': 'جزر توركس وكايكوس',
    'TD': 'تشاد',
    'TF': 'الأقاليم الجنوبية الفرنسية',
    'TG': 'توغو',
    'TH': 'تايلاند',
    'TJ': 'طاجيكستان',
    'TK': 'توكيلاو',
    'TL': 'تيمور - ليشتي',
    'TM': 'تركمانستان',
    'TN': 'تونس',
    'TO': 'تونغا',
    'TR': 'تركيا',
    'TT': 'ترينيداد وتوباغو',
    'TV': 'توفالو',
    'TW': 'تايوان',
    'TZ': 'تنزانيا',
    'UA': 'أوكرانيا',
    'UG': 'أوغندا',
    'UM': 'جزر الولايات المتحدة النائية',
    'UN': 'الأمم المتحدة',
    'US': 'الولايات المتحدة',
    'UY': 'أورغواي',
    'UZ': 'أوزبكستان',
    'VA': 'الفاتيكان',
    'VC': 'سانت فنسنت وجزر غرينادين',
    'VE': 'فنزويلا',
    'VG': 'جزر فيرجن البريطانية',
    'VI': 'جزر فيرجن الأمريكية',
    'VN': 'فيتنام',
    'VU': 'فانواتو',
    'WF': 'جزر والس وفوتونا',
    'WS': 'ساموا',
    'XA': 'لكنات تجريبية غير أصلية',
    'XB': 'لكنات تجريبية ثنائية الاتجاه',
    'XK': 'كوسوفو',
    'YE': 'اليمن',
    'YT': 'مايوت',
    'ZA': 'جنوب أفريقيا',
    'ZM': 'زامبيا',
    'ZW': 'زيمبابوي',
    'ZZ': 'منطقة غير معروفة',
}
# Optional favorites: exact channel ID or exact displayed name.
FAVORITE_IDS = set()
FAVORITE_NAMES = set()

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
GROUP_RE = re.compile(r'\s+group-title="[^"]*"')
DURATION_RE = re.compile(r'^(#EXTINF:\s*-?\d+(?:\.\d+)?)')
NEWS_RE = re.compile(r'(news|أخبار|اخبار|الحدث|الجزيرة|العربية|الميادين|الشرق|سكاي نيوز|الاخبارية)', re.I)
SPORTS_RE = re.compile(r'(sports?|رياضة|رياضي|كرة القدم|bein)', re.I)
MBC_RE = re.compile(r'(?<![a-z0-9])mbc(?:[0-9]|\b|\s|[-_])', re.I)
BEIN_RE = re.compile(r'bein\s*[-_]?\s*sports?', re.I)
ARABIC_RE = re.compile(r'[\u0600-\u06ff]')


def download():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; IPTVPlaylistBuilder/2.0)"}
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(SOURCE, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as response:
                text = response.read().decode("utf-8-sig", errors="replace")
            if not text.lstrip().startswith("#EXTM3U"):
                raise ValueError("Source did not return an M3U playlist")
            return text
        except Exception as exc:
            last_error = exc
            print(f"Download attempt {attempt + 1} failed: {exc}")
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Could not download source; old playlist preserved: {last_error}")


def entries(text):
    pending = None
    extras = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#EXTINF:"):
            pending = line
            extras = []
        elif pending is not None and line.startswith("#"):
            extras.append(line)
        elif pending is not None and line and not line.startswith("#"):
            if line.startswith(("http://", "https://")):
                yield pending, extras, line
            pending = None
            extras = []


def attributes(extinf):
    # Only parse attributes before the comma separating metadata and channel name.
    metadata = extinf.split(",", 1)[0]
    return dict(ATTR_RE.findall(metadata))


def channel_name(extinf):
    return extinf.split(",", 1)[1].strip() if "," in extinf else ""


def country_code(attrs):
    # iptv-org may expose country via tvg-country or the tvg-id suffix.
    country = attrs.get("tvg-country", "").split(";", 1)[0].strip().upper()
    if re.fullmatch(r"[A-Z]{2}", country):
        return country
    channel_id = attrs.get("tvg-id", "")
    match = re.search(r"\.([a-z]{2})(?:@[^.]*)?$", channel_id, re.I)
    return match.group(1).upper() if match else "ZZ"


def rewrite_group(extinf, group):
    if '"' in group or "\n" in group:
        raise ValueError("Invalid group name")
    metadata, sep, name = extinf.partition(",")
    metadata = GROUP_RE.sub("", metadata)
    match = DURATION_RE.match(metadata)
    if not match:
        raise ValueError(f"Invalid EXTINF duration: {extinf[:100]}")
    prefix = match.group(1)
    rest = metadata[match.end():]
    # EXTINF duration must appear before any attributes.
    return f'{prefix}{rest} group-title="{group}"{sep}{name}'


def add(out, group, item):
    extinf, extras, url = item
    out.append(rewrite_group(extinf, group))
    out.extend(extras)
    out.append(url)


def main():
    raw = download()
    groups = defaultdict(list)
    seen = set()
    favorites = []
    favorite_ids = {x.casefold() for x in FAVORITE_IDS}
    favorite_names = {x.casefold() for x in FAVORITE_NAMES}
    count = 0

    for item in entries(raw):
        extinf, _, url = item
        if url in seen:
            continue
        seen.add(url)
        attrs = attributes(extinf)
        code = country_code(attrs)
        name = channel_name(extinf)
        tvg_id = attrs.get("tvg-id", "")
        source_group = attrs.get("group-title", "")
        combined = " ".join((name, tvg_id, source_group))
        is_arabic = code in ARAB_CODES or bool(ARABIC_RE.search(name))
        if code == "SY":
            group = "01 | 🇸🇾 سوريا"
        elif MBC_RE.search(combined):
            group = "02 | 📺 جميع قنوات MBC"
        elif is_arabic and NEWS_RE.search(combined):
            group = "03 | 📰 الأخبار العربية"
        elif BEIN_RE.search(combined) or (is_arabic and SPORTS_RE.search(combined)):
            group = "04 | ⚽ الرياضة العربية وbeIN Sports"
        elif code in ARAB_CODES:
            group = "ARAB:" + code
        else:
            group = "FOREIGN:" + code
        groups[group].append(item)
        count += 1
        if tvg_id.casefold() in favorite_ids or name.casefold() in favorite_names:
            favorites.append(item)

    if count < 100:
        raise RuntimeError(f"Only {count} streams found; refusing to overwrite old playlist")

    output = ["#EXTM3U"]
    group_count = 0

    def emit(group, items):
        nonlocal group_count
        if not items:
            return
        for item in items:
            add(output, group, item)
        group_count += 1

    # Syria first; all MBC; Arabic news; Arabic sports and beIN Sports.
    for group in (
        "01 | 🇸🇾 سوريا",
        "02 | 📺 جميع قنوات MBC",
        "03 | 📰 الأخبار العربية",
        "04 | ⚽ الرياضة العربية وbeIN Sports",
    ):
        emit(group, groups.pop(group, []))

    # Optional favorites collection (duplicates intentional).
    emit("05 | ⭐ المفضلة", favorites)

    # Remaining Arab countries, one group per country, in the chosen order.
    for number, (code, name) in enumerate(ARAB_COUNTRIES[1:], start=6):
        emit(f"{number:02d} | 🌙 {name}", groups.pop("ARAB:" + code, []))

    # Every foreign country gets its own named group, sorted by Arabic name.
    foreign = []
    for key, items in groups.items():
        if key.startswith("FOREIGN:"):
            code = key.split(":", 1)[1]
            name = FOREIGN_NAMES.get(code, "بلد غير محدد" if code == "ZZ" else code)
            foreign.append((name, code, items))
        elif key.startswith("ARAB:"):
            # Safety fallback for unexpected Arabic country codes.
            foreign.append((key, key, items))
    for name, code, items in sorted(foreign, key=lambda x: (x[0], x[1])):
        emit(f"🌍 {name} ({code})", items)

    content = "\n".join(output) + "\n"
    if not content.startswith("#EXTM3U\n"):
        raise RuntimeError("Invalid generated M3U header")
    temp = OUTPUT.with_suffix(".m3u.tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(OUTPUT)
    print(f"Success: {count} unique streams, {group_count} groups, "
          f"{len(favorites)} favorites. Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
