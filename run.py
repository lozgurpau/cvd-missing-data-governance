"""Tek giriş noktası.  python run.py [--config config.yaml] [--scale deneme|tam] [--stage kontrol|veri|ana|duyarlilik|rapor|all]"""
import argparse, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _pin_threads_early():
    """OpenMP/BLAS iş parçacığı sayısını, OpenMP yüklenmeden ÖNCE (hiçbir sklearn/xgboost içe aktarılmadan) sabitle.
    Aksi hâlde HistGradientBoosting/XGBoost/LightGBM model başına tüm çekirdekleri kullanır (n_jobs işçileriyle çarpışır)."""
    try:
        import yaml
        cfg_path = "config.yaml"
        if "--config" in sys.argv:
            cfg_path = sys.argv[sys.argv.index("--config") + 1]
        with open(cfg_path, encoding="utf-8") as f:
            thr = int(yaml.safe_load(f).get("compute", {}).get("threads_per_model", 1))
    except Exception:  # noqa
        thr = 1
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[v] = str(thr)  # config.yaml yetkilidir; ortamdan gelen değer ezilir


_pin_threads_early()
from cvdrev.config import load_config
from cvdrev.util import get_logger, write_json

STAGES = ["kontrol", "veri", "ana", "duyarlilik", "rapor"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--scale", default=None, help="mini | deneme | tam (config.yaml'ı geçersiz kılar; mini yalnız boru hattı testi)")
    ap.add_argument("--stage", default="all")
    ap.add_argument("--n-jobs", type=int, default=None)
    a = ap.parse_args()
    cfg = load_config(a.config, scale=a.scale, n_jobs=a.n_jobs)
    log = get_logger(cfg.out_dir)
    log.info("cvdrev baslatildi | scale=%s | n_jobs=%d | out=%s", cfg.scale, cfg.n_jobs, cfg.out_dir)
    stages = STAGES if a.stage == "all" else [s for s in a.stage.split(",")]
    for s in stages:
        if s not in STAGES:
            raise SystemExit(f"bilinmeyen asama: {s}; secenekler: {STAGES}")
    status = {}
    # önceki koşudan kalan hata kaydı bu koşunun sonuç zip'ine girmesin diye durum dosyası koşu başında sıfırlanır.
    write_json(os.path.join(cfg.out_dir, "run_status.json"), {"durum": "kosuyor", "asamalar": stages})
    t_all = time.time()
    for s in stages:
        t0 = time.time()
        log.info("=== ASAMA %s basliyor ===", s)
        try:
            if s == "kontrol":
                from cvdrev.checks import run_checks; run_checks(cfg, log)
            elif s == "veri":
                from cvdrev.data import build_analytic; from cvdrev.cohort import run_cohort; from cvdrev.cohort_v2 import run_cohort_v2
                build_analytic(cfg, log); run_cohort(cfg, log); run_cohort_v2(cfg, log)
            elif s == "ana":
                from cvdrev.main_analysis import run_main; run_main(cfg, log)
            elif s == "duyarlilik":
                from cvdrev.sensitivity import run_sensitivity; run_sensitivity(cfg, log)
            elif s == "rapor":
                from cvdrev.report import run_report; run_report(cfg, log)
            status[s] = {"ok": True, "sec": round(time.time() - t0, 1)}
            log.info("=== ASAMA %s bitti (%.0f s) ===", s, time.time() - t0)
        except Exception as e:  # noqa
            status[s] = {"ok": False, "sec": round(time.time() - t0, 1), "error": repr(e)}
            log.error("ASAMA %s HATA: %s\n%s", s, repr(e), traceback.format_exc())
            write_json(os.path.join(cfg.out_dir, "run_status.json"), status)
            raise
    status["toplam_sec"] = round(time.time() - t_all, 1)
    write_json(os.path.join(cfg.out_dir, "run_status.json"), status)
    log.info("tamamlandi: %s", status)


if __name__ == "__main__":
    main()
