#!/usr/bin/env python3
"""Test actual Alpine archive filter without Docker, network or hardware."""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile

source=Path(__file__).with_name('k93-prepare-alpine.py')
spec=importlib.util.spec_from_file_location('alpine',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def archive(entries):
    data=io.BytesIO()
    with tarfile.open(fileobj=data,mode='w') as stream:
        for name,link in entries:
            item=tarfile.TarInfo(name)
            if link is None:
                item.size=4;stream.addfile(item,io.BytesIO(b'test'))
            else:
                item.type=tarfile.SYMTYPE;item.linkname=link;stream.addfile(item)
    data.seek(0)
    return tarfile.open(fileobj=data)

with tempfile.TemporaryDirectory(prefix='k93-alpine-filter-') as directory:
    root=Path(directory)/'root';root.mkdir()
    with archive([('bin/busybox',None),('usr/bin/yes','/bin/busybox')]) as stream:
        stream.extractall(root,filter=module.rootfs_filter)
    assert (root/'usr/bin/yes').read_bytes()==b'test'
    assert (root/'usr/bin/yes').resolve()==root/'bin/busybox'
    for entry in [('../outside',None),('bad','../../outside'),('bad','/../../outside')]:
        try:
            with archive([entry]) as stream:
                stream.extractall(root,filter=module.rootfs_filter)
        except tarfile.FilterError:
            pass
        else:
            raise AssertionError('Archive escape accepted: '+repr(entry))
    assert not (Path(directory)/'outside').exists()
print('PASS: actual rootfs filter rebases absolute applet links and rejects escapes; no hardware')
