# -*- coding: utf-8 -*-
"""宇树科技投资人一图通 · 水墨中国风。数字与正式版逐字一致，仅更换视觉系统。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image as PImage

fm.fontManager.addfont('/System/Library/Fonts/Supplemental/Songti.ttc')
plt.rcParams['font.sans-serif']=['Songti SC','Times New Roman','Arial Unicode MS']
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['pdf.fonttype']=42

# 水墨色系
PAPER='#F6F1E6'; INK='#262321'; INK2='#4A4642'; MOH='#8C867D'
HAIR='#C9C0B0'; GRID='#E9E2D3'; CARD='#FBF7ED'
ZHU='#A23B2E'   # 朱砂
QING='#3E5C6B'; QING2='#7E98A2'; QING3='#C3CFD3'
WHITE='#FFFFFF'

FW,FH=100.0,140.0
fig=plt.figure(figsize=(14,19.6),dpi=200)
fig.patch.set_facecolor(PAPER)
ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,FW); ax.set_ylim(0,FH); ax.axis('off')

# 宣纸水墨底纹
paper=plt.imread('ppt_assets/ink_paper.png')
ax.imshow(paper,extent=[0,100,0,140],aspect='auto',zorder=0,alpha=0.85)

def T(x,y,s,size=10,color=INK,bold=False,ha='left',va='center',style='normal',ls=1.25,alpha=1.0,z=5,rot=0):
    ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,linespacing=ls,rotation=rot,alpha=alpha,
            fontweight='bold' if bold else 'normal',fontstyle=style,zorder=z,
            family='Songti SC')

def rect(x,y,w,h,fc=None,ec=None,lw=0.8,z=1,alpha=1.0):
    ax.add_patch(Rectangle((x,y),w,h,facecolor=fc if fc else 'none',
                 edgecolor=ec if ec else 'none',linewidth=lw,zorder=z,alpha=alpha))

def hairline(x1,y1,x2,y2,c=HAIR,lw=0.8,z=2):
    ax.plot([x1,x2],[y1,y2],color=c,lw=lw,zorder=z,solid_capstyle='butt')

def panel(x,y,w,h,title,sub=None):
    rect(x,y,w,h,fc=CARD,ec=HAIR,lw=0.9,z=1,alpha=0.72)
    # 朱砂小方印式标题标记
    rect(x+1.6,y+h-2.9,0.5,1.55,fc=ZHU,z=3)
    T(x+2.5,y+h-2.1,title,size=12.6,bold=True,color=INK)
    if sub: T(x+w-1.6,y+h-2.1,sub,size=8.2,color=MOH,ha='right')

def chart_axes(fx,fy,fw,fh):
    a=fig.add_axes([fx/FW,fy/FH,fw/FW,fh/FH])
    for sp in ('top','right'): a.spines[sp].set_visible(False)
    for sp in ('left','bottom'): a.spines[sp].set_color(HAIR); a.spines[sp].set_linewidth(0.8)
    a.tick_params(length=0,labelsize=8,colors=INK2)
    a.set_axisbelow(True)
    a.grid(axis='y',color=GRID,lw=0.7)
    for lab in a.get_xticklabels()+a.get_yticklabels(): lab.set_family('Songti SC')
    return a

# ---- 水墨机器人：白底转透明 ----
rob=PImage.open('ppt_assets/ink_robot.png').convert('RGBA')
ra=np.array(rob).astype(float)
dark=(255-ra[...,:3].mean(axis=2))
al=np.clip((dark-6)*3.2,0,255).astype('uint8')
rgb=(ra[...,:3]*0.28+np.array([38,35,33])*0.72).astype('uint8')
out=np.dstack([rgb,al]); PImage.fromarray(out).save('ppt_assets/ink_robot_t.png')

# ============ 页眉 ============
# 内容区与页脚区压淡底纹，保证文字清晰；页眉保留远山意境
rect(0,13.0,100,116.0,fc=PAPER,alpha=0.60,z=0.4)
rect(0,2.0,100,10.8,fc=PAPER,alpha=0.74,z=0.4)
hairline(2.2,128.9,97.8,128.9,INK,1.1)
hairline(2.2,128.45,97.8,128.45,HAIR,0.7)
rect(3,135.7,0.55,0.55,fc=ZHU,z=3)
T(3.9,135.97,'科创板通用机器人龙头  ·  688836.SH',size=9.6,color=MOH)
T(3,133.3,'宇树科技  经营与财务全景一图通',size=24,bold=True,color=INK)
T(3,130.7,'高增长换挡期：人形切换、扣非盈利与费用扩张的赛跑',size=11.5,color=INK2)
T(3,127.5,'资料截止 2026-08-30  ｜  金额单位：万元（图表换算为亿元）  ｜  A=已实现    E=预测（严格分列）',size=8.6,color=MOH)
# 印章
rect(69.4,130.6,3.5,3.5,fc=ZHU,z=4)
for i,ch in enumerate('宇树科技'):
    T(70.27+(i%2)*1.75,133.05-(i//2)*1.75,ch,size=12.5,bold=True,color=PAPER,ha='center',z=5)
# 水墨机器人
ax.imshow(plt.imread('ppt_assets/ink_robot_t.png'),extent=[77.5,98.2,126.8,141.3],aspect='auto',zorder=3,alpha=0.92)
# 左侧竖排装饰
for i,ch in enumerate('数据为凭・研以致用'):
    T(0.95,112-i*2.05,ch,size=8.5,color=MOH,ha='center',rot=0)

# ============ KPI 带 ============
kpis=[
 ('16.99 亿元','2025 营业收入','两年 CAGR 约 226.8%\n2024/2025 同比 +146.8%/+332.6%'),
 ('5.91 亿元','2025 扣非归母净利润','扣非净利率 34.8%\n归母 2.78 亿，受股份支付扰动'),
 ('60.13%','2025 主营毛利率','44.22%→56.74%→60.13%\n全栈自研支撑、逐年抬升'),
 ('11.52 亿元','2026H1 营收（+48.54%）','扣非 2.44 亿、同比 -19.34%\n收入增、利润端承压（未审计）'),
 ('59.17 亿元','IPO 募资净额','发行市值 609.93 亿\n2026-08-19 上市，发行价 150.80 元'),
]
y0,y1=115.2,128.6
hairline(2.2,y1,97.8,y1,INK,1.0); hairline(2.2,y0,97.8,y0,HAIR,0.9)
cw=95.6/5
for i,(num,lab,sub) in enumerate(kpis):
    x=2.2+i*cw
    if i: hairline(x,y0+0.6,x,y1-0.6,HAIR,0.7)
    T(x+1.4,125.0,num,size=18.5,bold=True,color=INK)
    T(x+1.4,121.6,lab,size=9.6,bold=True,color=INK2)
    for j,ln in enumerate(sub.split('\n')):
        c = ZHU if (i==3 and j==1) else MOH
        T(x+1.4,119.0-j*2.0,ln,size=8.0,color=c)

# ============ 增长 ============
panel(2.2,84.0,46.6,29.0,'增长轨迹：营收三年十倍级，增速逐期换挡')
a=chart_axes(4.0,92.3,43.0,16.4)
yrs=['2023A','2024A','2025A']; rev=[1.59,3.93,16.99]
bars=a.bar(yrs,rev,width=0.52,color=[QING3,QING2,QING],zorder=3)
for b,v in zip(bars,rev):
    a.text(b.get_x()+b.get_width()/2,v+0.4,f'{v:.2f}',ha='center',fontsize=9,fontweight='bold',color=INK)
a.set_ylim(0,19.5); a.set_yticks([0,5,10,15])
T(4.0,90.5,'同比：—   /  +146.82%  /  +332.64%（2023 为基期）',size=8.4,color=MOH)
hairline(4.0,89.2,47.0,89.2,HAIR,0.7)
T(4.0,87.4,'换挡信号：2026Q1 同比 +68.49%、2026H1 +48.54%，高斜率阶段过去、进入中高速区间',size=8.6,color=INK2)
T(4.0,85.4,'2026H1 营收 11.52 亿元，略超业绩预告上限（11.28 亿，E）；未经审计',size=8.6,color=INK2)

# ============ 产品 ============
panel(51.2,84.0,46.6,29.0,'产品切换：人形两年间成为第一大产品')
a=chart_axes(53.0,92.0,20.0,14.6)
human=np.array([1.88,27.60,51.78]); quad=np.array([75.78,59.53,41.62]); oth=100-human-quad
x=np.arange(3)
a.bar(x,human,width=0.5,color=QING,label='人形',zorder=3)
a.bar(x,quad,bottom=human,width=0.5,color=QING2,label='四足',zorder=3)
a.bar(x,oth,bottom=human+quad,width=0.5,color=QING3,label='组件及其他',zorder=3)
for i in range(3):
    a.text(i,human[i]/2,f'{human[i]:.1f}%',ha='center',va='center',fontsize=7.6,color=WHITE,fontweight='bold')
    a.text(i,human[i]+quad[i]/2,f'{quad[i]:.1f}%',ha='center',va='center',fontsize=7.2,color=WHITE)
    a.text(i,human[i]+quad[i]+oth[i]/2,f'{oth[i]:.1f}%',ha='center',va='center',fontsize=6.8,color=INK)
a.set_xticks(x); a.set_xticklabels(yrs); a.set_ylim(0,100); a.set_yticks([0,50,100])
for lx,lc,lt in [(53.0,QING,'人形'),(58.4,QING2,'四足'),(64.6,QING3,'组件及其他')]:
    rect(lx,107.55,0.95,0.95,fc=lc); T(lx+1.35,108.02,lt,8.0,color=INK2)
T(75.2,107.0,'人形主营收入（亿元）',size=8.6,bold=True,color=QING)
T(75.2,104.5,'0.03 → 1.07 → 8.68',size=11,bold=True,color=INK)
T(75.2,102.1,'占主营 1.88%→27.60%→51.78%',size=8.4,color=MOH)
hairline(75.2,100.7,96.0,100.7,HAIR,0.7)
T(75.2,99.0,'人形销量 5→412→5,215 台',size=8.8,bold=True,color=INK2)
T(75.2,97.0,'平均单价 59.34→26.04→16.64 万元/台',size=8.4,color=INK2)
T(75.2,95.0,'四足销量 3,121→23,037 台、单价降至 3.03 万',size=8.4,color=INK2)
T(75.2,93.0,'2025 纯人形出货超 5,500 台（公司称全球第一）',size=8.4,color=INK2)
T(75.2,90.9,'以价换量、扩大装机与开发者生态',size=8.4,color=MOH,style='italic')
T(53.0,89.4,'结论：完成“四足→人形”结构切换，人形决定下一阶段弹性；组件及其他 2025 占约 6.6%（精确拆分待核）',size=8.4,color=INK2)
T(53.0,87.4,'图：主营收入分产品占比（%，100% 堆叠）',size=7.8,color=MOH)

# ============ 盈利 ============
panel(2.2,53.0,46.6,29.0,'盈利质量：扣非强劲，归母受股份支付扰动')
a=chart_axes(4.0,60.4,27.0,17.6)
ni=[-0.11,0.95,2.78]; nd=[-0.18,0.78,5.91]; x=np.arange(3); w=0.36
a.bar(x-w/2,ni,w,color=QING3,label='归母净利润',zorder=3)
a.bar(x+w/2,nd,w,color=QING,label='扣非归母',zorder=3)
for xi,v in zip(x-w/2,ni): a.text(xi,v-0.22,f'{v:.2f}',ha='center',va='top',fontsize=7.4,color=QING2)
for xi,v in zip(x+w/2,nd): a.text(xi,v+0.2,f'{v:.2f}',ha='center',va='bottom',fontsize=7.4,color=INK,fontweight='bold')
a.set_xticks(x); a.set_xticklabels(yrs); a.set_ylim(-1.6,7.4); a.axhline(0,color=HAIR,lw=0.8)
a2=a.twinx()
gm=[44.22,56.74,60.13]
a2.plot(x,gm,color=ZHU,lw=2.0,marker='o',ms=4,zorder=4)
for xi,g in zip(x,gm): a2.text(xi-0.12,g+1.4,f'{g:.1f}%',ha='right',fontsize=7.6,color=ZHU,fontweight='bold')
a2.set_ylim(25,82); a2.set_yticks([])
for sp in ('top','right','left'): a2.spines[sp].set_visible(False)
a.legend(loc='upper center',bbox_to_anchor=(0.5,0.99),ncol=2,frameon=False,fontsize=7.6,handlelength=1.0,columnspacing=1.2)
T(4.0,58.6,'线：主营毛利率 44.22%→56.74%→60.13%（右轴，朱砂线）',size=8.0,color=ZHU)
T(4.0,56.5,'2025 非经常性净损失 -3.13 亿元（主要为股份支付），归母低于扣非；',size=8.4,color=INK2)
T(4.0,54.6,'扣非加权 ROE 28.70%、基本 EPS 0.76 元——评估盈利应以扣非为主。',size=8.4,color=INK2)

# ============ 市场研发财务 ============
panel(51.2,53.0,46.6,29.0,'市场、研发与财务韧性')
blocks=[
 ('市场结构 · 境内反超',['境内主营占比 44.4%→44.3%→56.4%，2025 年反超；','境外 7.32 亿元、占 43.65%，仍是重要市场（关注汇率）。']),
 ('研发投入 · 绝对额升、费率降',['研发费用 0.50→0.70→1.45 亿元，费率 31.39%→8.53%（规模摊薄非收缩）；','研发人员 184 人、占 35.66%（2025 末员工 516 人）；','原拟募投约 42.02 亿，模型/本体/新产品约 35.77 亿、约 85% 投向研发。']),
 ('现金流与杠杆 · 稳健',['2025 经营现金流 6.70 亿元、CFO/营收 39.43%；资产负债率 18.82%。','2026H1 末总资产 38.45 亿（较年初 +19.85%）、负债率 25.11%；','CFO 2.32 亿元、同比 -32.53%。']),
]
yy=77.8
for i,(h,lines) in enumerate(blocks):
    rect(53.0,yy-0.2,0.42,0.42,fc=ZHU,z=3)
    T(53.9,yy,h,size=9.8,bold=True,color=INK)
    for j,ln in enumerate(lines):
        T(53.9,yy-2.0-j*1.85,ln,size=8.5,color=INK2)
    if i<2: hairline(53.0,yy-7.4,96.0,yy-7.4,HAIR,0.7)
    yy-=8.9

# ============ 投资要点 ============
panel(2.2,23.5,46.6,27.5,'投资要点：技术垂直整合 × 出货规模 × 财务弹性')
bull=[
 ('全栈自研','电机/控制器/感知算法/整机/具身模型垂直整合，支撑 60.13% 毛利率与降价空间'),
 ('出货领先','2025 人形确认收入 5,215 台、公司称纯人形出货超 5,500 台全球第一；四足三年超 3.3 万台'),
 ('产销顺畅','2025 年前三季度人形产销率超 95%，基本满产满销'),
 ('价格带下探','人形单价降至 16.64 万元、G1 进入 10 万元级，扩大装机与开发者生态'),
 ('资金弹药','低杠杆、经营现金流为正；IPO 募资净额 59.17 亿元支撑研发与制造投入'),
]
yy=46.4
for h,b in bull:
    rect(4.0,yy-0.5,0.45,0.45,fc=QING,z=3)
    T(5.0,yy,h,size=9.6,bold=True,color=INK)
    T(14.2,yy,b,size=8.5,color=INK2)
    yy-=4.55

# ============ 风险 ============
panel(51.2,23.5,46.6,27.5,'主要风险：场景集中、价格下行与费用扩张最需盯紧')
risks=[
 ('商业化场景集中','人形 2025 1-9M 约 73.6% 收入来自科研教育，行业应用仅约 9.01%'),
 ('价格下行/竞争','两类产品单价逐年走低，价格战或进一步压缩单价与毛利'),
 ('股份支付扰动','2025 非经常性净损失 -3.13 亿，后续激励或继续扰动归母'),
 ('费用扩张','2026H1 扣非 -19.34%、CFO -32.53%，费用刚性下利润率承压'),
 ('高估值波动','发行市值 609.93 亿、媒体口径 PE 219.23 倍（待核），对兑现高度敏感'),
 ('外包/供应链/外销','劳务外包升至 6,802.65 万；境外占 43.65%，汇率与供应链风险并存'),
]
yy=46.4
for h,b in risks:
    ax.scatter([53.22],[yy-0.28],s=42,marker='D',color=ZHU,zorder=4)
    T(54.0,yy,h,size=9.4,bold=True,color=ZHU)
    T(68.6,yy,b,size=8.3,color=INK2)
    yy-=3.78

# ============ 增长变量 ============
rect(2.2,13.5,95.6,8.0,fc=CARD,ec=HAIR,lw=1.0,alpha=0.85)
rect(3.8,19.0,0.5,1.4,fc=ZHU,z=3)
T(4.7,19.7,'增长变量：事实（A）与计划（E）分列',size=10.5,bold=True,color=INK)
T(4.7,17.4,'已兑现 A：人形放量至主营 51.78%  ·  境内反超至 56.35%  ·  IPO 募资净额 59.17 亿到位  ·  2025 扣非净利率 34.8%',size=8.7,color=INK2)
T(4.7,15.2,'待验证 E：行业场景渗透提速（当前人形行业应用仅约 9.01%）  ·  募投研发转化  ·  制造基地达产规划人形 7.5 万+四足 11.5 万台/年（规划，非已实现）  ·  海外扩张',size=8.7,color=INK2)

# ============ 页脚 ============
hairline(2.2,12.0,97.8,12.0,HAIR,0.8)
T(2.2,10.4,'资料来源：S1 招股说明书（注册稿，上交所 auditId=2178）；S2 上市保荐书（注册稿）；S3 审核落实函回复；S4 招股意向书；S5 上市公告书；S6 发行/投资风险公告；S7 浦银国际、S8 兴业证券、S9 国信证券研报转引；S10 东方财富/证券时报数据中心（交叉核对）；S11 公司官网。',size=7.3,color=MOH,ls=1.4)
T(2.2,7.6,'口径说明：金额除注明外为万元（图表换算亿元）；2023–2025 为经审计年度数（注册稿口径），2026Q1 经审阅、2026H1 为上市公告书披露且未经审计；E 为 2026-05 上会稿业绩预告，预测不作为已实现事实；占比/同比/CAGR 由原始数据现算，“约/待核”为原始披露未直接给出或需以原文复核项。',size=7.3,color=MOH,ls=1.4)
T(2.2,4.6,'本图仅用于内部投资研究汇报，不构成任何投资建议；二级市场行情截至 2026-08-30，其后数据不纳入。',size=7.6,color=ZHU,bold=True)
T(97.8,4.6,'宇树科技 688836.SH  ·  内部汇报 · 单页全景（水墨版）',size=7.6,color=MOH,ha='right')

OUT='/Users/guoqingtao/Desktop/AI办公评测/豆包办公/宇树科技投资人一图通_水墨风_截至20260830.png'
fig.savefig(OUT,dpi=200,facecolor=PAPER)
fig.savefig('/Users/guoqingtao/Desktop/AI办公评测/豆包办公/宇树科技投资人一图通_水墨风_截至20260830.pdf',facecolor=PAPER)
print('SAVED',OUT)
