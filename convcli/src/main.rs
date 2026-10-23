//! 把 tenhou.net/6 格式的对局 JSONL 批量转换为 mjai 事件流
//! 用法: convcli <input.jsonl> <outdir> [start_index]
use convlog::tenhou::Log;
use convlog::tenhou_to_mjai;
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("usage: convcli <input.jsonl> <outdir>");
        std::process::exit(1);
    }
    let input = &args[1];
    let outdir = Path::new(&args[2]);
    fs::create_dir_all(outdir).expect("create outdir");

    let f = fs::File::open(input).expect("open input");
    let reader = BufReader::new(f);
    let (mut ok, mut bad) = (0usize, 0usize);

    for (i, line) in reader.lines().enumerate() {
        let line = match line {
            Ok(l) => l,
            Err(_) => continue,
        };
        if line.trim().is_empty() {
            continue;
        }
        match Log::from_json_str(&line) {
            Ok(log) => match tenhou_to_mjai(&log) {
                Ok(events) => {
                    let path = outdir.join(format!("{i:03}.mjai.jsonl"));
                    let mut out = fs::File::create(&path).expect("create out");
                    for e in events {
                        if let Ok(s) = serde_json::to_string(&e) {
                            writeln!(out, "{s}").ok();
                        }
                    }
                    ok += 1;
                }
                Err(e) => {
                    eprintln!("line {i}: convert error: {e}");
                    bad += 1;
                }
            },
            Err(e) => {
                eprintln!("line {i}: parse error: {e}");
                bad += 1;
            }
        }
    }
    println!("converted {ok}, failed {bad}");
}
