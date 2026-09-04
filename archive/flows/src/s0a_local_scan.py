#!/usr/bin/env python3
# S0a 本地全词表扫描(零token): 语料txt × 词表 → 命中CSV(公司,词,逐字引语,文件)
import re,csv,glob,os,subprocess,sys
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORDS=[w.strip() for w in """InP衬底,磷化铟衬底,三甲基铟,磷烷,阵列波导光栅,AWG,PLC分路器,陶瓷插芯,陶瓷管壳,光隔离器,隔离器,FAU,光纤阵列,采样示波器,时钟恢复,CPO耦合,TOSA,ROSA,BOSA,激光驱动芯片,跨阻放大,TIA,CDR芯片,光模块PCB""".split(',')]
CORPUS=sys.argv[1] if len(sys.argv)>1 else f'{ROOT}/flows/input/corpus-v1'
out=csv.writer(open(f'{ROOT}/flows/out/s0a-local-hits.csv','w',encoding='utf-8-sig',newline=''))
out.writerow(['文件','词','引语(±40字)'])
n=0
for pdf in glob.glob(f'{CORPUS}/**/*.pdf',recursive=True):
    txt=pdf+'.txt'
    if not os.path.exists(txt):
        subprocess.run(['pdftotext','-layout',pdf,txt],capture_output=True)
    try: t=re.sub(r'\s+','',open(txt,encoding='utf-8',errors='ignore').read())
    except: continue
    for w in WORDS:
        for m in list(re.finditer(re.escape(w),t))[:3]:
            out.writerow([os.path.basename(pdf),w,t[max(0,m.start()-40):m.end()+40]]); n+=1
print(f'HITS={n}')
