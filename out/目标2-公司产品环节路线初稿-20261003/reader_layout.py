"""Present the existing research draft as a reader, with an on-demand evidence library."""
import html,re,json
from pathlib import Path
from public_text import public_html
B=Path(__file__).resolve().parent
esc=lambda x:html.escape(str(x),quote=True)
def lower_headings(text):
    return re.sub(r'<(/?)h([1-3])(?=[ >])',lambda m:'<'+m[1]+'h'+str(int(m[2])+2),text)
def render_reader(*,products,parts_html,catalog,comparison_html,module_directory,cards,**_):
    companies=list(dict.fromkeys(p['company'] for p in products));buckets=list(dict.fromkeys(p['bucket'] for p in products))
    company_body=catalog[catalog.index('<div class="filters">'):]
    company_ids={c['company']:c['id'] for c in json.loads((B/'全部公司产品清单.json').read_text())}
    labels={'中际旭创 / InnoLight':'中际旭创','光迅科技 / Accelink':'光迅科技','新易盛 / Eoptolink':'新易盛','Source Photonics':'索尔思(Source Photonics)'}
    for c in companies:
        cid=company_ids[labels.get(c,c)]
        action='<div class="company-actions"><button type="button" data-company-route="'+esc(c)+'">查看这家公司的详细模块路线 →</button></div>'
        company_body=re.sub(r'(<details[^>]*id="'+cid+r'"[^>]*><summary>.*?</summary>)',lambda m:m[1]+action,company_body,count=1)
    parts_body=parts_html[parts_html.index('<div class="layer-buttons">'):]
    narrative=(B/'reader_narrative.html').read_text()
    css=(B/'reader.css').read_text();js=(B/'reader.js').read_text()
    header='''<header class="masthead"><p class="eyebrow"><a href="../光模块知识体系/01-foundation.html">光模块入门</a> / 技术路线与公司产品</p><h1>光模块的技术路线与公司产品</h1><p class="deck">光模块都要完成电信号与光信号的转换，但相同速率的产品，可以采用不同的发光、光路和电处理方案。这些选择决定了模块需要哪些器件，以及器件怎样连接。</p></header>
<nav class="top-nav" aria-label="主要导航"><a href="#reader-product">01 产品怎样工作</a><a href="#reader-routes">02 路线怎样组合</a><a href="#reader-upstream">03 上游产品的作用</a><a href="#library">04 公司与产品</a><a href="#evidence">05 规格与比较条件</a></nav>'''
    library='''<section id="library" class="library-section"><p class="eyebrow">按需要查资料</p><h2>找到公司，再展开它的产品与已知实现</h2><p>先选查询方式，再输入公司、型号或产品词。目录保留集团、品牌、制造服务与历史身份；展开产品可查看规格、资料来源与适用阶段。</p><div class="library-tabs" role="tablist" aria-label="资料查询方式"><button role="tab" id="tab-catalog" aria-controls="catalog" aria-selected="true" data-pane="catalog">按公司查</button><button role="tab" id="tab-products" aria-controls="products" aria-selected="false" data-pane="products">查光模块型号</button><button role="tab" id="tab-components" aria-controls="components" aria-selected="false" data-pane="components">查材料、器件与设备</button></div>'''
    library+='<div id="catalog" class="library-pane" role="tabpanel" aria-labelledby="tab-catalog"><h3>公司提供了哪些产品？</h3><p class="pane-help">公司名称按产品归属区分；集团、子公司和历史品牌可能分别列出。</p>'+company_body+'<div class="pager" id="catalog-pager"></div></div>'
    library+='<div id="products" class="library-pane" role="tabpanel" aria-labelledby="tab-products" hidden><span id="overview"></span><h3>这款模块的各环节怎么做？</h3><p class="pane-help">速率相同不等于路线相同。产品型号、产品族、演示和历史计划分别标注；展开后查看来源与适用阶段。</p><div class="filters"><input id="query" aria-label="搜索产品" placeholder="搜索型号或路线，例如 EML、硅光、TRO"><select id="company" aria-label="公司"><option value="">全部公司</option>'+''.join('<option>'+esc(c)+'</option>' for c in companies)+'</select><select id="bucket" aria-label="资料对象"><option value="">全部资料类型</option>'+''.join('<option>'+esc(b)+'</option>' for b in buckets)+'</select></div><p id="visible" class="result-count" aria-live="polite"></p><div class="module-results">'+cards+'</div><div class="pager" id="products-pager"></div></div>'
    library+='<div id="components" class="library-pane" role="tabpanel" aria-labelledby="tab-components" hidden><h3>材料、芯片、器件和设备各提供什么？</h3><p class="pane-help">看产品的用途、所在环节和证据范围。工艺能力、制造服务与待核线索分别注明；跨层级的一组摘录会出现在多个筛选中。</p>'+parts_body+'<div class="pager" id="components-pager"></div></div></section>'
    appendix='''<section id="evidence" class="evidence-section"><p class="eyebrow">从技术结构到产品表现</p><h2>理解路线之后，还要对齐规格、条件与实际采用状态</h2><div class="gap-grid"><div><h3>确认是哪一款产品</h3><p>完整型号和版本决定具体配置。同一产品族可能包括不同光学平台、连接器和电处理版本；送样、认证和量产也有不同时间。</p></div><div><h3>比较相同条件下的表现</h3><p>功耗、误码率、成本、良率和可靠性要对应相同速率、距离、温度与主机条件，典型值与最大值不能直接相减。</p></div><div><h3>确认器件和工艺的采用关系</h3><p>设备能力与材料用途说明能做什么；具体产品使用哪台设备、哪种材料，还需要型号、工序和测试条件之间的直接对应。</p></div></div>
<details class="appendix"><summary>怎样理解规格、来源与未确认项</summary><div class="appendix-body"><p>产品型号规格、产品族公告和历史资料分别标注。原厂规格代表厂商披露，不能自动视为第三方实测；产品目录也不等于当前批量交付。</p><p>“暂无对应资料”表示实现尚不能确认；“来源未说明”表示所列文件没有给出该参数；“规格冲突”表示不同来源的描述不一致。三者都不能直接解释为产品没有这个功能。</p><p>型号卡片中的功能与结构明细覆盖信号路径、辅助电路和封装；这些检查项不是顺序生产工序。来源、资料日期与产品阶段可在卡片中查看。</p></div></details>'''
    appendix+='<details class="appendix" id="module-catalog"><summary>模块产品范围与公司归属</summary><div class="appendix-body">'+lower_headings(module_directory)+'</div></details>'
    files=[('非模块产品与环节.csv','材料、器件与设备'),('产品路线总表.csv','模块路线总表'),('全部公司产品清单.csv','公司产品目录'),('逐环节标注表.csv','功能与结构明细')]
    appendix+='<div id="files" class="downloads"><h3>产品资料表</h3><p>按公司、产品或功能筛选详细规格与来源。</p>'+''.join('<a href="'+n+'">'+label+' CSV ↗</a>' for n,label in files)+'</div></section>'
    page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>公司产品与技术路线 · 光模块研究</title><style>'+css+'</style></head><body>'+header+'<main>'+narrative+library+appendix+'</main><footer>光模块 · 技术路线与公司产品 · 2026年10月</footer><script>'+js+'</script></body></html>'

    return public_html(page)
