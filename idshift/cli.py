import argparse
def main(argv=None):
    p=argparse.ArgumentParser(prog="idshift")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("site")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--wave", type=int, default=1)
    h=sub.add_parser("harvest")
    h.add_argument("--base", required=True)
    h.add_argument("--wave-name", required=True)
    h.add_argument("--out", required=True)
    h.add_argument("--checkpoint", required=True)
    v=sub.add_parser("verify")
    v.add_argument("--out", required=True)
    v.add_argument("--expect", required=True)
    args=p.parse_args(argv)
    if args.cmd=="site":
        from idshift.site import serve
        serve(args.host, args.port, args.wave); return 0
    if args.cmd=="harvest":
        from idshift.harvest import run_harvest
        return run_harvest(args)
    if args.cmd=="verify":
        from idshift.verify import run_verify
        return run_verify(args)
    return 2
if __name__=="__main__":
    raise SystemExit(main())
