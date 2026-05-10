"""
Stock Screener – SMI Signal Strategy
Kryteria: USA + Europa | market cap > 200 mln | volume > 300 000
         | EPS TTM > 0 | Sales TTM > 0 | Quick Ratio > 1.0
Sygnał wejścia: SMI crossover / exit OS na interwale tygodniowym
(port Pine Script: "SMI Signal Strategy" – lengthK=10, lengthD=3, lengthEMA=3)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import json
import os
from datetime import datetime
from io import StringIO

MIN_MARKET_CAP = 200_000_000
MIN_VOLUME     = 300_000
MIN_QUICK      = 1.0
DELAY          = 0.25
OUTPUT_DIR     = "results"

# ══════════════════════════════════════════════════════════════
#  POBIERANIE TICKERÓW
# ══════════════════════════════════════════════════════════════

def get_sp500():
    try:
        url = ("https://www.ishares.com/us/products/239726/ISHARES-CORE-SP-500-ETF/"
               "1467271812596.ajax?fileType=csv&fileName=IVV_holdings&dataType=fund")
        r  = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        df = pd.read_csv(StringIO(r.text), skiprows=9)
        df = df[df["Asset Class"] == "Equity"]
        tickers = df["Ticker"].dropna().str.strip().str.replace(".", "-", regex=False).tolist()
        print(f"  S&P 500 (iShares IVV): {len(tickers)} spolok")
        return tickers
    except Exception as e:
        print(f"  S&P 500 blad: {e}")
        return []

def get_sp600():
    try:
        url = ("https://www.ishares.com/us/products/239774/ISHARES-CORE-SP-SMALLCAP-ETF/"
               "1467271812596.ajax?fileType=csv&fileName=IJR_holdings&dataType=fund")
        r  = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        df = pd.read_csv(StringIO(r.text), skiprows=9)
        df = df[df["Asset Class"] == "Equity"]
        tickers = df["Ticker"].dropna().str.strip().str.replace(".", "-", regex=False).tolist()
        print(f"  S&P 600 (iShares IJR): {len(tickers)} spolok")
        return tickers
    except Exception as e:
        print(f"  S&P 600 blad: {e}")
        return []

def get_russell2000():
    try:
        url = ("https://www.ishares.com/us/products/239710/ISHARES-RUSSELL-2000-ETF/"
               "1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund")
        r  = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        df = pd.read_csv(StringIO(r.text), skiprows=9)
        df = df[df["Asset Class"] == "Equity"]
        tickers = df["Ticker"].dropna().str.strip().tolist()
        print(f"  Russell 2000: {len(tickers)} spółek")
        return tickers
    except Exception as e:
        print(f"  Russell 2000 błąd: {e}")
        return []

def get_european_indices():
    dax = [
        "ADS.DE","AIR.DE","ALV.DE","BAS.DE","BAYN.DE","BEI.DE","BMW.DE","BNR.DE",
        "CON.DE","1COV.DE","DHER.DE","DB1.DE","DBK.DE","DHL.DE","DTE.DE","EOAN.DE",
        "FRE.DE","FME.DE","HEI.DE","HEN3.DE","IFX.DE","LIN.DE","MBG.DE","MRK.DE",
        "MTX.DE","MUV2.DE","PAH3.DE","POWR.DE","QGEN.DE","RHM.DE","RWE.DE","SAP.DE",
        "SHL.DE","SIE.DE","SY1.DE","VNA.DE","VOW3.DE","ZAL.DE","PUM.DE","ENR.DE",
    ]
    cac = [
        "AC.PA","ACA.PA","AI.PA","AIR.PA","ALO.PA","MT.PA","ATO.PA","CS.PA","BNP.PA",
        "EN.PA","CAP.PA","CA.PA","AXA.PA","DSY.PA","EDEN.PA","EL.PA","ERF.PA","EDF.PA",
        "ENGI.PA","FP.PA","KER.PA","LR.PA","LHN.PA","MC.PA","ML.PA","ORA.PA","RI.PA",
        "PUB.PA","RNO.PA","SAF.PA","SGO.PA","SAN.PA","SU.PA","GLE.PA","STLAM.PA",
        "STM.PA","TEP.PA","HO.PA","URW.PA","VIE.PA","DG.PA","VIV.PA","WLN.PA",
    ]
    ftse = [
        "AAF.L","AAL.L","ABF.L","ADM.L","AHT.L","ANTO.L","AZN.L","AUTO.L","AV.L",
        "BAB.L","BA.L","BARC.L","BATS.L","BHKLY.L","BP.L","BDEV.L","BKG.L","BLND.L",
        "BT-A.L","CCH.L","CNA.L","CPG.L","CRDA.L","DCC.L","DGE.L","EXPN.L","FERG.L",
        "FLTR.L","FRES.L","GSK.L","GLEN.L","HLMA.L","HL.L","HSBA.L","IMB.L","INF.L",
        "IHG.L","III.L","ITRK.L","JD.L","JMAT.L","KGF.L","LAND.L","LGEN.L","LLOY.L",
        "LMP.L","MKS.L","MNDI.L","MNG.L","MRO.L","NG.L","NXT.L","OCDO.L","PHNX.L",
        "PRU.L","PSH.L","PSN.L","PSON.L","REL.L","RIO.L","RKT.L","RMV.L","RR.L",
        "RS1.L","SBRY.L","SDR.L","SGE.L","SHEL.L","SKG.L","SKY.L","SLA.L","SMDS.L",
        "SMIN.L","SMT.L","SN.L","SPX.L","SSE.L","STAN.L","SVT.L","TSCO.L","TW.L",
        "ULVR.L","UTG.L","UU.L","VOD.L","WEIR.L","WPP.L","WTB.L",
    ]
    aex = [
        "ABN.AS","ADYEN.AS","AGN.AS","AH.AS","AKZA.AS","MT.AS","ASML.AS","ASR.AS",
        "BESI.AS","DSMF.AS","EXOR.AS","HEIA.AS","IMCD.AS","INGA.AS","JUST.AS",
        "KPN.AS","NN.AS","PHIA.AS","PRX.AS","RAND.AS","REN.AS","SHELL.AS","SBM.AS",
        "URW.AS","UNA.AS","VPK.AS","WKL.AS",
    ]
    ibex = [
        "ACS.MC","ACX.MC","AMS.MC","ANA.MC","BBVA.MC","BKT.MC","CABK.MC","CLNX.MC",
        "COL.MC","ELE.MC","ENG.MC","FDR.MC","FER.MC","GRF.MC","IAG.MC","IBE.MC",
        "IDR.MC","ITX.MC","LOG.MC","MAP.MC","MEL.MC","MRL.MC","MTS.MC","NTGY.MC",
        "RED.MC","REE.MC","REP.MC","ROVI.MC","SAB.MC","SAN.MC","SGRE.MC","SOL.MC",
        "TEF.MC","UNI.MC","VIS.MC",
    ]
    smi = [
        "ABBN.SW","ADEN.SW","ALC.SW","CSGN.SW","GEBN.SW","GIVN.SW","CFR.SW",
        "HOLN.SW","LONN.SW","NESN.SW","NOVN.SW","ROG.SW","SANN.SW","SCMN.SW",
        "SGSN.SW","SLHN.SW","SRENH.SW","UBSG.SW","ZURN.SW",
    ]
    mib = [
        "A2A.MI","AMP.MI","ATL.MI","AZM.MI","BMED.MI","BMPS.MI","BZU.MI","CPR.MI",
        "DIA.MI","ENEL.MI","ENI.MI","EXOR.MI","FCA.MI","FBK.MI","G.MI","HER.MI",
        "ISP.MI","IVG.MI","LDO.MI","MB.MI","MONC.MI","PIRC.MI","PRY.MI","PST.MI",
        "REC.MI","SRG.MI","STM.MI","TEN.MI","TIT.MI","TRN.MI","UCG.MI","UNI.MI",
    ]
    omx = [
        "ABB.ST","ALFA.ST","ASSA-B.ST","AZN.ST","ATCO-A.ST","BOL.ST","ERIC-B.ST",
        "ESSITY-B.ST","EVO.ST","GETI-B.ST","HEXA-B.ST","HM-B.ST","HUFV-A.ST",
        "INVE-B.ST","KINV-B.ST","NDA-SE.ST","SAND.ST","SCA-B.ST","SEB-A.ST",
        "SECU-B.ST","SKA-B.ST","SKF-B.ST","SSAB-A.ST","SHB-A.ST","SWED-A.ST",
        "SWMA.ST","TEL2-B.ST","TELIA.ST","VOLV-B.ST","VOLCAR-B.ST",
    ]
    obx = [
        "AKERBP.OL","AKSO.OL","AKER.OL","AMSC.OL","AUTO.OL","BAKKA.OL","DNB.OL",
        "EQNR.OL","FRO.OL","GOGL.OL","MOWI.OL","NEL.OL","NHY.OL","NSKOG.OL",
        "ORK.OL","PGS.OL","REC.OL","SALM.OL","SCHA.OL","SDRL.OL","SNOG.OL",
        "STB.OL","SUBC.OL","TEL.OL","TOM.OL","TGS.OL","VAR.OL","WILS.OL","YAR.OL",
    ]
    bel = [
        "ABI.BR","ACKB.BR","AGS.BR","APAM.BR","ARGX.BR","COLR.BR","D5MT.BR",
        "EKTA-B.BR","GBL.BR","GLPG.BR","KBC.BR","MELE.BR","ONTEX.BR","PROX.BR",
        "SOLB.BR","TNET.BR","UCB.BR","UMI.BR","WDP.BR",
    ]
    wig = [
        "ALE.WA","CCC.WA","CDR.WA","CPS.WA","DNP.WA","JSW.WA","KGH.WA","KRU.WA",
        "LPP.WA","MBK.WA","OPL.WA","PCO.WA","PEO.WA","PGE.WA","PKN.WA","PKO.WA",
        "PZU.WA","SPL.WA","TPE.WA","XTB.WA",
    ]
    all_tickers = list(set(dax + cac + ftse + aex + ibex + smi + mib + omx + obx + bel + wig))
    print(f"  EU statyczna lista: {len(all_tickers)} tickerow")
    print(f"    DAX:{len(dax)} CAC:{len(cac)} FTSE:{len(ftse)} AEX:{len(aex)} IBEX:{len(ibex)}")
    print(f"    SMI:{len(smi)} MIB:{len(mib)} OMX:{len(omx)} OBX:{len(obx)} BEL:{len(bel)} WIG:{len(wig)}")
    return all_tickers


# ══════════════════════════════════════════════════════════════
#  SMI INDICATOR
# ══════════════════════════════════════════════════════════════

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()

def ema_ema(series: pd.Series, length: int) -> pd.Series:
    return ema(ema(series, length), length)

def calc_smi(high, low, close, length_k=10, length_d=3, length_ema=3):
    highest_high         = high.rolling(length_k).max()
    lowest_low           = low.rolling(length_k).min()
    highest_lowest_range = highest_high - lowest_low
    relative_range       = close - (highest_high + lowest_low) / 2
    denom = ema_ema(highest_lowest_range, length_d).replace(0, np.nan)
    smi     = 200 * (ema_ema(relative_range, length_d) / denom)
    smi_ema = ema(smi, length_ema)
    return smi, smi_ema

def smi_signals(smi, smi_ema, use_cross=True, use_zone=True, use_zero=False, strong_only=False):
    if len(smi) < 3:
        return False, False, None, None, "—"
    s0, s1 = float(smi.iloc[-1]), float(smi.iloc[-2])
    e0, e1 = float(smi_ema.iloc[-1]), float(smi_ema.iloc[-2])
    cross_up = (s1 < e1) and (s0 >= e0)
    exit_os  = (s1 < -40) and (s0 >= -40)
    zero_up  = (s1 < 0)   and (s0 >= 0)
    raw_buy    = (use_cross and cross_up) or (use_zone and exit_os) or (use_zero and zero_up)
    strong_buy = raw_buy and (s1 <= -40 or s0 <= -40)
    buy_signal = strong_only and strong_buy or (not strong_only and raw_buy)
    if s0 >= 40:    zone = "OVERBOUGHT"
    elif s0 <= -40: zone = "OVERSOLD"
    elif s0 > 0:    zone = "Bullish"
    else:           zone = "Bearish"
    return buy_signal, strong_buy, round(s0, 2), round(e0, 2), zone


# ══════════════════════════════════════════════════════════════
#  ANALIZA FUNDAMENTALNA
# ══════════════════════════════════════════════════════════════

def check_fundamentals(info: dict):
    eps       = info.get("trailingEps")
    sales_ttm = info.get("totalRevenue")
    quick     = info.get("quickRatio")

    eps_ok   = eps       is not None and eps       > 0
    sales_ok = sales_ttm is not None and sales_ttm > 0
    quick_ok = quick is None or quick > MIN_QUICK   # brak danych = przepuszczamy

    passed = eps_ok and sales_ok and quick_ok

    metrics = {
        "eps_ttm":       round(eps,  2)             if eps       is not None else None,
        "sales_ttm_mln": round(sales_ttm / 1e6, 1) if sales_ttm is not None else None,
        "quick_ratio":   round(quick, 2)            if quick     is not None else None,
    }
    return passed, metrics


# ══════════════════════════════════════════════════════════════
#  GŁÓWNA PĘTLA SCREENER
# ══════════════════════════════════════════════════════════════

def run_screener():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start = datetime.now()
    print("=" * 60)
    print(f"SCREENER START: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Wskaźnik: SMI(10,3,3) | cross_up + exit_OS | weekly")
    print(f"Filtry:   cap>{MIN_MARKET_CAP/1e6:.0f}M | vol>{MIN_VOLUME:,} | EPS>0 | Sales>0 | QR>{MIN_QUICK}")
    print("=" * 60)

    print("\n[1/5] Pobieranie list spółek...")
    usa_tickers = list(set(get_sp500() + get_sp600() + get_russell2000()))
    eu_tickers  = list(set(get_european_indices()))
    all_tickers = [(t, "USA") for t in usa_tickers] + [(t, "EU") for t in eu_tickers]
    print(f"\nŁącznie: {len(all_tickers)} spółek ({len(usa_tickers)} USA, {len(eu_tickers)} EU)")

    print("\n[2/5] Analiza spółek...")
    results, signals, strong = [], [], []
    skipped = errors = 0

    for i, (symbol, market) in enumerate(all_tickers):
        try:
            tkr = yf.Ticker(symbol)
            fi  = tkr.fast_info

            price = getattr(fi, "last_price", None)
            if not price or price <= 0:
                skipped += 1; continue

            market_cap = getattr(fi, "market_cap", None)
            if not market_cap or market_cap < MIN_MARKET_CAP:
                skipped += 1; continue

            volume = getattr(fi, "three_month_average_volume", None) \
                     or getattr(fi, "last_volume", None)
            if not volume or volume < MIN_VOLUME:
                skipped += 1; continue

            currency = getattr(fi, "currency", "USD")

            try:
                info = tkr.info
            except Exception:
                skipped += 1; continue

            fund_ok, metrics = check_fundamentals(info)
            if not fund_ok:
                skipped += 1; continue

            hist = tkr.history(period="2y", interval="1wk").dropna(subset=["High", "Low", "Close"])
            if len(hist) < 20:
                skipped += 1; continue

            smi_ser, smi_ema_ser = calc_smi(hist["High"], hist["Low"], hist["Close"])
            buy_sig, strong_sig, smi_val, smi_ema_val, zone = smi_signals(smi_ser, smi_ema_ser)

            if smi_val is None:
                skipped += 1; continue

            name    = info.get("shortName", symbol)
            sector  = info.get("sector", "—")
            country = info.get("country", "—")

            smi_above_ema  = smi_val > smi_ema_val if smi_ema_val else False
            market_cap_mln = round(market_cap / 1e6, 1)
            volume_k       = round(volume / 1000, 1)

            row = {
                "ticker": symbol, "name": name, "market": market,
                "country": country, "sector": sector,
                "price": round(price, 2), "currency": currency,
                "market_cap_mln": market_cap_mln, "volume_k": volume_k,
                "smi": smi_val, "smi_ema": smi_ema_val,
                "smi_above_ema": smi_above_ema, "zone": zone,
                "signal": buy_sig, "strong_signal": strong_sig,
                **metrics,
                "scanned_at": datetime.now().isoformat(),
            }
            results.append(row)

            sig_tag = "STRONG" if strong_sig else ("SYGNAŁ" if buy_sig else "ok    ")
            qr_str  = f"QR={metrics['quick_ratio']}" if metrics['quick_ratio'] else "QR=n/a"
            print(f"  {sig_tag} [{i+1}] {symbol:10s} {market} | {price:8.2f} {currency} "
                  f"| cap={market_cap_mln:.0f}M | SMI={smi_val:6.1f} EMA={smi_ema_val:6.1f} "
                  f"| {zone:12s} | EPS={metrics['eps_ttm']} {qr_str}")

            if buy_sig:    signals.append(row)
            if strong_sig: strong.append(row)

            time.sleep(DELAY)

        except KeyboardInterrupt:
            print("\nPrzerwano."); break
        except Exception:
            errors += 1

    elapsed = round((datetime.now() - start).total_seconds() / 60, 1)
    print(f"\n[3/5] Gotowe w {elapsed} min | Kandydaci:{len(results)} Sygnały:{len(signals)} Strong:{len(strong)} Pominięto:{skipped} Błędy:{errors}")

    print("\n[4/5] Zapis wyników...")
    meta = {
        "generated_at": datetime.now().isoformat(), "elapsed_min": elapsed,
        "total_scanned": len(all_tickers), "candidates": len(results),
        "signals": len(signals), "strong": len(strong),
        "skipped": skipped, "errors": errors, "indicator": "SMI(10,3,3)",
        "min_cap_mln": MIN_MARKET_CAP / 1e6, "min_volume": MIN_VOLUME, "min_quick": MIN_QUICK,
    }
    for fname, data in [("meta", meta), ("results", results), ("signals", signals), ("strong", strong)]:
        with open(f"{OUTPUT_DIR}/{fname}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    if results: pd.DataFrame(results).to_csv(f"{OUTPUT_DIR}/results.csv", index=False)
    if signals: pd.DataFrame(signals).to_csv(f"{OUTPUT_DIR}/signals.csv", index=False)

    print("[5/5] Generowanie raportu HTML...")
    generate_html(meta, results, signals, strong)
    print(f"\nGotowe! Wyniki w: {OUTPUT_DIR}/")
    print(f"\n💡 Aby przeanalizować wyniki: wklej plik results/signals.json do Claude.")
    return signals


# ══════════════════════════════════════════════════════════════
#  RAPORT HTML
# ══════════════════════════════════════════════════════════════

def generate_html(meta, results, signals, strong):
    dt = datetime.fromisoformat(meta["generated_at"]).strftime("%d.%m.%Y %H:%M")

    def zone_badge(zone):
        cls = {"OVERBOUGHT":"zone-ob","OVERSOLD":"zone-os","Bullish":"zone-bull","Bearish":"zone-bear"}.get(zone,"")
        return f'<span class="zone-badge {cls}">{zone}</span>'

    def fmt_cap(mln):
        if mln is None: return "—"
        return f"{mln/1000:.1f} B" if mln >= 1000 else f"{mln:.0f} M"

    def fmt_vol(k):
        if k is None: return "—"
        return f"{k/1000:.1f}M" if k >= 1000 else f"{k:.0f}K"

    def na(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "—"

    def rows_html(data):
        if not data:
            return "<tr><td colspan='13' style='text-align:center;color:#888;padding:2rem'>Brak wyników</td></tr>"
        html = ""
        for r in data:
            sb = '<span class="badge-strong">STRONG</span>' if r.get("strong_signal") else (
                 '<span class="badge-signal">BUY</span>'    if r.get("signal")        else "")
            sc = "smi-above" if r["smi_above_ema"] else "smi-below"
            html += f"""<tr>
              <td><span class="ticker">{r['ticker']}</span>{sb}</td>
              <td class="name-col">{r['name']}</td>
              <td><span class="badge-{'usa' if r['market']=='USA' else 'eu'}">{r['market']}</span></td>
              <td>{r['sector']}</td>
              <td class="num">{r['price']} {r['currency']}</td>
              <td class="num cap-col">{fmt_cap(r.get('market_cap_mln'))}</td>
              <td class="num">{fmt_vol(r.get('volume_k'))}</td>
              <td class="num {sc}">{r['smi']}</td>
              <td class="num">{r['smi_ema']}</td>
              <td>{zone_badge(r['zone'])}</td>
              <td class="num">{na(r.get('eps_ttm'))}</td>
              <td class="num">{na(r.get('sales_ttm_mln'))} M</td>
              <td class="num">{na(r.get('quick_ratio'))}</td>
            </tr>"""
        return html

    def signal_cards(data):
        if not data:
            return "<div class='empty'>Brak sygnałów w tym skanie</div>"
        cards = ""
        for r in sorted(data, key=lambda x: -x.get("strong_signal", 0)):
            mc  = "usa" if r["market"] == "USA" else "eu"
            tc  = "linear-gradient(90deg,#ff6b00,#ffb800)" if r.get("strong_signal") else "linear-gradient(90deg,#00c8ff,#00e599)"
            sl  = "STRONG BUY" if r.get("strong_signal") else "BUY SIGNAL"
            sc2 = "#ffb800" if r.get("strong_signal") else "#00c8ff"
            z   = r.get("zone","—")
            zc  = {"OVERBOUGHT":"#ff4560","OVERSOLD":"#00e599","Bullish":"#4da6ff","Bearish":"#ffa040"}.get(z,"#888")
            cards += (
                f'<div class="signal-card">'
                f'<div style="position:absolute;top:0;left:0;right:0;height:2px;background:{tc}"></div>'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                f'<div><div class="sc-ticker">{r["ticker"]}</div><div class="sc-name">{r["name"]}</div></div>'
                f'<span class="badge-{mc}">{r["market"]}</span></div>'
                f'<div class="sc-price">{r["price"]} {r["currency"]}</div>'
                f'<div class="sc-row"><span>Sygnał</span><span style="color:{sc2};font-weight:500">{sl}</span></div>'
                f'<div class="sc-row"><span>Strefa SMI</span><span style="color:{zc}">{z}</span></div>'
                f'<div class="sc-row"><span>Sektor</span><span>{r["sector"]}</span></div>'
                f'<div class="sc-row"><span>Market Cap</span><span style="color:var(--accent)">{fmt_cap(r.get("market_cap_mln"))}</span></div>'
                f'<div class="sc-row"><span>Wolumen avg</span><span>{fmt_vol(r.get("volume_k"))}</span></div>'
                f'<div class="sc-divider"></div>'
                f'<div class="sc-row"><span>EPS TTM</span><span style="color:var(--green)">{na(r.get("eps_ttm"))}</span></div>'
                f'<div class="sc-row"><span>Sales TTM</span><span style="color:var(--green)">{na(r.get("sales_ttm_mln"))} M</span></div>'
                f'<div class="sc-row"><span>Quick Ratio</span><span style="color:var(--green)">{na(r.get("quick_ratio"))}</span></div>'
                f'<div class="sc-stoch">'
                f'<div class="sc-stoch-item"><div class="sc-stoch-label">SMI</div>'
                f'<div class="sc-stoch-val {"green" if r["smi_above_ema"] else "red"}">{r["smi"]}</div></div>'
                f'<div class="sc-stoch-item"><div class="sc-stoch-label">SMI EMA</div>'
                f'<div class="sc-stoch-val">{r["smi_ema"]}</div></div>'
                f'</div></div>'
            )
        return f'<div class="signal-grid">{cards}</div>'

    all_rows    = rows_html(sorted(results, key=lambda x: (-x.get("strong_signal",0), x["smi"])))
    signal_rows = rows_html(sorted(signals, key=lambda x: -x.get("strong_signal",0)))
    cards_html  = signal_cards(signals)

    sc   = meta["signals"];  str_ = meta["strong"]
    cc   = meta["candidates"]; tc = meta["total_scanned"]; el = meta["elapsed_min"]
    cap  = int(meta.get("min_cap_mln", 200)); vol = int(meta.get("min_volume", 300000))
    qr   = meta.get("min_quick", 1.0)

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stock Screener SMI – {dt}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#0a0e14;--bg2:#111620;--border:#1e2d45;--text:#c8d8f0;--muted:#4a6080;
         --accent:#00c8ff;--green:#00e599;--amber:#ffb800;--red:#ff4560;--usa:#3b82f6;--eu:#10b981}}
  body{{background:var(--bg);color:var(--text);font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.6}}
  .header{{border-bottom:1px solid var(--border);padding:2rem 2.5rem 1.5rem;display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem}}
  .header-left h1{{font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:500;color:#fff;letter-spacing:-.5px}}
  .header-left h1 span{{color:var(--accent)}}
  .header-left p{{font-size:12px;color:var(--muted);margin-top:4px;font-family:'IBM Plex Mono',monospace}}
  .criteria-pills{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}
  .pill{{font-family:'IBM Plex Mono',monospace;font-size:11px;padding:3px 10px;border:1px solid var(--border);border-radius:100px;color:var(--muted)}}
  .pill.active{{border-color:var(--accent);color:var(--accent)}}
  .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1px;background:var(--border);border-bottom:1px solid var(--border)}}
  .stat{{background:var(--bg);padding:1.25rem 1.5rem}}
  .stat-label{{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}
  .stat-value{{font-size:28px;font-weight:300;color:#fff;margin-top:4px;font-family:'IBM Plex Mono',monospace}}
  .stat-value.highlight{{color:var(--accent)}}.stat-value.green{{color:var(--green)}}.stat-value.amber{{color:var(--amber)}}
  .stat-sub{{font-size:11px;color:var(--muted);margin-top:2px}}
  .tabs{{display:flex;border-bottom:1px solid var(--border);padding:0 2rem}}
  .tab{{font-family:'IBM Plex Mono',monospace;font-size:12px;padding:12px 20px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;margin-bottom:-1px;background:none;border-top:none;border-left:none;border-right:none;transition:all .15s}}
  .tab:hover{{color:var(--text)}}.tab.active{{color:var(--accent);border-bottom-color:var(--accent)}}
  .content{{padding:1.5rem 2rem}}.panel{{display:none}}.panel.active{{display:block}}
  .toolbar{{display:flex;gap:10px;margin-bottom:1rem;flex-wrap:wrap;align-items:center}}
  .search-input{{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:7px 12px;color:var(--text);font-family:'IBM Plex Mono',monospace;font-size:12px;width:240px;outline:none}}
  .search-input:focus{{border-color:var(--accent)}}
  .filter-select{{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:7px 12px;color:var(--text);font-family:'IBM Plex Mono',monospace;font-size:12px;outline:none;cursor:pointer}}
  .count-label{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--muted);margin-left:auto}}
  .table-wrap{{overflow-x:auto}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  thead th{{font-family:'IBM Plex Mono',monospace;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap}}
  tbody tr{{border-bottom:1px solid var(--border);transition:background .1s}}
  tbody tr:hover{{background:var(--bg2)}}
  td{{padding:10px 12px;vertical-align:middle}}
  .ticker{{font-family:'IBM Plex Mono',monospace;font-weight:500;color:#fff;font-size:13px}}
  .name-col{{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-size:12px}}
  .cap-col{{color:var(--muted);font-size:12px}}
  .num{{font-family:'IBM Plex Mono',monospace;font-size:12px;text-align:right}}
  .smi-above{{color:var(--green)}}.smi-below{{color:var(--red)}}
  .badge-usa{{display:inline-block;font-size:10px;font-family:'IBM Plex Mono',monospace;padding:2px 7px;border-radius:4px;background:rgba(59,130,246,.15);color:var(--usa);border:1px solid rgba(59,130,246,.3)}}
  .badge-eu{{display:inline-block;font-size:10px;font-family:'IBM Plex Mono',monospace;padding:2px 7px;border-radius:4px;background:rgba(16,185,129,.15);color:var(--eu);border:1px solid rgba(16,185,129,.3)}}
  .badge-signal{{display:inline-block;font-size:9px;font-family:'IBM Plex Mono',monospace;padding:1px 6px;border-radius:4px;background:rgba(0,200,255,.15);color:var(--accent);border:1px solid rgba(0,200,255,.3);margin-left:6px;vertical-align:middle;animation:pulse 2s infinite}}
  .badge-strong{{display:inline-block;font-size:9px;font-family:'IBM Plex Mono',monospace;padding:1px 6px;border-radius:4px;background:rgba(255,184,0,.15);color:var(--amber);border:1px solid rgba(255,184,0,.4);margin-left:6px;vertical-align:middle;animation:pulse 1.5s infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
  .zone-badge{{display:inline-block;font-size:10px;font-family:'IBM Plex Mono',monospace;padding:2px 8px;border-radius:4px;white-space:nowrap}}
  .zone-ob{{background:rgba(255,69,96,.12);color:#ff4560;border:1px solid rgba(255,69,96,.3)}}
  .zone-os{{background:rgba(0,229,153,.12);color:#00e599;border:1px solid rgba(0,229,153,.3)}}
  .zone-bull{{background:rgba(77,166,255,.12);color:#4da6ff;border:1px solid rgba(77,166,255,.3)}}
  .zone-bear{{background:rgba(255,160,64,.12);color:#ffa040;border:1px solid rgba(255,160,64,.3)}}
  .signal-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px;margin-bottom:1.5rem}}
  .signal-card{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:1rem 1.25rem;position:relative;overflow:hidden}}
  .sc-ticker{{font-family:'IBM Plex Mono',monospace;font-size:18px;font-weight:500;color:#fff}}
  .sc-name{{font-size:12px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .sc-price{{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:300;color:var(--accent);margin:10px 0 8px}}
  .sc-row{{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:4px}}
  .sc-row span:last-child{{font-family:'IBM Plex Mono',monospace;color:var(--text)}}
  .sc-divider{{border-top:1px solid var(--border);margin:8px 0}}
  .sc-stoch{{display:flex;gap:12px;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}}
  .sc-stoch-item{{flex:1}}
  .sc-stoch-label{{font-size:10px;font-family:'IBM Plex Mono',monospace;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}}
  .sc-stoch-val{{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:500;margin-top:2px}}
  .sc-stoch-val.green{{color:var(--green)}}.sc-stoch-val.red{{color:var(--red)}}
  .empty{{text-align:center;padding:4rem 2rem;color:var(--muted);font-family:'IBM Plex Mono',monospace;font-size:13px}}
  .empty::before{{content:'//';display:block;font-size:32px;margin-bottom:1rem;color:var(--border)}}
  .hint-box{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:1.5rem 2rem;font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--muted);line-height:1.8}}
  .hint-box strong{{color:var(--accent)}}
  .hint-box code{{background:rgba(0,200,255,.08);color:var(--accent);padding:2px 7px;border-radius:4px;font-size:12px}}
  footer{{border-top:1px solid var(--border);padding:1rem 2rem;font-size:11px;color:var(--muted);font-family:'IBM Plex Mono',monospace;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
</style>
</head>
<body>
<div class="header">
  <div class="header-left">
    <h1>STOCK <span>SCREENER</span> // SMI</h1>
    <p>// generated {dt} &nbsp;|&nbsp; elapsed {el} min &nbsp;|&nbsp; SMI(10,3,3) weekly</p>
    <div class="criteria-pills">
      <span class="pill active">USA + Europa</span>
      <span class="pill active">cap &gt; {cap} mln</span>
      <span class="pill active">vol &gt; {vol:,}</span>
      <span class="pill active">EPS TTM &gt; 0</span>
      <span class="pill active">Sales TTM &gt; 0</span>
      <span class="pill active">Quick Ratio &gt; {qr}</span>
      <span class="pill active">SMI cross / exit OS (1W)</span>
    </div>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-label">Przeskanowano</div><div class="stat-value">{tc}</div><div class="stat-sub">USA + EU</div></div>
  <div class="stat"><div class="stat-label">Kandydaci</div><div class="stat-value highlight">{cc}</div><div class="stat-sub">fundamenty OK</div></div>
  <div class="stat"><div class="stat-label">Sygnały BUY</div><div class="stat-value green">{sc}</div><div class="stat-sub">cross / exit OS</div></div>
  <div class="stat"><div class="stat-label">Strong BUY</div><div class="stat-value amber">{str_}</div><div class="stat-sub">z głębi strefy OS</div></div>
  <div class="stat"><div class="stat-label">Min. Cap</div><div class="stat-value">{cap}</div><div class="stat-sub">mln USD/EUR</div></div>
  <div class="stat"><div class="stat-label">Czas skanu</div><div class="stat-value">{el}</div><div class="stat-sub">minut</div></div>
</div>
<div class="tabs">
  <button class="tab active" onclick="switchTab('signals',this)">Sygnały BUY ({sc})</button>
  <button class="tab" onclick="switchTab('all',this)">Wszyscy kandydaci ({cc})</button>
  <button class="tab" onclick="switchTab('hint',this)">✦ Jak analizować</button>
</div>
<div class="content">

  <div id="panel-signals" class="panel active">
    {cards_html}
    <div class="table-wrap">
      <table><thead><tr>
        <th>Ticker</th><th>Nazwa</th><th>Rynek</th><th>Sektor</th>
        <th style="text-align:right">Cena</th><th style="text-align:right">Cap</th>
        <th style="text-align:right">Wolumen</th><th style="text-align:right">SMI</th>
        <th style="text-align:right">EMA</th><th>Strefa</th>
        <th style="text-align:right">EPS TTM</th><th style="text-align:right">Sales TTM</th>
        <th style="text-align:right">Quick R.</th>
      </tr></thead><tbody>{signal_rows}</tbody></table>
    </div>
  </div>

  <div id="panel-all" class="panel">
    <div class="toolbar">
      <input class="search-input" type="text" placeholder="szukaj tickera lub nazwy..." oninput="filterTable(this.value)"/>
      <select class="filter-select" onchange="filterMarket(this.value)">
        <option value="">Wszystkie rynki</option><option value="USA">USA</option><option value="EU">EU</option>
      </select>
      <select class="filter-select" onchange="filterZone(this.value)">
        <option value="">Wszystkie strefy</option><option value="OVERSOLD">OVERSOLD</option>
        <option value="Bearish">Bearish</option><option value="Bullish">Bullish</option>
        <option value="OVERBOUGHT">OVERBOUGHT</option>
      </select>
      <span class="count-label" id="row-count">{cc} wyników</span>
    </div>
    <div class="table-wrap">
      <table id="tbl-all"><thead><tr>
        <th>Ticker</th><th>Nazwa</th><th>Rynek</th><th>Sektor</th>
        <th style="text-align:right">Cena</th><th style="text-align:right">Cap</th>
        <th style="text-align:right">Wolumen</th><th style="text-align:right">SMI</th>
        <th style="text-align:right">EMA</th><th>Strefa</th>
        <th style="text-align:right">EPS TTM</th><th style="text-align:right">Sales TTM</th>
        <th style="text-align:right">Quick R.</th>
      </tr></thead><tbody id="tbody-all">{all_rows}</tbody></table>
    </div>
  </div>

  <div id="panel-hint" class="panel">
    <div class="hint-box">
      <strong>// Jak uzyskać analizę AI dla tych wyników</strong><br><br>
      1. Otwórz plik <code>results/signals.json</code> z katalogu skanu<br>
      2. Wklej jego zawartość do Claude na <code>claude.ai</code><br>
      3. Napisz: <em>"Przeanalizuj te sygnały screener i zrób ranking Top 5"</em><br><br>
      Alternatywnie możesz wkleić plik <code>results/results.csv</code> jeśli chcesz analizę wszystkich kandydatów.<br><br>
      <strong>// Pliki wynikowe</strong><br><br>
      <code>results/signals.json</code> — spółki z sygnałem BUY<br>
      <code>results/strong.json</code> — tylko Strong BUY (z głębi OVERSOLD)<br>
      <code>results/results.json</code> — wszyscy kandydaci (fundamenty OK)<br>
      <code>results/results.csv</code> — to samo w formacie CSV
    </div>
  </div>

</div>
<footer>
  <span>// stock-screener &nbsp;|&nbsp; SMI(10,3,3) &nbsp;|&nbsp; dane: Yahoo Finance</span>
  <span>Nie stanowi porady inwestycyjnej</span>
</footer>
<script>
function switchTab(name, btn) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
}}
let mf = '', zf = '';
function filterMarket(v) {{ mf = v; applyFilters(); }}
function filterZone(v)   {{ zf = v; applyFilters(); }}
function filterTable(v)  {{ applyFilters(v); }}
function applyFilters(search) {{
  const rows = document.querySelectorAll('#tbody-all tr');
  let visible = 0;
  const s = (search ?? document.querySelector('.search-input').value).toLowerCase();
  rows.forEach(row => {{
    const t = row.textContent.toLowerCase();
    const ok = (!mf || t.includes(mf.toLowerCase()))
            && (!zf || t.includes(zf.toLowerCase()))
            && (!s  || t.includes(s));
    row.style.display = ok ? '' : 'none';
    if (ok) visible++;
  }});
  document.getElementById('row-count').textContent = visible + ' wyników';
}}
</script>
</body>
</html>"""

    path = f"{OUTPUT_DIR}/index.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Raport: {path}")


if __name__ == "__main__":
    run_screener()
