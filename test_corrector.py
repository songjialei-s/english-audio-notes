import sys
sys.path.insert(0, '.')
from backend.text_corrector import correct_ocr_text

test = """victoru胜利
triumph/u
lawver
激(当)
proVoke
ignite
provoke
trigger
shove
Vulgar 粗鲁的
Co arse
Co rrel onte
分别的
Yespective
不考虑的
jrrespective
分勃地
Yespe (ti Velu
treasure
诊惜
chexish
Corvect 矫正
rectity"""

print(correct_ocr_text(test))
