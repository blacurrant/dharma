"""Writes VF_MANIFEST.json + SHA256SUMS.txt (pure python). Re-run after any change; the manifest lists itself last-run hashes of everything else."""
import json, hashlib, os, glob, ast, datetime
VF = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff'
os.chdir(VF)
src = ast.parse(open('scripts/vf_nodes.py').read())
SPEC = next(ast.literal_eval(n.value) for n in src.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'SPEC')
gen = {t['file']: t for t in json.load(open('evidence/10_generation.json'))['textures']}
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()
pats = ('textures/*.png', 'contact/*.png', 'renders/*.png', 'VF_*.md', 'VF_PROP_PLACEMENTS.json', 'scripts/*.py', 'evidence/*.json', 'evidence/*.txt', 'evidence/*.log', 'TempleEnvironmentKit_vf_working.blend')
files = []
for p in pats:
    files += sorted(glob.glob(p))
items = []
for f in files:
    d = dict(path=f, sha256=sha(f), bytes=os.path.getsize(f))
    if f in gen:
        t = gen[f]; nm = os.path.basename(f)[:-4]
        sp = SPEC.get(nm)
        d.update({k: t[k] for k in ('role', 'color_space', 'tiling', 'tile_size_m', 'projection', 'blend', 'width', 'height', 'channels') if k in t})
        if sp:
            d['recommended'] = dict(kind=sp[0], mapping=sp[1], tile_m=sp[2], opacity_default=sp[3], opacity_range=list(sp[4]), weight_inside_combat_circle_r10=sp[5])
    items.append(d)
man = dict(generated=datetime.datetime.now().astimezone().isoformat(timespec='seconds'), generator='scripts/15_manifest.py', milestone='VISUAL FOUNDATION iteration 1',
           notes=['Unity world (x,z) = Blender (x,y); macro maps U=(x+20)/40, V=(z+20)/40, file row 0 = z +20',
                  'verify_b/ and bake_out_b/ (floor-part verification intermediates) are intentionally not hashed here',
                  'all hashes are SHA-256 of the file bytes'], file_count=len(items), files=items)
json.dump(man, open('VF_MANIFEST.json', 'w'), indent=1)
open('SHA256SUMS.txt', 'w').write(''.join(f"{i['sha256']}  {i['path']}\n" for i in items))
print('MANIFEST', len(items), 'files;', sum(1 for i in items if i['path'].startswith('textures/')), 'textures;', sum(i['bytes'] for i in items) / 1e6, 'MB hashed')
