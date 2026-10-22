"""İşçi sayısı kıyası: aynı 24 model-eğitimi görevini 8 / 12 / 16 işçiyle koşturur, duvar sürelerini yazar.
Kullanım (cvdrev ortamında, paket klasöründe):  python bench_workers.py [--workers 8 12 16]
Çıktı: out\isci_kiyasi.json  — en kısa süreyi veren değer config.yaml → compute.n_jobs için önerilir."""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np
from joblib import Parallel, delayed


def _task(i, n=6000, d=32):
    from sklearn.ensemble import RandomForestClassifier
    from lightgbm import LGBMClassifier
    rs = np.random.default_rng(i); X = rs.normal(size=(n, d)); y = (X[:, 0] + 0.5 * X[:, 1] + rs.normal(size=n) > 0).astype(int)
    t0 = time.time()
    RandomForestClassifier(n_estimators=200, n_jobs=1, random_state=i).fit(X, y)
    LGBMClassifier(n_estimators=300, num_leaves=31, n_jobs=1, verbose=-1, random_state=i).fit(X, y)
    return time.time() - t0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, nargs="+", default=[8, 12, 16]); ap.add_argument("--tasks", type=int, default=24)
    a = ap.parse_args()
    cpu = os.cpu_count(); res = {"mantiksal_cekirdek": cpu, "gorev": a.tasks, "sonuc": {}}
    for w in a.workers:
        if w > cpu:
            res["sonuc"][str(w)] = {"atlandi": f"{w} > cekirdek {cpu}"}; continue
        t0 = time.time()
        try:
            if w == 1:
                per = [_task(i) for i in range(a.tasks)]
            else:
                per = Parallel(n_jobs=w, backend="loky")(delayed(_task)(i) for i in range(a.tasks))
        except (PermissionError, OSError) as e:
            res["sonuc"][str(w)] = {"hata": repr(e)}; print(w, "hata", e); continue
        wall = time.time() - t0
        res["sonuc"][str(w)] = {"duvar_s": round(wall, 1), "gorev_basina_ort_s": round(float(np.mean(per)), 2), "verim_gorev_dk": round(a.tasks / wall * 60, 1)}
        print(f"{w} isci: {wall:.1f} s duvar, gorev basina {np.mean(per):.2f} s")
    ok = {k: v["duvar_s"] for k, v in res["sonuc"].items() if "duvar_s" in v}
    if ok:
        res["oneri_n_jobs"] = int(min(ok, key=ok.get))
    os.makedirs("out", exist_ok=True)
    json.dump(res, open(os.path.join("out", "isci_kiyasi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
