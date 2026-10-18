#!/usr/bin/env python3
"""Assemble verified SquashFS/static-bootstrap RAM initramfs; no hardware access."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='build/k93/rootfs-gui-v1')
    parser.add_argument('--image',default='build/k93/alpine-gui-v2.squashfs')
    parser.add_argument('--network-root',action='store_true',help='Receive the pinned image over USB instead of embedding it')
    parser.add_argument('--desktop-test',action='store_true',help='Include manual bounded framebuffer test; never auto-start it')
    args=parser.parse_args()
    assert not args.desktop_test or args.network_root,'Desktop diagnostic requires split root'
    output=(ROOT/args.output).resolve()
    assert output.is_relative_to(ROOT/'build/k93') and not output.exists()
    image=(ROOT/args.image).resolve()
    assert image.is_relative_to(ROOT/'build/k93') and image.suffix=='.squashfs'
    proof=image.with_name(image.stem+'-squashfs.json')
    receipt=json.loads(proof.read_text())
    assert receipt['board']=='K93AP' and receipt['full_readback_matches'] and receipt['source_unchanged']
    assert sha(image)==receipt['image_sha256']
    apk=ROOT/'build/k93/busybox-static-1.37.0-r30.apk'
    assert sha(apk)=='fb023d6a1e2dce9069b11b302e674c273b9e17d04d17b03ee16526475b0971e6'
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(apk.read_bytes())),ignore_zeros=True) as archive:
        binary=archive.extractfile('bin/busybox.static').read()
    assert binary[:7]==b'\x7fELF\x01\x01\x01' and binary[18:20]==b'\x28\x00'
    for directory in ['bin','dev','proc','sys','run','tmp','newroot']:
        (output/directory).mkdir(parents=True,exist_ok=True)
    (output/'bin/busybox').write_bytes(binary);(output/'bin/busybox').chmod(0o755)
    (output/'bin/sh').symlink_to('busybox')
    for source,destination in [('squash-init','init'),('alpine-init','k93-stage2')]:
        shutil.copyfile(ROOT/'rootfs/k93'/source,output/destination)
        (output/destination).chmod(0o755)
    if args.desktop_test:
        for source,destination in [('desktop-test.sh','k93-desktop-test.sh'),('xorg-fbdev.conf','k93-xorg.conf'),('twm-test.conf','k93-twm.conf')]:
            shutil.copyfile(ROOT/'rootfs/k93'/source,output/destination)
            (output/destination).chmod(0o755 if destination.endswith('.sh') else 0o644)
        helper=ROOT/'build/k93/fb-read-v1/k93-fb-read'
        assert sha(helper)=='6bee646f88aa62a5dfdedae00afc48de33e9585afd464b7f38432bada398f2c1'
        shutil.copyfile(helper,output/'k93-fb-read');(output/'k93-fb-read').chmod(0o755)
    if args.network_root:
        (output/'root-transfer-network').write_text('K93 USB-only RAM image receiver\n')
        image_path='/run/root.squashfs'
    else:
        shutil.copyfile(image,output/'root.squashfs')
        assert sha(output/'root.squashfs')==receipt['image_sha256']
        image_path='/root.squashfs'
    (output/'root.squashfs.sha256').write_text(receipt['image_sha256']+'  '+image_path+'\n')
    result={'board':'K93AP','ram_only':True,'upper_limit_mib':64,'tmp_limit_mib':32,
            'image_receipt_sha256':sha(proof),'hardware_tested':False,'network_root':args.network_root,'desktop_test':args.desktop_test,
            'root_image':{'path':image.relative_to(ROOT).as_posix(),'sha256':receipt['image_sha256'],'size':image.stat().st_size},
            'files':{p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file() and not p.is_symlink()}}
    with (output.parent/(output.name+'-manifest.json')).open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
