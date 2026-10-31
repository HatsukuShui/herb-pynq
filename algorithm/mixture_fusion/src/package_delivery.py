"""Package portable sources, evidence and data, without local runtime or native binaries."""
from pathlib import Path
import hashlib,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    files=[]
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or '__pycache__' in relative.parts or relative.as_posix().startswith('build/native/'):
            continue
        if relative.as_posix()=='checksums.json':continue
        if path.suffix.lower() in ['.dll','.exe','.pyc']:continue
        if any(not re.fullmatch(r'[a-z0-9_.-]+',part) for part in relative.parts):raise ValueError('Nonportable path: '+str(relative))
        files.append(path)
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest=ROOT/'checksums.json';manifest.write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    target=ROOT.parent/'shuishengxi_algorithm_delivery.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for path in files+[manifest]:z.write(path,'shuishengxi_algorithm/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(json.dumps(dict(path=str(target),files=len(files)+1,bytes=target.stat().st_size),ensure_ascii=False))

if __name__=='__main__':main()
