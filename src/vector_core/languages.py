"""Curriculum metadata, never a claim of linguistic competence."""
from vector_core.persistence import put

# Explicit varieties share neither an automatic translation nor grammar model.
CURRICULUM=[
('en','English',['Latn']),('cmn','Mandarin Chinese',['Hans','Hant']),('hi','Hindi',['Deva']),('es','Spanish',['Latn']),
('ar','Arabic',['Arab']),('fr','French',['Latn']),('bn','Bengali',['Beng']),('pt','Portuguese',['Latn']),
('id','Indonesian',['Latn']),('ur','Urdu',['Arab']),('ru','Russian',['Cyrl']),('de','German',['Latn']),
('ja','Japanese',['Hani','Hira','Kana']),('pa','Punjabi',['Guru','Arab']),('mr','Marathi',['Deva']),('te','Telugu',['Telu']),
('tr','Turkish',['Latn']),('ta','Tamil',['Taml']),('vi','Vietnamese',['Latn']),('ko','Korean',['Hang','Hani']),
('sw','Swahili',['Latn']),('fa','Persian',['Arab']),('th','Thai',['Thai']),('it','Italian',['Latn']),
('gu','Gujarati',['Gujr']),('ha','Hausa',['Latn','Arab']),('yue','Cantonese (Yue Chinese)',['Hant','Hans']),
('jv','Javanese',['Latn','Java']),('pl','Polish',['Latn']),('uk','Ukrainian',['Cyrl']),('ml','Malayalam',['Mlym']),
('kn','Kannada',['Knda']),('am','Amharic',['Ethi']),('my','Burmese',['Mymr']),('tl','Tagalog',['Latn']),
('nl','Dutch',['Latn']),('el','Greek (Modern)',['Grek']),('he','Hebrew (Modern)',['Hebr']),('ro','Romanian',['Latn']),
('yo','Yoruba',['Latn']),('la-x-classic','Classical Latin',['Latn']),('grc','Ancient Greek',['Grek']),('hbo','Biblical Hebrew',['Hebr'])]
ENGLISH_DOMAINS=['phonetics','phonology','morphology','syntax','semantics','pragmatics','discourse','etymology','historical English','dialects','registers','idioms','figurative language','rhetoric','poetry','narrative','persuasion','argumentation','formal writing','informal writing','technical communication']
VARIETIES={'ar':['Modern Standard Arabic','Egyptian Arabic','Levantine Arabic','other varieties require explicit identification'],
'cmn':['Mandarin; Simplified/Traditional script distinction'],'yue':['Yue/Cantonese; not interchangeable with Mandarin'],
'pa':['Gurmukhi writing','Shahmukhi writing'],'en':['Variety/register must be specified when relevant'],
'la-x-classic':['Classical Latin; other Latin periods separate'],'grc':['Attic','Ionic','Koine; period must be specified'],'hbo':['Biblical Hebrew; Masoretic pointing and textual witnesses require provenance']}

def seed(memory):
    for code,name,scripts in CURRICULUM:
        if not memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='languages' AND record_key=?",(code,)).fetchone():
            put(memory,'languages',code,{'id':code,'name':name,'scripts':scripts,'varieties':VARIETIES.get(code,['Variety/region not inferred']),
                'historical':code in {'la-x-classic','grc','hbo'},'coverage':'curriculum-only; proficiency unqualified',
                'domains':ENGLISH_DOMAINS if code=='en' else ['source-attested vocabulary','grammar','usage','ambiguity'],
                'provenance':'Developer-authored curriculum selection; names/codes are identifiers, not a linguistic dataset.'})
    return {'curriculum_languages':43,'qualified_languages':0}

def identify(text):
    import unicodedata
    counts={}
    names={'LATIN':'Latn','GREEK':'Grek','HEBREW':'Hebr','ARABIC':'Arab','CYRILLIC':'Cyrl','CJK':'Hani','HIRAGANA':'Hira','KATAKANA':'Kana','HANGUL':'Hang','DEVANAGARI':'Deva','BENGALI':'Beng','TAMIL':'Taml','TELUGU':'Telu','THAI':'Thai','ETHIOPIC':'Ethi','MYANMAR':'Mymr','GURMUKHI':'Guru','GUJARATI':'Gujr','KANNADA':'Knda','MALAYALAM':'Mlym'}
    for char in text[:20000]:
        if not char.isalpha():continue
        name=unicodedata.name(char,'');script=next((value for key,value in names.items() if key in name),'Other')
        counts[script]=counts.get(script,0)+1
    return {'script_counts':counts,'language':'und','uncertainty':'Unicode script evidence does not identify a language, dialect or historical period.'}
